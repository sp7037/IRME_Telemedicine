from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from users.models import User, DoctorProfile, PatientProfile, TMCProfile
from consultations.models import (
    Consultation, ConsultationEvent, ConsultationFinance, ConsultationFeeSetting,
    ConsultationFollowUpSession, Payment, PatientWallet, PatientWalletEntry,
    TMCAccount, TMCAccountEntry, TMCRechargeRequest,
)
from consultations.finance import patient_wallet_topup, tmc_account_topup


class TMCWalletOwnershipTests(APITestCase):
    def setUp(self):
        self.operator = User.objects.create_user(email="owner@ownership.test", password="testpass", is_tmc_operator=True)
        self.other_operator = User.objects.create_user(email="other@ownership.test", password="testpass", is_tmc_operator=True)
        self.tmc = TMCProfile.objects.create(user=self.operator)
        self.other_tmc = TMCProfile.objects.create(user=self.other_operator)
        self.patient_user = User.objects.create_user(email="patient@ownership.test", password="testpass", is_patient=True)
        self.patient = PatientProfile.objects.create(user=self.patient_user, created_by_tmc=self.tmc)
        other_patient_user = User.objects.create_user(email="other-patient@ownership.test", password="testpass", is_patient=True)
        self.other_patient = PatientProfile.objects.create(user=other_patient_user, created_by_tmc=self.other_tmc)
        self.doctor_user = User.objects.create_user(email="doctor@ownership.test", password="testpass", is_doctor=True)
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, consultation_fee="100.00",
            profile_completed=True, admin_verified=True, is_approved=True)
        ConsultationFeeSetting.objects.create(direct_patient_fee="100.00", tmc_consultation_fee="100.00")
        tmc_account_topup(self.tmc, "500.00", "Isolated test opening")
        tmc_account_topup(self.other_tmc, "500.00", "Isolated test opening")
        patient_wallet_topup(self.patient, "500.00", "Isolated test opening")

    @staticmethod
    def financial_state():
        return {
            "tmc_accounts": list(TMCAccount.objects.order_by("pk").values()),
            "patient_wallets": list(PatientWallet.objects.order_by("pk").values()),
            "quotas": list(TMCProfile.objects.order_by("pk").values("pk", "free_consultations_used", "discounted_consultations_used")),
            "tmc_entries": TMCAccountEntry.objects.count(),
            "patient_entries": PatientWalletEntry.objects.count(),
            "consultations": Consultation.objects.count(), "finance": ConsultationFinance.objects.count(),
            "payments": list(Payment.objects.order_by("pk").values()),
            "events": ConsultationEvent.objects.count(), "followups": ConsultationFollowUpSession.objects.count(),
            "recharges": list(TMCRechargeRequest.objects.order_by("pk").values()),
        }

    def completed_tmc_consultation(self):
        return Consultation.objects.create(patient=self.patient, doctor=self.doctor, tmc=self.tmc,
            consultation_type="TMC", scheduled_time=timezone.now(), status="COMPLETED", is_completed=True)

    def test_patient_cannot_spend_any_tmc_wallet_or_free_quota_via_generic_booking(self):
        self.tmc.free_consultation_quota = 2
        self.tmc.save(update_fields=["free_consultation_quota"])
        self.client.force_authenticate(self.patient_user)
        before = self.financial_state()
        for centre in (self.tmc, self.other_tmc):
            for amount in ("0.00", "1.00", "100.00"):
                with self.subTest(centre=centre.pk, amount=amount):
                    response = self.client.post(reverse("book-consultation"), {
                        "doctor_id": self.doctor.pk, "consultation_type": "TMC", "tmc_id": centre.pk,
                        "amount": amount, "is_tmc_operator": True, "is_staff": True,
                    }, format="json")
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(self.financial_state(), before)

    def test_direct_booking_cannot_attach_tmc_wallet(self):
        self.client.force_authenticate(self.patient_user)
        before = self.financial_state()
        response = self.client.post(reverse("book-consultation"), {
            "doctor_id": self.doctor.pk, "consultation_type": "DIRECT", "tmc_id": self.other_tmc.pk,
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.financial_state(), before)

    def test_direct_patient_can_still_use_own_wallet(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.post(reverse("book-consultation"), {"doctor_id": self.doctor.pk}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        consultation = Consultation.objects.get(pk=response.data["consultation_id"])
        self.assertIsNone(consultation.tmc_id)
        self.assertEqual(str(PatientWallet.objects.get(patient=self.patient).balance), "400.00")
        self.assertEqual(list(TMCAccount.objects.values_list("balance", flat=True)), [500, 500])

    def test_operator_cannot_spoof_other_wallet_id(self):
        self.client.force_authenticate(self.operator)
        before = self.financial_state()
        response = self.client.post(reverse("tmc-book-consultation"), {
            "doctor_id": self.doctor.pk, "patient_id": self.patient.pk, "tmc_id": self.other_tmc.pk,
        }, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.financial_state(), before)

    def test_operator_cannot_book_other_centres_patient(self):
        self.client.force_authenticate(self.operator)
        before = self.financial_state()
        response = self.client.post(reverse("tmc-book-consultation"), {
            "doctor_id": self.doctor.pk, "patient_id": self.other_patient.pk,
        }, format="json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.financial_state(), before)

    def test_owner_booking_debits_only_own_wallet_once(self):
        self.client.force_authenticate(self.operator)
        response = self.client.post(reverse("tmc-book-consultation"), {
            "doctor_id": self.doctor.pk, "patient_id": self.patient.pk, "tmc_id": self.tmc.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        consultation = Consultation.objects.get(pk=response.data["consultation_id"])
        self.assertEqual(consultation.tmc_id, self.tmc.pk)
        self.assertEqual(str(TMCAccount.objects.get(tmc=self.tmc).balance), "400.00")
        self.assertEqual(str(TMCAccount.objects.get(tmc=self.other_tmc).balance), "500.00")
        self.assertEqual(TMCAccountEntry.objects.filter(consultation=consultation).count(), 1)

    def test_stale_profile_without_operator_role_cannot_access_wallet(self):
        self.operator.is_tmc_operator = False
        self.operator.save(update_fields=["is_tmc_operator"])
        self.client.force_authenticate(self.operator)
        before = self.financial_state()
        self.assertEqual(self.client.get(reverse("tmc-finance-summary")).status_code, 403)
        self.assertEqual(self.client.post(reverse("tmc-book-consultation"), {
            "doctor_id": self.doctor.pk, "patient_id": self.patient.pk,
        }, format="json").status_code, 403)
        self.assertEqual(self.financial_state(), before)

    def test_foreign_recharge_actions_are_scoped_and_never_reach_services(self):
        recharge = TMCRechargeRequest.objects.create(tmc=self.other_tmc, amount="100.00", requested_by=self.other_operator)
        before = self.financial_state()
        actions = [
            ("tmc-razorpay-order", "create_tmc_recharge_order_reference"),
            ("tmc-razorpay-verify", "mark_tmc_recharge_success"),
            ("tmc-recharge-cancel", "cancel_tmc_recharge_request"),
        ]
        for actor, expected in ((self.operator, 404), (self.patient_user, 403)):
            self.client.force_authenticate(actor)
            for route, service in actions:
                with self.subTest(actor=actor.pk, route=route), patch("consultations.views." + service) as mocked:
                    response = self.client.post(reverse(route, args=[recharge.pk]), {
                        "tmc_id": self.other_tmc.pk, "razorpay_payment_id": "fake", "razorpay_signature": "fake",
                    }, format="json")
                    self.assertEqual(response.status_code, expected)
                    mocked.assert_not_called()
                    self.assertEqual(self.financial_state(), before)

    def test_nonstaff_operator_cannot_approve_or_topup_wallet(self):
        recharge = TMCRechargeRequest.objects.create(tmc=self.tmc, amount="100.00", requested_by=self.operator)
        self.client.force_authenticate(self.operator)
        before = self.financial_state()
        self.assertEqual(self.client.post(reverse("staff-tmc-wallet-topup"), {
            "tmc_profile_id": self.other_tmc.pk, "amount": "999.00", "is_staff": True,
        }, format="json").status_code, 403)
        self.assertEqual(self.client.post(reverse("staff-tmc-recharge-process", args=[recharge.pk]), {
            "approve": True, "is_staff": True,
        }, format="json").status_code, 403)
        self.assertEqual(self.financial_state(), before)

    def test_patient_and_other_tmc_cannot_trigger_paid_followup(self):
        consultation = self.completed_tmc_consultation()
        before = self.financial_state()
        with patch("consultations.views._followup_window_status", return_value={"is_free": False, "free_remaining": 0}):
            for actor in (self.patient_user, self.other_operator):
                self.client.force_authenticate(actor)
                response = self.client.post(reverse("patient-followup-request", args=[consultation.pk]), {}, format="json")
                self.assertEqual(response.status_code, 403)
                self.assertEqual(self.financial_state(), before)

    def test_owning_operator_can_authorise_paid_followup(self):
        consultation = self.completed_tmc_consultation()
        self.client.force_authenticate(self.operator)
        with patch("consultations.views._followup_window_status", return_value={"is_free": False, "free_remaining": 0}):
            response = self.client.post(reverse("patient-followup-request", args=[consultation.pk]), {}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(str(TMCAccount.objects.get(tmc=self.tmc).balance), "400.00")
        self.assertEqual(str(TMCAccount.objects.get(tmc=self.other_tmc).balance), "500.00")
        self.assertEqual(consultation.follow_up_sessions.get().requested_by_id, self.operator.pk)

    def test_patient_free_followup_does_not_spend_tmc_wallet(self):
        consultation = self.completed_tmc_consultation()
        self.client.force_authenticate(self.patient_user)
        before = list(TMCAccount.objects.order_by("pk").values())
        response = self.client.post(reverse("patient-followup-request", args=[consultation.pk]), {}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertFalse(response.data["is_billable"])
        self.assertEqual(list(TMCAccount.objects.order_by("pk").values()), before)

    def test_zero_charge_followup_does_not_require_wallet_spending_permission(self):
        consultation = self.completed_tmc_consultation()
        ConsultationFeeSetting.objects.update(tmc_consultation_fee="0.00")
        self.client.force_authenticate(self.patient_user)
        before = list(TMCAccount.objects.order_by("pk").values())
        with patch("consultations.views._followup_window_status", return_value={"is_free": False, "free_remaining": 0}):
            response = self.client.post(reverse("patient-followup-request", args=[consultation.pk]), {}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["amount_charged"], "0.00")
        self.assertEqual(list(TMCAccount.objects.order_by("pk").values()), before)

    def test_tmc_consultation_payment_actions_require_owner_not_patient(self):
        consultation = self.completed_tmc_consultation()
        payment = Payment.objects.create(consultation=consultation, amount="100.00", paid_by_tmc=True)
        before = self.financial_state()
        for actor in (self.patient_user, self.other_operator, self.doctor_user):
            self.client.force_authenticate(actor)
            for route, service in (("razorpay-order", "create_razorpay_order_reference"),
                                   ("razorpay-verify", "mark_razorpay_payment_success")):
                with self.subTest(actor=actor.pk, route=route), patch("consultations.views." + service) as mocked:
                    response = self.client.post(reverse(route, args=[payment.pk]), {
                        "razorpay_payment_id": "fake", "razorpay_signature": "fake",
                    }, format="json")
                    self.assertEqual(response.status_code, 403)
                    mocked.assert_not_called()
                    self.assertEqual(self.financial_state(), before)

    def test_tmc_owner_payment_action_reaches_own_payment_service(self):
        consultation = self.completed_tmc_consultation()
        payment = Payment.objects.create(consultation=consultation, amount="100.00", paid_by_tmc=True)
        payment.gateway_order_id = "order_test_owner"
        self.client.force_authenticate(self.operator)
        with patch("consultations.views.create_razorpay_order_reference", return_value=payment) as mocked:
            response = self.client.post(reverse("razorpay-order", args=[payment.pk]), {}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(mocked.call_args.args[0].pk, payment.pk)
