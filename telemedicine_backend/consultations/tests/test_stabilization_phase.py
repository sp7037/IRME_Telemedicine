from django.urls import reverse
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User, DoctorProfile, PatientProfile
from consultations.models import (
    Consultation, Prescription, PrescriptionVersion,
    PatientWallet, PatientWalletEntry, PatientWalletRechargeRequest,
)


class StabilizationPhaseTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()
        self.doctor_user = User.objects.create_user(
            email="doc-stab@test.com", password="x", is_doctor=True
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            profile_completed=True,
            admin_verified=True,
            is_approved=True,
        )
        self.patient_user = User.objects.create_user(
            email="pat-stab@test.com", password="x", is_patient=True
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        self.consultation = Consultation.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            consultation_type=Consultation.ConsultationType.DIRECT,
            status=Consultation.StatusChoices.IN_PROGRESS,
            scheduled_time=timezone.now(),
        )
        self.staff = User.objects.create_user(email="staff-stab@test.com", password="x", is_staff=True)

    def test_prescription_create_then_update_creates_versions(self):
        self.client.force_authenticate(user=self.doctor_user)
        url = reverse("prescription", kwargs={"consultation_id": self.consultation.id})
        r1 = self.client.post(
            url,
            {"medicines": [{"name": "A", "dose": "1"}], "instructions": "rest"},
            format="json",
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        rx = Prescription.objects.get(consultation=self.consultation)
        self.assertEqual(rx.versions.count(), 1)

        r2 = self.client.put(
            url,
            {"medicines": [{"name": "B", "dose": "2"}], "instructions": "rest"},
            format="json",
        )
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        rx.refresh_from_db()
        self.assertEqual(rx.medicines[0]["name"], "B")
        self.assertGreaterEqual(rx.versions.count(), 2)

    def test_patient_cannot_list_prescription_versions(self):
        self.client.force_authenticate(user=self.doctor_user)
        url = reverse("prescription", kwargs={"consultation_id": self.consultation.id})
        self.client.post(url, {"medicines": [{"name": "A"}]}, format="json")
        vurl = reverse("prescription-versions", kwargs={"consultation_id": self.consultation.id})
        self.client.force_authenticate(user=self.patient_user)
        r = self.client.get(vurl)
        self.assertEqual(r.status_code, 403)

    def test_events_order_asc(self):
        self.client.force_authenticate(user=self.patient_user)
        url = reverse("consultation-events", kwargs={"consultation_id": self.consultation.id})
        r = self.client.get(url, {"order": "asc"})
        self.assertEqual(r.status_code, 200)
        if len(r.data) >= 2:
            self.assertLessEqual(r.data[0]["created_at"], r.data[-1]["created_at"])

    def test_staff_reports_and_patient_recharge_request_does_not_credit_wallet(self):
        wallet, _ = PatientWallet.objects.get_or_create(patient=self.patient)
        initial_totals = (wallet.balance, wallet.total_credited, wallet.total_debited)
        initial_entries = PatientWalletEntry.objects.filter(wallet=wallet).count()
        self.client.force_authenticate(user=self.patient_user)
        self.assertEqual(self.client.get(reverse("staff-operations-report")).status_code, 403)
        recharge_response = self.client.post(reverse("patient-wallet-summary"), {"amount": "1"}, format="json")
        self.assertEqual(recharge_response.status_code, 201)
        recharge = PatientWalletRechargeRequest.objects.get(id=recharge_response.data["id"])
        self.assertEqual(recharge.patient_id, self.patient.id)
        self.assertEqual(recharge.requested_by_id, self.patient_user.id)
        self.assertEqual(recharge.status, PatientWalletRechargeRequest.Status.PENDING)
        self.assertEqual(str(recharge.amount), "1.00")
        wallet.refresh_from_db()
        self.assertEqual((wallet.balance, wallet.total_credited, wallet.total_debited), initial_totals)
        self.assertEqual(PatientWalletEntry.objects.filter(wallet=wallet).count(), initial_entries)

        self.client.force_authenticate(user=self.staff)
        rep = self.client.get(reverse("staff-operations-report"))
        self.assertEqual(rep.status_code, 200)
        self.assertIn("consultations_total", rep.data)

        csv_r = self.client.get(reverse("staff-export-summary"))
        self.assertEqual(csv_r.status_code, 200)
        self.assertIn("text/csv", csv_r["Content-Type"])

    def test_create_consultation_finance_idempotent(self):
        from consultations.finance import create_consultation_finance
        from consultations.models import ConsultationFinance

        self.consultation.is_free = True
        self.consultation.save(update_fields=["is_free"])
        f1 = create_consultation_finance(self.consultation, amount="0")
        f2 = create_consultation_finance(self.consultation, amount="999.00")
        self.assertEqual(f1.id, f2.id)
        self.assertEqual(ConsultationFinance.objects.filter(consultation=self.consultation).count(), 1)
