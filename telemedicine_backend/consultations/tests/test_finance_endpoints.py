import hashlib
import hmac
import json
from unittest.mock import patch

from django.test import TransactionTestCase, override_settings
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import User, DoctorProfile, PatientProfile, TMCProfile
from consultations.models import (
    Consultation,
    ConsultationFeeSetting,
    Payment,
    PatientWallet,
    PatientWalletEntry,
    PatientWalletRechargeRequest,
    TMCAccount,
    TMCAccountEntry,
    TMCRechargeRequest,
)


class FinanceEndpointTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()
        self.doctor_user = User.objects.create_user(email="doctor-fin@test.com", password="testpass123", is_doctor=True)
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            profile_completed=True,
            admin_verified=True,
            is_approved=True,
        )
        self.patient_user = User.objects.create_user(email="patient-fin@test.com", password="testpass123", is_patient=True)
        self.patient_profile = PatientProfile.objects.create(user=self.patient_user)
        self.tmc_user = User.objects.create_user(email="tmc-fin@test.com", password="testpass123", is_tmc_operator=True)
        self.tmc_profile = TMCProfile.objects.create(user=self.tmc_user, free_consultation_quota=2)

    def test_patient_wallet_summary_and_staff_topup(self):
        staff = User.objects.create_user(
            email="staff-fin@test.com", password="testpass123", is_staff=True
        )
        staff.user_permissions.add(Permission.objects.get(content_type__app_label="consultations", codename="change_patientwallet"))
        self.client.force_authenticate(user=staff)
        topup = self.client.post(
            reverse("staff-patient-wallet-topup"),
            {"patient_profile_id": self.patient_profile.id, "amount": "500.00"},
            format="json",
        )
        self.assertEqual(topup.status_code, 201)
        self.client.force_authenticate(user=self.patient_user)
        summary = self.client.get(reverse("patient-wallet-summary"))
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.data["balance"], "500.00")

    def test_patient_recharge_request_and_staff_approval(self):
        self.client.force_authenticate(user=self.patient_user)
        request_response = self.client.post(
            reverse("patient-wallet-summary"),
            {"amount": "700.00", "reference_note": "UPI-TEST"},
            format="json",
        )
        self.assertEqual(request_response.status_code, 201)
        recharge_id = request_response.data["id"]
        self.assertEqual(PatientWalletRechargeRequest.objects.get(id=recharge_id).status, "PENDING")

        staff = User.objects.create_user(
            email="staff-patient-recharge@test.com", password="testpass123", is_staff=True
        )
        staff.user_permissions.add(Permission.objects.get(content_type__app_label="consultations", codename="change_patientwalletrechargerequest"))
        self.client.force_authenticate(user=staff)
        list_response = self.client.get(reverse("staff-patient-recharge-list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertTrue(any(row["id"] == recharge_id for row in list_response.data))
        approve_response = self.client.post(
            reverse("staff-patient-recharge-process", kwargs={"recharge_id": recharge_id}),
            {"action": "approve", "admin_note": "Verified"},
            format="json",
        )
        self.assertEqual(approve_response.status_code, 200)
        wallet = PatientWallet.objects.get(patient=self.patient_profile)
        self.assertEqual(str(wallet.balance), "700.00")

    def test_patient_wallet_summary_reconciles_legacy_manual_approved_recharge(self):
        recharge = PatientWalletRechargeRequest.objects.create(
            patient=self.patient_profile,
            amount="200.00",
            status=PatientWalletRechargeRequest.Status.APPROVED,
            provider=PatientWalletRechargeRequest.Provider.MANUAL,
            reference_note="ADMIN-APPROVED",
        )
        self.client.force_authenticate(user=self.patient_user)

        response = self.client.get(reverse("patient-wallet-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["balance"], "200.00")
        wallet = PatientWallet.objects.get(patient=self.patient_profile)
        self.assertEqual(str(wallet.total_credited), "200.00")
        self.assertTrue(
            PatientWalletEntry.objects.filter(
                wallet=wallet,
                description=f"Approved recharge request #{recharge.id}",
                amount="200.00",
            ).exists()
        )

    def test_staff_patient_list_includes_wallet_and_source_type(self):
        Consultation.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            consultation_type=Consultation.ConsultationType.DIRECT,
            scheduled_time=timezone.now() + timezone.timedelta(days=1),
        )
        Consultation.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            tmc=self.tmc_profile,
            consultation_type=Consultation.ConsultationType.TMC,
            scheduled_time=timezone.now() + timezone.timedelta(days=2),
        )
        staff = User.objects.create_user(
            email="staff-patients@test.com", password="testpass123", is_staff=True
        )
        self.client.force_authenticate(user=staff)

        response = self.client.get(reverse("staff-patient-list"))

        self.assertEqual(response.status_code, 200)
        row = next(item for item in response.data if item["id"] == self.patient_profile.id)
        self.assertEqual(row["patient_type"], "BOTH")
        self.assertEqual(row["direct_consultations"], 1)
        self.assertEqual(row["tmc_consultations"], 1)
        self.assertIn("wallet_balance", row)

    def test_tmc_finance_summary_endpoint(self):
        self.client.force_authenticate(user=self.tmc_user)
        response = self.client.get(reverse("tmc-finance-summary"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("balance", response.data)

    def test_tmc_recharge_request_and_staff_approval(self):
        self.client.force_authenticate(user=self.tmc_user)
        request_response = self.client.post(
            reverse("tmc-recharge-requests"),
            {"amount": "1200.00", "reference_note": "UTR-TEST"},
            format="json",
        )
        self.assertEqual(request_response.status_code, 201)
        recharge_id = request_response.data["id"]
        self.assertEqual(TMCRechargeRequest.objects.get(id=recharge_id).status, "PENDING")

        staff = User.objects.create_user(
            email="staff-tmc-fin@test.com", password="testpass123", is_staff=True
        )
        staff.user_permissions.add(Permission.objects.get(content_type__app_label="consultations", codename="change_tmcrechargerequest"))
        self.client.force_authenticate(user=staff)
        approve_response = self.client.post(
            reverse("staff-tmc-recharge-process", kwargs={"recharge_id": recharge_id}),
            {"action": "approve", "admin_note": "Verified"},
            format="json",
        )
        self.assertEqual(approve_response.status_code, 200)
        account = TMCAccount.objects.get(tmc=self.tmc_profile)
        self.assertEqual(str(account.balance), "1200.00")

    @override_settings(RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET="", RAZORPAY_ENABLED=False)
    def test_tmc_razorpay_order_can_be_canceled_without_pending_request(self):
        self.client.force_authenticate(user=self.tmc_user)
        request_response = self.client.post(
            reverse("tmc-recharge-requests"),
            {"amount": "500.00"},
            format="json",
        )
        recharge_id = request_response.data["id"]

        order_response = self.client.post(reverse("tmc-razorpay-order", kwargs={"recharge_id": recharge_id}), {}, format="json")
        self.assertEqual(order_response.status_code, 200)
        self.assertTrue(order_response.data["order_id"].startswith("order_dev_tmc_"))

        cancel_response = self.client.post(reverse("tmc-recharge-cancel", kwargs={"recharge_id": recharge_id}), {}, format="json")
        self.assertEqual(cancel_response.status_code, 200)
        recharge = TMCRechargeRequest.objects.get(id=recharge_id)
        self.assertEqual(recharge.status, TMCRechargeRequest.Status.CANCELED)
        summary = self.client.get(reverse("tmc-finance-summary"))
        canceled_row = next(row for row in summary.data["recent_recharge_requests"] if row["id"] == recharge_id)
        self.assertEqual(canceled_row["status"], TMCRechargeRequest.Status.CANCELED)

    @override_settings(RAZORPAY_KEY_ID="rzp_test_key", RAZORPAY_KEY_SECRET="test_secret", RAZORPAY_ENABLED=True)
    def test_tmc_razorpay_verify_credits_wallet_immediately(self):
        recharge = TMCRechargeRequest.objects.create(
            tmc=self.tmc_profile,
            amount="900.00",
            requested_by=self.tmc_user,
            provider=TMCRechargeRequest.Provider.RAZORPAY,
            gateway_order_id="order_test_tmc_123",
        )
        gateway_payment_id = "pay_tmc_123"
        signature = hmac.new(
            b"test_secret",
            f"{recharge.gateway_order_id}|{gateway_payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        self.client.force_authenticate(user=self.tmc_user)

        response = self.client.post(
            reverse("tmc-razorpay-verify", kwargs={"recharge_id": recharge.id}),
            {"razorpay_payment_id": gateway_payment_id, "razorpay_signature": signature},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        recharge.refresh_from_db()
        account = TMCAccount.objects.get(tmc=self.tmc_profile)
        self.assertEqual(recharge.status, TMCRechargeRequest.Status.APPROVED)
        self.assertEqual(str(account.balance), "900.00")
        self.assertTrue(
            TMCAccountEntry.objects.filter(
                account=account,
                description=f"Razorpay TMC wallet recharge #{recharge.id}",
            ).exists()
        )

    def test_staff_fee_settings_create_active_setting(self):
        staff = User.objects.create_user(
            email="staff-fee@test.com", password="testpass123", is_staff=True
        )
        staff.user_permissions.add(Permission.objects.get(content_type__app_label="consultations", codename="add_consultationfeesetting"))
        self.client.force_authenticate(user=staff)
        response = self.client.post(
            reverse("staff-fee-settings"),
            {"direct_patient_fee": "300.00", "tmc_consultation_fee": "250.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        setting = ConsultationFeeSetting.objects.get(id=response.data["id"])
        self.assertTrue(setting.is_active)
        self.assertEqual(str(setting.direct_patient_fee), "300.00")

    @override_settings(RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET="", RAZORPAY_ENABLED=False)
    def test_razorpay_order_reference_can_be_prepared_without_keys(self):
        consultation = Consultation.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            consultation_type=Consultation.ConsultationType.DIRECT,
            scheduled_time=timezone.now() + timezone.timedelta(days=1),
        )
        payment = Payment.objects.create(consultation=consultation, amount="350.00", status=Payment.Status.PENDING)
        self.client.force_authenticate(user=self.patient_user)

        response = self.client.post(reverse("razorpay-order", kwargs={"payment_id": payment.id}), {}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["provider"], "RAZORPAY")
        self.assertTrue(response.data["gateway_order_id"].startswith("order_dev_"))
        self.assertFalse(response.data["key_id_configured"])

    @override_settings(RAZORPAY_KEY_ID="rzp_test_key", RAZORPAY_KEY_SECRET="test_secret", RAZORPAY_ENABLED=True)
    @patch("consultations.finance.urlopen")
    def test_razorpay_verify_marks_payment_paid_with_valid_signature(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(
            {"id": "order_test_123", "amount": 35000, "currency": "INR"}
        ).encode("utf-8")
        consultation = Consultation.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            consultation_type=Consultation.ConsultationType.DIRECT,
            scheduled_time=timezone.now() + timezone.timedelta(days=1),
        )
        payment = Payment.objects.create(consultation=consultation, amount="350.00", status=Payment.Status.PENDING)
        self.client.force_authenticate(user=self.patient_user)
        order_response = self.client.post(reverse("razorpay-order", kwargs={"payment_id": payment.id}), {}, format="json")
        self.assertEqual(order_response.status_code, 200, order_response.data)
        mock_urlopen.assert_called_once()
        gateway_request = mock_urlopen.call_args.args[0]
        self.assertEqual(gateway_request.full_url, "https://api.razorpay.com/v1/orders")
        self.assertEqual(gateway_request.get_method(), "POST")
        order_payload = json.loads(gateway_request.data)
        self.assertEqual(order_payload["amount"], 35000)
        self.assertEqual(order_payload["currency"], "INR")
        order_id = order_response.data["gateway_order_id"]
        self.assertEqual(order_id, "order_test_123")
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PENDING)
        gateway_payment_id = "pay_test_123"
        signature = hmac.new(
            b"test_secret",
            f"{order_id}|{gateway_payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = self.client.post(
            reverse("razorpay-verify", kwargs={"payment_id": payment.id}),
            {"razorpay_payment_id": gateway_payment_id, "razorpay_signature": signature},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(payment.gateway_payment_id, gateway_payment_id)
