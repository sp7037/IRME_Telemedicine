from django.test import TransactionTestCase
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User, DoctorProfile, PatientProfile, TMCProfile
from consultations.models import (
    Consultation,
    AdminPlatformAccount,
    AdminPlatformEntry,
    ConsultationFeeSetting,
    Payment,
    ConsultationFinance,
    PatientWallet,
    PatientWalletEntry,
    TMCAccount,
    TMCAccountEntry,
    DoctorEarning,
    DoctorSchedule,
)
from consultations.finance import admin_platform_topup, patient_wallet_topup, tmc_account_topup


class ConsultationBookingTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()

        # Create doctor user & profile
        self.doctor_user = User.objects.create_user(
            email="doctor@test.com",
            password="testpass123",
            is_doctor=True,
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            max_daily_consultations=1,
            profile_completed=True,
            admin_verified=True,
            is_approved=True,
            consultation_fee="100.00",
        )

        # Secondary doctor for fallback logic
        self.alt_doctor_user = User.objects.create_user(
            email="doctor2@test.com",
            password="testpass123",
            is_doctor=True,
        )
        self.alt_doctor_profile = DoctorProfile.objects.create(
            user=self.alt_doctor_user,
            specialty=self.doctor_profile.specialty,
            profile_completed=True,
            admin_verified=True,
            is_approved=True,
            consultation_fee="100.00",
        )

        # Create patient user & profile
        self.patient_user = User.objects.create_user(
            email="patient@test.com",
            password="testpass123",
            is_patient=True,
        )
        self.patient_profile = PatientProfile.objects.create(user=self.patient_user)

        # Create TMC user & profile
        self.tmc_user = User.objects.create_user(
            email="tmc@test.com",
            password="testpass123",
            is_tmc_operator=True,
        )
        self.tmc_profile = TMCProfile.objects.create(
            user=self.tmc_user,
            free_consultation_quota=1,
            free_consultations_used=0,
        )
        patient_wallet_topup(self.patient_profile, "5000.00", "Test patient balance")
        tmc_account_topup(self.tmc_profile, "5000.00", "Test TMC balance")
        admin_platform_topup("5000.00", "Test admin platform balance")

    def authenticate_patient(self):
        self.client.force_authenticate(user=self.patient_user)

    def authenticate_tmc(self):
        self.patient_profile.created_by_tmc = self.tmc_profile
        self.patient_profile.save(update_fields=["created_by_tmc"])
        self.client.force_authenticate(user=self.tmc_user)

    def authenticate_new_patient(self, email="patient2@test.com"):
        user = User.objects.create_user(email=email, password="testpass123", is_patient=True)
        profile = PatientProfile.objects.create(user=user)
        patient_wallet_topup(profile, "5000.00", "Test patient balance")
        self.client.force_authenticate(user=user)
        return user, profile

    def test_direct_consultation_booking_creates_payment_when_amount_provided(self):
        """A legacy amount field does not replace the configured doctor's fee."""
        self.doctor_profile.consultation_fee = "250.00"
        self.doctor_profile.save(update_fields=["consultation_fee"])
        self.authenticate_patient()

        url = reverse("book-consultation")
        payload = {
            "doctor_id": self.doctor_profile.id,
            "consultation_type": "DIRECT",
            "amount": "250.00",
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        consultation_id = response.data["consultation_id"]
        consultation = Consultation.objects.get(id=consultation_id)
        payment = Payment.objects.get(consultation=consultation)
        finance = ConsultationFinance.objects.get(consultation=consultation)
        wallet = PatientWallet.objects.get(patient=self.patient_profile)
        self.assertFalse(consultation.is_free)
        self.assertEqual(str(payment.amount), "250.00")
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertFalse(payment.paid_by_tmc)
        self.assertEqual(finance.billing_type, ConsultationFinance.BillingType.PAID)
        self.assertEqual(finance.payer_entity, ConsultationFinance.PayerEntity.PATIENT)
        self.assertTrue(PatientWalletEntry.objects.filter(wallet=wallet, consultation=consultation).exists())

    def test_tmc_booking_uses_free_quota_first(self):
        """First TMC booking should consume free quota and not create Payment."""
        self.authenticate_tmc()

        url = reverse("tmc-book-consultation")
        payload = {
            "doctor_id": self.doctor_profile.id,
            "consultation_type": "TMC",
            "tmc_id": self.tmc_profile.id,
            "patient_id": self.patient_profile.id,
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        consultation = Consultation.objects.get(id=response.data["consultation_id"])

        self.tmc_profile.refresh_from_db()
        self.assertTrue(consultation.is_free)
        self.assertEqual(self.tmc_profile.free_consultations_used, 1)
        self.assertFalse(Payment.objects.filter(consultation=consultation).exists())
        finance = ConsultationFinance.objects.get(consultation=consultation)
        self.assertEqual(finance.billing_type, ConsultationFinance.BillingType.FREE)
        account = TMCAccount.objects.get(tmc=self.tmc_profile)
        self.assertTrue(TMCAccountEntry.objects.filter(account=account, consultation=consultation).exists())

    def test_tmc_dashboard_booking_does_not_require_admin_wallet_for_free_quota(self):
        admin_account = AdminPlatformAccount.objects.get(name="Platform Wallet")
        admin_account.balance = "0.00"
        admin_account.save(update_fields=["balance"])
        self.patient_profile.created_by_tmc = self.tmc_profile
        self.patient_profile.save(update_fields=["created_by_tmc"])
        self.client.force_authenticate(user=self.tmc_user)

        response = self.client.post(
            reverse("tmc-book-consultation"),
            {
                "patient_id": self.patient_profile.id,
                "doctor_id": self.doctor_profile.id,
                "amount": "100.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        consultation = Consultation.objects.get(id=response.data["consultation_id"])
        self.assertTrue(consultation.is_free)
        self.assertEqual(str(consultation.finance.amount_charged), "0.00")

    def test_tmc_consultation_list_includes_free_status(self):
        """TMC dashboard needs is_free to show free quota consultations correctly."""
        consultation = Consultation.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tmc=self.tmc_profile,
            consultation_type=Consultation.ConsultationType.TMC,
            scheduled_time=timezone.now() + timezone.timedelta(minutes=10),
            status=Consultation.StatusChoices.COMPLETED,
            is_completed=True,
            is_free=True,
        )
        ConsultationFinance.objects.create(
            consultation=consultation,
            source_type=ConsultationFinance.SourceType.TMC,
            billing_type=ConsultationFinance.BillingType.FREE,
            payer_entity=ConsultationFinance.PayerEntity.TMC,
            payment_status=ConsultationFinance.PaymentStatus.NOT_REQUIRED,
            amount_charged="0.00",
            doctor_earning_status=ConsultationFinance.DoctorEarningStatus.NOT_APPLICABLE,
        )
        self.client.force_authenticate(user=self.tmc_user)

        response = self.client.get(reverse("tmc-consultations"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(item for item in response.data if item["id"] == consultation.id)
        self.assertTrue(row["is_free"])
        self.assertEqual(row["billing_type"], ConsultationFinance.BillingType.FREE)

    def test_tmc_booking_creates_payment_after_quota_exhausted(self):
        """Once TMC free quota is exhausted, bookings should create a paid Payment."""
        self.doctor_profile.consultation_fee = "500.00"
        self.doctor_profile.save(update_fields=["consultation_fee"])
        self.authenticate_tmc()

        url = reverse("tmc-book-consultation")

        self.tmc_profile.free_consultations_used = self.tmc_profile.free_consultation_quota
        self.tmc_profile.save(update_fields=["free_consultations_used"])

        # Second booking: should create Payment
        response = self.client.post(
            url,
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "TMC",
                "tmc_id": self.tmc_profile.id,
                "patient_id": self.patient_profile.id,
                "amount": "500.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        consultation = Consultation.objects.get(id=response.data["consultation_id"])
        payment = Payment.objects.get(consultation=consultation)

        self.assertFalse(consultation.is_free)
        self.assertEqual(str(payment.amount), "500.00")
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertTrue(payment.paid_by_tmc)
        finance = ConsultationFinance.objects.get(consultation=consultation)
        self.assertEqual(finance.billing_type, ConsultationFinance.BillingType.PAID)
        self.assertEqual(finance.payer_entity, ConsultationFinance.PayerEntity.TMC)

    def test_tmc_free_consultation_pays_doctor_from_admin_wallet_on_completion(self):
        self.authenticate_tmc()
        response = self.client.post(
            reverse("tmc-book-consultation"),
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "TMC",
                "tmc_id": self.tmc_profile.id,
                "patient_id": self.patient_profile.id,
                "amount": "100.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        consultation_id = response.data["consultation_id"]
        consultation = Consultation.objects.get(id=consultation_id)
        finance = ConsultationFinance.objects.get(consultation=consultation)
        self.assertTrue(consultation.is_free)
        self.assertEqual(str(finance.doctor_fee), "100.00")
        self.assertEqual(str(finance.amount_charged), "0.00")
        self.assertEqual(str(finance.admin_subsidy_amount), "100.00")

        self.client.force_authenticate(user=self.doctor_user)
        self.client.patch(
            reverse("doctor-response", kwargs={"pk": consultation_id}),
            {"status": "ACCEPTED"},
            format="json",
        )
        consultation.refresh_from_db()
        if consultation.status == Consultation.StatusChoices.QUEUED:
            self.client.post(reverse("start-consultation", kwargs={"consultation_id": consultation_id}))
        self.client.post(reverse("complete-consultation", kwargs={"consultation_id": consultation_id}))

        earning = DoctorEarning.objects.get(consultation_id=consultation_id)
        self.assertEqual(str(earning.earning_amount), "100.00")
        self.assertEqual(earning.status, DoctorEarning.Status.EARNED)
        admin_account = AdminPlatformAccount.objects.get(name="Platform Wallet")
        self.assertEqual(str(admin_account.total_doctor_subsidies), "100.00")
        self.assertTrue(
            AdminPlatformEntry.objects.filter(
                consultation_id=consultation_id,
                entry_type=AdminPlatformEntry.EntryType.DOCTOR_SUBSIDY,
                amount="100.00",
            ).exists()
        )

    def test_tmc_discount_quota_charges_discounted_fee_plus_platform_fee(self):
        ConsultationFeeSetting.objects.filter(is_active=True).update(is_active=False)
        ConsultationFeeSetting.objects.create(
            name="Platform fee test",
            direct_patient_fee="0.00",
            tmc_consultation_fee="0.00",
            platform_fee_percentage="10.00",
            is_active=True,
        )
        self.tmc_profile.free_consultations_used = self.tmc_profile.free_consultation_quota
        self.tmc_profile.discount_percentage = "10.00"
        self.tmc_profile.discounted_consultation_quota = 100
        self.tmc_profile.discounted_consultations_used = 0
        self.tmc_profile.save(
            update_fields=[
                "free_consultations_used",
                "discount_percentage",
                "discounted_consultation_quota",
                "discounted_consultations_used",
            ]
        )
        self.authenticate_tmc()

        response = self.client.post(
            reverse("tmc-book-consultation"),
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "TMC",
                "tmc_id": self.tmc_profile.id,
                "patient_id": self.patient_profile.id,
                "amount": "100.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        consultation = Consultation.objects.get(id=response.data["consultation_id"])
        finance = ConsultationFinance.objects.get(consultation=consultation)
        payment = Payment.objects.get(consultation=consultation)
        self.tmc_profile.refresh_from_db()

        self.assertFalse(consultation.is_free)
        self.assertEqual(str(finance.doctor_fee), "100.00")
        self.assertEqual(str(finance.discount_amount), "10.00")
        self.assertEqual(str(finance.platform_fee), "10.00")
        self.assertEqual(str(finance.admin_subsidy_amount), "10.00")
        self.assertEqual(str(finance.amount_charged), "100.00")
        self.assertEqual(str(payment.amount), "100.00")
        self.assertEqual(self.tmc_profile.discounted_consultations_used, 1)
        admin_account = AdminPlatformAccount.objects.get(name="Platform Wallet")
        self.assertEqual(str(admin_account.total_platform_fees), "10.00")

    def test_tmc_full_price_after_discount_quota_adds_platform_fee(self):
        ConsultationFeeSetting.objects.filter(is_active=True).update(is_active=False)
        ConsultationFeeSetting.objects.create(
            name="Platform fee test",
            direct_patient_fee="0.00",
            tmc_consultation_fee="0.00",
            platform_fee_percentage="10.00",
            is_active=True,
        )
        self.tmc_profile.free_consultations_used = self.tmc_profile.free_consultation_quota
        self.tmc_profile.discount_percentage = "10.00"
        self.tmc_profile.discounted_consultation_quota = 1
        self.tmc_profile.discounted_consultations_used = 1
        self.tmc_profile.save(
            update_fields=[
                "free_consultations_used",
                "discount_percentage",
                "discounted_consultation_quota",
                "discounted_consultations_used",
            ]
        )
        self.authenticate_tmc()

        response = self.client.post(
            reverse("tmc-book-consultation"),
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "TMC",
                "tmc_id": self.tmc_profile.id,
                "patient_id": self.patient_profile.id,
                "amount": "100.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        finance = ConsultationFinance.objects.get(consultation_id=response.data["consultation_id"])
        payment = Payment.objects.get(consultation_id=response.data["consultation_id"])
        self.assertEqual(str(finance.doctor_fee), "100.00")
        self.assertEqual(str(finance.discount_amount), "0.00")
        self.assertEqual(str(finance.platform_fee), "10.00")
        self.assertEqual(str(finance.admin_subsidy_amount), "0.00")
        self.assertEqual(str(finance.amount_charged), "110.00")
        self.assertEqual(str(payment.amount), "110.00")

    def test_doctor_earning_created_on_completion(self):
        self.doctor_profile.consultation_fee = "300.00"
        self.doctor_profile.save(update_fields=["consultation_fee"])
        self.authenticate_patient()
        booking = self.client.post(
            reverse("book-consultation"),
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "DIRECT",
                "amount": "300.00",
            },
            format="json",
        )
        self.assertEqual(booking.status_code, status.HTTP_201_CREATED)
        consultation_id = booking.data["consultation_id"]
        consultation = Consultation.objects.get(id=consultation_id)

        # doctor accepts -> may start immediately
        self.client.force_authenticate(user=self.doctor_user)
        self.client.patch(
            reverse("doctor-response", kwargs={"pk": consultation_id}),
            {"status": "ACCEPTED"},
            format="json",
        )
        consultation.refresh_from_db()
        if consultation.status == Consultation.StatusChoices.QUEUED:
            self.client.post(reverse("start-consultation", kwargs={"consultation_id": consultation_id}))
        self.client.post(reverse("complete-consultation", kwargs={"consultation_id": consultation_id}))

        earning = DoctorEarning.objects.get(consultation_id=consultation_id)
        self.assertEqual(str(earning.earning_amount), "300.00")

    def test_direct_booking_rejects_insufficient_patient_wallet_balance(self):
        PatientWallet.objects.filter(patient=self.patient_profile).delete()
        self.authenticate_patient()

        response = self.client.post(
            reverse("book-consultation"),
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "DIRECT",
                "amount": "250.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("wallet", response.data)
        self.assertFalse(Consultation.objects.exists())

    def test_direct_booking_uses_doctor_fee_when_amount_not_provided(self):
        self.doctor_profile.consultation_fee = "750.00"
        self.doctor_profile.save(update_fields=["consultation_fee"])
        wallet = PatientWallet.objects.get(patient=self.patient_profile)
        wallet.balance = "700.00"
        wallet.save(update_fields=["balance"])
        self.authenticate_patient()

        response = self.client.post(
            reverse("book-consultation"),
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "DIRECT",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("wallet", response.data)
        self.assertFalse(Consultation.objects.exists())

    def test_patient_cannot_book_another_consultation_while_one_is_open(self):
        self.authenticate_patient()
        Consultation.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            scheduled_time=timezone.now() + timezone.timedelta(minutes=10),
            consultation_type=Consultation.ConsultationType.DIRECT,
            status=Consultation.StatusChoices.IN_PROGRESS,
        )

        response = self.client.post(
            reverse("book-consultation"),
            {
                "doctor_id": self.alt_doctor_profile.id,
                "consultation_type": "DIRECT",
                "amount": "100.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("consultation", response.data)

    def test_tmc_paid_booking_rejects_insufficient_tmc_wallet_balance(self):
        self.tmc_profile.free_consultations_used = self.tmc_profile.free_consultation_quota
        self.tmc_profile.save(update_fields=["free_consultations_used"])
        TMCAccount.objects.filter(tmc=self.tmc_profile).delete()
        self.authenticate_tmc()

        response = self.client.post(
            reverse("tmc-book-consultation"),
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "TMC",
                "tmc_id": self.tmc_profile.id,
                "patient_id": self.patient_profile.id,
                "amount": "500.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficient TMC wallet balance", str(response.data))
        self.assertFalse(Consultation.objects.exists())
        self.assertFalse(Payment.objects.exists())

    def test_booking_respects_doctor_daily_limit(self):
        """Doctor should not exceed max_daily_consultations."""
        self.authenticate_patient()
        url = reverse("book-consultation")

        # First booking succeeds
        response1 = self.client.post(
            url,
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "DIRECT",
                "amount": "100.00",
            },
            format="json",
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second booking same day should fall back to alternate doctor
        self.authenticate_new_patient()
        response2 = self.client.post(
            url,
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "DIRECT",
                "amount": "100.00",
            },
            format="json",
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        consultation = Consultation.objects.get(id=response2.data["consultation_id"])
        # Should have been reassigned to alternate doctor
        self.assertEqual(consultation.doctor, self.alt_doctor_profile)

    def test_conflicting_slot_uses_fallback_doctor(self):
        """If selected doctor already has a consultation at the requested time, choose fallback."""
        self.authenticate_new_patient()
        url = reverse("book-consultation")

        # Book initial consultation at a fixed time
        scheduled_time = timezone.now() + timezone.timedelta(hours=1)
        Consultation.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            scheduled_time=scheduled_time,
            consultation_type=Consultation.ConsultationType.DIRECT,
            status=Consultation.StatusChoices.PENDING,
        )

        response = self.client.post(
            url,
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "DIRECT",
                "scheduled_time": scheduled_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        consultation = Consultation.objects.get(id=response.data["consultation_id"])
        self.assertEqual(consultation.doctor, self.alt_doctor_profile)

    def test_doctor_schedule_rejects_overlapping_slot(self):
        self.client.force_authenticate(user=self.doctor_user)
        url = reverse("doctor-schedule")
        first = self.client.post(
            url,
            {
                "day_of_week": "Monday",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "is_online": True,
            },
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        overlap = self.client.post(
            url,
            {
                "day_of_week": "Monday",
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "is_online": True,
            },
            format="json",
        )
        self.assertEqual(overlap.status_code, status.HTTP_400_BAD_REQUEST)

    def test_doctor_schedule_can_pause_delete_and_reactivate_without_overlap(self):
        self.client.force_authenticate(user=self.doctor_user)
        url = reverse("doctor-schedule")
        active = self.client.post(
            url,
            {
                "day_of_week": "Tuesday",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "is_online": True,
                "consultation_duration_minutes": 30,
            },
            format="json",
        )
        self.assertEqual(active.status_code, status.HTTP_201_CREATED)

        inactive = self.client.post(
            url,
            {
                "day_of_week": "Tuesday",
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "is_online": True,
                "is_active": False,
            },
            format="json",
        )
        self.assertEqual(inactive.status_code, status.HTTP_201_CREATED)

        reactivate = self.client.patch(
            reverse("doctor-schedule-detail", kwargs={"pk": inactive.data["id"]}),
            {"is_active": True},
            format="json",
        )
        self.assertEqual(reactivate.status_code, status.HTTP_400_BAD_REQUEST)

        pause = self.client.patch(
            reverse("doctor-schedule-detail", kwargs={"pk": active.data["id"]}),
            {"is_active": False},
            format="json",
        )
        self.assertEqual(pause.status_code, status.HTTP_200_OK)

        reactivate_after_pause = self.client.patch(
            reverse("doctor-schedule-detail", kwargs={"pk": inactive.data["id"]}),
            {"is_active": True},
            format="json",
        )
        self.assertEqual(reactivate_after_pause.status_code, status.HTTP_200_OK)

        delete = self.client.delete(reverse("doctor-schedule-detail", kwargs={"pk": active.data["id"]}))
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_booking_respects_configured_online_schedule(self):
        self.authenticate_patient()
        target_time = timezone.now() + timezone.timedelta(days=3)
        target_time = target_time.replace(hour=15, minute=0, second=0, microsecond=0)
        day_name = target_time.strftime("%A")
        DoctorSchedule.objects.create(
            doctor=self.doctor_profile,
            day_of_week=day_name,
            start_time="09:00:00",
            end_time="10:00:00",
            is_online=True,
        )
        DoctorSchedule.objects.create(
            doctor=self.alt_doctor_profile,
            day_of_week=day_name,
            start_time="09:00:00",
            end_time="10:00:00",
            is_online=True,
        )

        response = self.client.post(
            reverse("book-consultation"),
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "DIRECT",
                "scheduled_time": target_time.isoformat(),
                "amount": "100.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("doctor", response.data)

    def test_booking_must_fit_inside_schedule_duration_window(self):
        self.authenticate_patient()
        target_time = timezone.now() + timezone.timedelta(days=4)
        target_time = target_time.replace(hour=9, minute=15, second=0, microsecond=0)
        day_name = target_time.strftime("%A")
        DoctorSchedule.objects.create(
            doctor=self.doctor_profile,
            day_of_week=day_name,
            start_time="09:00:00",
            end_time="09:30:00",
            is_online=True,
            consultation_duration_minutes=30,
        )
        DoctorSchedule.objects.create(
            doctor=self.alt_doctor_profile,
            day_of_week=day_name,
            start_time="09:00:00",
            end_time="09:30:00",
            is_online=True,
            consultation_duration_minutes=30,
        )

        response = self.client.post(
            reverse("book-consultation"),
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "DIRECT",
                "scheduled_time": target_time.isoformat(),
                "amount": "100.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("doctor", response.data)




    def _assert_submitted_amounts_cannot_set_price(self, url, payload, doctor_fee, charge, *, tmc=False):
        for amount in ("1.00", "0.00", "9999.00", None):
            with self.subTest(submitted_amount=amount), transaction.atomic():
                request_data = dict(payload)
                if amount is not None:
                    request_data["amount"] = amount
                request_data.update({"is_free": True, "doctor_fee": "1.00", "discount_percentage": "100"})
                response = self.client.post(url, request_data, format="json")
                self.assertEqual(response.status_code, 201, response.data)
                consultation = Consultation.objects.get(pk=response.data["consultation_id"])
                self.assertFalse(consultation.is_free)
                self.assertEqual(str(consultation.finance.doctor_fee), doctor_fee)
                self.assertEqual(str(consultation.finance.amount_charged), charge)
                self.assertEqual(str(consultation.payment.amount), charge)
                if tmc:
                    account = TMCAccount.objects.get(tmc=self.tmc_profile)
                    entry = TMCAccountEntry.objects.get(account=account, consultation=consultation)
                else:
                    account = PatientWallet.objects.get(patient=self.patient_profile)
                    entry = PatientWalletEntry.objects.get(wallet=account, consultation=consultation)
                self.assertEqual(str(entry.amount), charge)
                self.assertEqual(account.balance, 5000 - entry.amount)
                transaction.set_rollback(True)

    def test_direct_booking_ignores_submitted_prices_and_keeps_platform_fee(self):
        self.doctor_profile.consultation_fee = "250.00"
        self.doctor_profile.save(update_fields=["consultation_fee"])
        ConsultationFeeSetting.objects.create(platform_fee_percentage="10.00")
        self.authenticate_patient()
        self._assert_submitted_amounts_cannot_set_price(
            reverse("book-consultation"),
            {"doctor_id": self.doctor_profile.id, "consultation_type": "DIRECT"},
            "250.00", "275.00",
        )

    def _configure_paid_tmc_discount(self):
        self.tmc_profile.free_consultations_used = self.tmc_profile.free_consultation_quota
        self.tmc_profile.discount_percentage = "10.00"
        self.tmc_profile.discounted_consultation_quota = 20
        self.tmc_profile.save(update_fields=["free_consultations_used", "discount_percentage", "discounted_consultation_quota"])

    def test_patient_cannot_authorise_tmc_wallet_with_submitted_prices(self):
        self._configure_paid_tmc_discount()
        self.authenticate_patient()
        for amount in ("1.00", "0.00", "9999.00"):
            response = self.client.post(reverse("book-consultation"), {
                "doctor_id": self.doctor_profile.id, "consultation_type": "TMC",
                "tmc_id": self.tmc_profile.id, "amount": amount,
            }, format="json")
            self.assertEqual(response.status_code, 403, response.data)
        self.assertFalse(Consultation.objects.exists())
        self.assertEqual(str(TMCAccount.objects.get(tmc=self.tmc_profile).balance), "5000.00")

    def test_tmc_dashboard_booking_ignores_submitted_prices(self):
        self._configure_paid_tmc_discount()
        self.patient_profile.created_by_tmc = self.tmc_profile
        self.patient_profile.save(update_fields=["created_by_tmc"])
        self.client.force_authenticate(user=self.tmc_user)
        self._assert_submitted_amounts_cannot_set_price(
            reverse("tmc-book-consultation"),
            {"doctor_id": self.doctor_profile.id, "patient_id": self.patient_profile.id},
            "100.00", "90.00", tmc=True,
        )

    def test_low_submitted_amount_cannot_bypass_wallet_balance_checks(self):
        PatientWallet.objects.filter(patient=self.patient_profile).update(balance="50.00")
        self.authenticate_patient()
        response = self.client.post(reverse("book-consultation"),
            {"doctor_id": self.doctor_profile.id, "consultation_type": "DIRECT", "amount": "1.00"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Consultation.objects.exists())
        self.tmc_profile.free_consultations_used = self.tmc_profile.free_consultation_quota
        self.tmc_profile.save(update_fields=["free_consultations_used"])
        self.patient_profile.created_by_tmc = self.tmc_profile
        self.patient_profile.save(update_fields=["created_by_tmc"])
        TMCAccount.objects.filter(tmc=self.tmc_profile).update(balance="50.00")
        self.client.force_authenticate(user=self.tmc_user)
        response = self.client.post(reverse("tmc-book-consultation"),
            {"doctor_id": self.doctor_profile.id, "patient_id": self.patient_profile.id, "amount": "1.00"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Consultation.objects.exists())

    def test_configured_global_fee_is_used_when_doctor_has_no_fee(self):
        self.doctor_profile.consultation_fee = None
        self.doctor_profile.save(update_fields=["consultation_fee"])
        ConsultationFeeSetting.objects.create(direct_patient_fee="180.00", tmc_consultation_fee="190.00")
        self.authenticate_patient()
        self._assert_submitted_amounts_cannot_set_price(
            reverse("book-consultation"),
            {"doctor_id": self.doctor_profile.id, "consultation_type": "DIRECT"}, "180.00", "180.00",
        )

    def test_different_fee_fallback_requires_reselection_without_charging(self):
        self.doctor_profile.availability.is_available_online = False
        self.doctor_profile.availability.save(update_fields=["is_available_online"])
        self.alt_doctor_profile.consultation_fee = "350.00"
        self.alt_doctor_profile.save(update_fields=["consultation_fee"])
        self.authenticate_patient()
        response = self.client.post(reverse("book-consultation"),
            {"doctor_id": self.doctor_profile.id, "consultation_type": "DIRECT", "amount": "1.00"}, format="json")
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("different fee", str(response.data))
        self.assertFalse(Consultation.objects.exists())
        self.assertFalse(Payment.objects.exists())
        self.assertFalse(PatientWalletEntry.objects.filter(consultation__isnull=False).exists())
        self.assertEqual(str(PatientWallet.objects.get(patient=self.patient_profile).balance), "5000.00")
