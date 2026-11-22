from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.db import connections
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from users.models import User, DoctorProfile, PatientProfile, TMCProfile
from consultations.models import (
    Consultation, ConsultationEvent, ConsultationFinance, Payment, DoctorEarning,
    ConsultationFeeSetting, PatientWallet, PatientWalletEntry, TMCAccount, TMCAccountEntry,
    AdminPlatformAccount, AdminPlatformEntry,
)
from consultations.finance import patient_wallet_topup, tmc_account_topup, mark_razorpay_payment_success
from consultations.wallet_returns import record_historical_rejection_review


class ReturnFixtures:
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="patient@return.test", password="x", is_patient=True)
        self.patient = PatientProfile.objects.create(user=self.user)
        self.doctor_user = User.objects.create_user(email="doctor@return.test", password="x", is_doctor=True, is_email_verified=True)
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, consultation_fee="100.00",
            max_daily_consultations=20, profile_completed=True, admin_verified=True, is_approved=True)
        ConsultationFeeSetting.objects.create(platform_fee_percentage="20.00", direct_patient_fee="100.00", tmc_consultation_fee="100.00")
        patient_wallet_topup(self.patient, "200.00")

    def book(self):
        # Separate repeated scenarios from the existing same-doctor cooldown.
        Consultation.objects.filter(patient=self.patient, status__in=["REJECTED", "REJECTED_BY_PATIENT", "CANCELED"]).update(
            created_at=timezone.now() - timezone.timedelta(minutes=20))
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("book-consultation"), {"doctor_id": self.doctor.pk}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return Consultation.objects.get(pk=response.data["consultation_id"])

    def postpone(self, consultation):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.patch(reverse("doctor-response", args=[consultation.pk]), {
            "status": "POSTPONED", "new_suggested_time": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
        }, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.client.force_authenticate(self.user)

    def respond(self, consultation, action="reject_postponed"):
        return self.client.patch(reverse("patient-response", args=[consultation.pk]), {"action": action}, format="json")


class PrestartWalletReturnTests(ReturnFixtures, APITestCase):
    def test_operator_review_of_historical_rejection_is_linked_once_and_retains_original_decision(self):
        consultation = self.book(); self.postpone(consultation)
        Consultation.objects.filter(pk=consultation.pk).update(status="REJECTED_BY_PATIENT")
        original = ConsultationEvent.objects.create(consultation=consultation, event_type="POSTPONE_REJECTED",
            from_status="POSTPONED", to_status="REJECTED_BY_PATIENT", actor=self.user, note="Original decision")
        first = record_historical_rejection_review(consultation.pk)
        second = record_historical_rejection_review(consultation.pk)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "RETURNED")
        self.assertEqual(PatientWalletEntry.objects.filter(entry_type="REFUND").count(), 1)
        original.refresh_from_db(); self.assertEqual(original.note, "Original decision")
        review = consultation.events.get(metadata__financial_reconciliation=True)
        self.assertEqual(review.metadata["original_decision_event_id"], original.pk)
        self.assertIsNone(review.actor_id)

    def test_postponement_rejection_returns_full_charge_once_and_reverses_platform_fee(self):
        consultation = self.book(); self.postpone(consultation)
        debit = PatientWalletEntry.objects.get(consultation=consultation, entry_type="DEBIT")
        response = self.respond(consultation)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["wallet_return"]["status"], "RETURNED")
        self.assertEqual(response.data["data"]["wallet_return"]["amount"], "120.00")
        self.assertEqual(PatientWallet.objects.get(patient=self.patient).balance, 200)
        refund = PatientWalletEntry.objects.get(consultation=consultation, entry_type="REFUND")
        self.assertEqual(refund.amount, debit.amount)
        self.assertIn(f"#{debit.pk}", refund.description)
        self.assertEqual(AdminPlatformAccount.objects.get().balance, 0)
        self.assertEqual(AdminPlatformEntry.objects.filter(consultation=consultation, entry_type="ADJUSTMENT").count(), 1)
        self.assertEqual(ConsultationFinance.objects.get(consultation=consultation).payment_status, "REFUNDED")
        self.assertEqual(Payment.objects.get(consultation=consultation).status, "PAID")
        self.assertFalse(DoctorEarning.objects.exists())
        self.assertEqual(self.respond(consultation).status_code, 200)
        self.assertEqual(PatientWalletEntry.objects.filter(entry_type="REFUND").count(), 1)
        self.assertEqual(consultation.events.filter(event_type="POSTPONE_REJECTED").count(), 1)

    def test_accepting_postponement_preserves_charge_and_no_second_debit(self):
        consultation = self.book(); self.postpone(consultation)
        response = self.respond(consultation, "approve_postponed")
        self.assertEqual(response.status_code, 200)
        consultation.refresh_from_db(); self.assertEqual(consultation.status, "PENDING")
        self.assertEqual(PatientWallet.objects.get(patient=self.patient).balance, 80)
        self.assertEqual(PatientWalletEntry.objects.filter(entry_type="DEBIT").count(), 1)
        self.assertFalse(PatientWalletEntry.objects.filter(entry_type="REFUND").exists())

    def test_return_uses_original_charge_after_current_fees_change_and_blocks_late_provider_mark_paid(self):
        consultation = self.book(); self.postpone(consultation)
        ConsultationFeeSetting.objects.update(platform_fee_percentage="50.00")
        response = self.respond(consultation)
        self.assertEqual(response.data["data"]["wallet_return"]["amount"], "120.00")
        payment = Payment.objects.get(consultation=consultation)
        with patch("consultations.finance.verify_razorpay_signature", return_value=True):
            with self.assertRaises(ValueError):
                mark_razorpay_payment_success(payment, "pay_unexpected", "signed")
        self.assertEqual(ConsultationFinance.objects.get(consultation=consultation).payment_status, "REFUNDED")
        self.assertEqual(self.client.post(reverse("razorpay-order", args=[payment.pk])).status_code, 403)

    def test_doctor_initial_rejection_and_patient_pending_cancellation_return_wallet(self):
        for action in ("doctor_reject", "cancel"):
            consultation = self.book()
            if action == "doctor_reject":
                self.client.force_authenticate(self.doctor_user)
                response = self.client.patch(reverse("doctor-response", args=[consultation.pk]), {"status": "REJECTED"}, format="json")
            else:
                response = self.respond(consultation, "cancel")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(PatientWallet.objects.get(patient=self.patient).balance, 200)
        self.assertEqual(PatientWalletEntry.objects.filter(entry_type="REFUND").count(), 2)

    def test_unrelated_patient_cannot_reject_or_receive_return(self):
        consultation = self.book(); self.postpone(consultation)
        other = User.objects.create_user(email="other@return.test", password="x", is_patient=True)
        PatientProfile.objects.create(user=other)
        self.client.force_authenticate(other)
        self.assertEqual(self.respond(consultation).status_code, 403)
        self.assertFalse(PatientWalletEntry.objects.filter(entry_type="REFUND").exists())

    def test_missing_or_conflicting_start_evidence_requires_review_without_credit(self):
        for reason in ("missing_booking", "started"):
            consultation = self.book(); self.postpone(consultation)
            if reason == "missing_booking":
                consultation.events.filter(event_type="REQUESTED").delete()
            else:
                ConsultationEvent.objects.create(consultation=consultation, event_type="STARTED")
            response = self.respond(consultation)
            self.assertEqual(response.data["data"]["wallet_return"]["status"], "REVIEW_REQUIRED")
            self.assertFalse(PatientWalletEntry.objects.filter(consultation=consultation, entry_type="REFUND").exists())
            patient_wallet_topup(self.patient, "120.00")

    def test_provider_mixed_or_existing_return_requires_review(self):
        for reason in ("provider", "previous_refund", "wrong_amount"):
            consultation = self.book(); self.postpone(consultation)
            if reason == "provider":
                Payment.objects.filter(consultation=consultation).update(provider="RAZORPAY", gateway_order_id="order_unknown")
            elif reason == "previous_refund":
                PatientWalletEntry.objects.create(wallet=PatientWallet.objects.get(patient=self.patient), consultation=consultation,
                    entry_type="REFUND", amount=1, balance_after=80)
            else:
                PatientWalletEntry.objects.filter(consultation=consultation, entry_type="DEBIT").update(amount=1)
            response = self.respond(consultation)
            self.assertEqual(response.data["data"]["wallet_return"]["status"], "REVIEW_REQUIRED")
            patient_wallet_topup(self.patient, "120.00")

    def test_platform_evidence_missing_requires_review_without_partial_credit(self):
        consultation = self.book(); self.postpone(consultation)
        AdminPlatformEntry.objects.filter(consultation=consultation).delete()
        response = self.respond(consultation)
        self.assertEqual(response.data["data"]["wallet_return"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(PatientWallet.objects.get(patient=self.patient).balance, 80)

    def test_failure_after_wallet_credit_rolls_back_status_credit_and_reversal(self):
        consultation = self.book(); self.postpone(consultation)
        with patch("consultations.wallet_returns.AdminPlatformEntry.objects.create", side_effect=RuntimeError("test posting failure")):
            with self.assertRaises(RuntimeError): self.respond(consultation)
        consultation.refresh_from_db(); self.assertEqual(consultation.status, "POSTPONED")
        self.assertEqual(PatientWallet.objects.get(patient=self.patient).balance, 80)
        self.assertFalse(PatientWalletEntry.objects.filter(entry_type="REFUND").exists())
        self.assertEqual(AdminPlatformAccount.objects.get().balance, 20)

    def test_tmc_discounted_charge_returns_only_original_tmc_debit_even_below_threshold(self):
        operator = User.objects.create_user(email="tmc@return.test", password="x", is_tmc_operator=True)
        tmc = TMCProfile.objects.create(user=operator, discount_percentage=30, discounted_consultation_quota=10)
        self.patient.created_by_tmc = tmc; self.patient.save(update_fields=["created_by_tmc"])
        tmc_account_topup(tmc, "100.00")
        self.client.force_authenticate(operator)
        response = self.client.post(reverse("tmc-book-consultation"), {"patient_id": self.patient.pk, "doctor_id": self.doctor.pk}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        consultation = Consultation.objects.get(patient=self.patient)
        original_charge = consultation.finance.amount_charged
        self.postpone(consultation)
        response = self.respond(consultation)
        self.assertEqual(response.data["data"]["wallet_return"]["destination"], "TMC wallet")
        self.assertEqual(TMCAccount.objects.get(tmc=tmc).balance, 100)
        self.assertEqual(TMCAccountEntry.objects.get(entry_type="REFUND").amount, original_charge)
        self.assertEqual(PatientWallet.objects.get(patient=self.patient).balance, 200)
        tmc.refresh_from_db(); self.assertEqual(tmc.discounted_consultations_used, 1)

    def test_free_legacy_tmc_case_does_not_fabricate_cash_or_restore_unknown_month(self):
        operator = User.objects.create_user(email="free-tmc@return.test", password="x", is_tmc_operator=True)
        tmc = TMCProfile.objects.create(user=operator, free_consultation_quota=1)
        self.patient.created_by_tmc = tmc; self.patient.save(update_fields=["created_by_tmc"])
        self.client.force_authenticate(operator)
        response = self.client.post(reverse("tmc-book-consultation"), {"patient_id": self.patient.pk, "doctor_id": self.doctor.pk}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        consultation = Consultation.objects.get(patient=self.patient)
        self.postpone(consultation)
        response = self.respond(consultation)
        self.assertEqual(response.data["data"]["wallet_return"]["status"], "REVIEW_REQUIRED")
        self.assertFalse(TMCAccountEntry.objects.filter(entry_type="REFUND").exists())
        tmc.refresh_from_db(); self.assertEqual(tmc.free_consultations_used, 1)


class ConcurrentRejectionTests(ReturnFixtures, TransactionTestCase):
    def test_two_rejections_have_one_wallet_return(self):
        consultation = self.book(); self.postpone(consultation)
        barrier = Barrier(2)
        def reject():
            try:
                client = APIClient(); client.force_authenticate(User.objects.get(pk=self.user.pk))
                barrier.wait(timeout=10)
                return client.patch(reverse("patient-response", args=[consultation.pk]), {"action": "reject_postponed"}, format="json").status_code
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(reject) for _ in range(2)]
            statuses = [future.result(timeout=20) for future in futures]
        self.assertEqual(statuses, [200, 200])
        self.assertEqual(PatientWalletEntry.objects.filter(entry_type="REFUND").count(), 1)
        self.assertEqual(PatientWallet.objects.get(patient=self.patient).balance, 200)
