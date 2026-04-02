from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient

from users.models import User, DoctorProfile, PatientProfile, TMCProfile


class FinanceEndpointTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()
        self.doctor_user = User.objects.create_user(email="doctor-fin@test.com", password="testpass123", is_doctor=True)
        self.doctor_profile = DoctorProfile.objects.create(user=self.doctor_user, profile_completed=True)
        self.patient_user = User.objects.create_user(email="patient-fin@test.com", password="testpass123", is_patient=True)
        self.patient_profile = PatientProfile.objects.create(user=self.patient_user)
        self.tmc_user = User.objects.create_user(email="tmc-fin@test.com", password="testpass123", is_tmc_operator=True)
        self.tmc_profile = TMCProfile.objects.create(user=self.tmc_user, free_consultation_quota=2)

    def test_patient_wallet_summary_and_topup(self):
        self.client.force_authenticate(user=self.patient_user)
        topup = self.client.post(reverse("patient-wallet-summary"), {"amount": "500.00"}, format="json")
        self.assertEqual(topup.status_code, 201)
        summary = self.client.get(reverse("patient-wallet-summary"))
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.data["balance"], "500.00")

    def test_tmc_finance_summary_endpoint(self):
        self.client.force_authenticate(user=self.tmc_user)
        response = self.client.get(reverse("tmc-finance-summary"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("balance", response.data)
