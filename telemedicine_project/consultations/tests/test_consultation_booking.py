from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User, DoctorProfile, PatientProfile, TMCProfile
from consultations.models import (
    Consultation,
    Payment,
    ConsultationFinance,
    PatientWallet,
    PatientWalletEntry,
    TMCAccount,
    TMCAccountEntry,
    DoctorEarning,
)


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

    def authenticate_patient(self):
        self.client.force_authenticate(user=self.patient_user)

    def test_direct_consultation_booking_creates_payment_when_amount_provided(self):
        """Direct booking with amount should create a paid Payment linked to patient."""
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
        self.assertFalse(payment.paid_by_tmc)
        self.assertEqual(finance.billing_type, ConsultationFinance.BillingType.PAID)
        self.assertEqual(finance.payer_entity, ConsultationFinance.PayerEntity.PATIENT)
        self.assertTrue(PatientWalletEntry.objects.filter(wallet=wallet, consultation=consultation).exists())

    def test_tmc_booking_uses_free_quota_first(self):
        """First TMC booking should consume free quota and not create Payment."""
        self.authenticate_patient()

        url = reverse("book-consultation")
        payload = {
            "doctor_id": self.doctor_profile.id,
            "consultation_type": "TMC",
            "tmc_id": self.tmc_profile.id,
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

    def test_tmc_booking_creates_payment_after_quota_exhausted(self):
        """Once TMC free quota is exhausted, bookings should create a paid Payment."""
        self.authenticate_patient()

        url = reverse("book-consultation")

        # First booking: uses free quota
        self.client.post(
            url,
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "TMC",
                "tmc_id": self.tmc_profile.id,
            },
            format="json",
        )

        # Second booking: should create Payment
        response = self.client.post(
            url,
            {
                "doctor_id": self.doctor_profile.id,
                "consultation_type": "TMC",
                "tmc_id": self.tmc_profile.id,
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

    def test_doctor_earning_created_on_completion(self):
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
        self.authenticate_patient()
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


