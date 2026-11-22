from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import User, PatientProfile, DoctorProfile, TMCProfile
from consultations.models import (
    ConsultationFeeSetting, PatientWallet, PatientWalletEntry, TMCAccount, TMCAccountEntry,
    Consultation, Payment, ConsultationFinance, DoctorAvailability,
)
from consultations.finance import patient_wallet_topup, create_consultation_finance


class PatientPaymentPreviewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="patient@preview.test", password="testpass", is_patient=True)
        self.patient = PatientProfile.objects.create(user=self.user)
        doctor_user = User.objects.create_user(email="doctor@preview.test", password="testpass", is_doctor=True, is_email_verified=True)
        self.doctor = DoctorProfile.objects.create(user=doctor_user, consultation_fee="100.00",
            profile_completed=True, admin_verified=True, is_approved=True)
        DoctorAvailability.objects.update_or_create(doctor=self.doctor, defaults={"is_available_online": True})
        self.setting = ConsultationFeeSetting.objects.create(direct_patient_fee="80.00", platform_fee_percentage="20.00")
        self.client.force_authenticate(self.user)

    def preview(self, **extra):
        return self.client.get(reverse("direct-booking-preview"), {"doctor_id": self.doctor.pk, **extra})

    def test_preview_matches_reported_100_balance_120_total_and_has_no_side_effects(self):
        patient_wallet_topup(self.patient, "100.00")
        response = self.preview()
        self.assertEqual(response.status_code, 200)
        for key, value in {"base_fee": "100.00", "platform_fee": "20.00", "total": "120.00",
                           "balance": "100.00", "shortfall": "20.00", "can_request": False, "price_reserved": False}.items():
            self.assertEqual(response.data[key], value)
        self.assertEqual(PatientWalletEntry.objects.count(), 1)
        self.assertFalse(Consultation.objects.exists())
        self.assertFalse(Payment.objects.exists())

    def test_missing_wallet_and_settings_are_not_created_by_preview(self):
        self.assertEqual(self.preview().data["balance"], "0.00")
        self.assertFalse(PatientWallet.objects.exists())
        self.setting.delete()
        self.assertEqual(self.preview().status_code, 409)
        self.assertFalse(ConsultationFeeSetting.objects.exists())

    def test_preview_uses_own_balance_and_server_prices_ignoring_foreign_ids_and_amounts(self):
        other_user = User.objects.create_user(email="other@preview.test", password="x", is_patient=True)
        other = PatientProfile.objects.create(user=other_user)
        patient_wallet_topup(other, "999.00")
        response = self.preview(patient_id=other.pk, amount="0", platform_fee="0")
        self.assertEqual(response.data["balance"], "0.00")
        self.assertEqual(response.data["total"], "120.00")
        self.client.force_authenticate(self.doctor.user)
        self.assertEqual(self.preview().status_code, 403)
        self.client.force_authenticate(None)
        self.assertIn(self.preview().status_code, (401, 403))

    def test_global_fee_fallback_zero_platform_and_malformed_doctor(self):
        self.doctor.consultation_fee = 0; self.doctor.save(update_fields=["consultation_fee"])
        self.setting.platform_fee_percentage = 0; self.setting.save(update_fields=["platform_fee_percentage"])
        self.assertEqual(self.preview().data["total"], "80.00")
        self.assertEqual(self.preview(doctor_id="invalid").status_code, 400)
        self.doctor.is_approved = False; self.doctor.save(update_fields=["is_approved"])
        self.assertEqual(self.preview().status_code, 404)

    def test_confirmed_current_total_books_and_debits_server_charge(self):
        patient_wallet_topup(self.patient, "120.00")
        response = self.client.post(reverse("book-consultation"), {
            "doctor_id": self.doctor.pk, "consultation_type": "DIRECT", "expected_total": "120.00", "amount": "1.00",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(PatientWallet.objects.get(patient=self.patient).balance, 0)
        self.assertEqual(Payment.objects.get().amount, 120)

    def test_changed_total_rejects_before_booking_without_debit(self):
        patient_wallet_topup(self.patient, "200.00")
        response = self.client.post(reverse("book-consultation"), {
            "doctor_id": self.doctor.pk, "expected_total": "100.00",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("expected_total", response.data)
        self.assertFalse(Consultation.objects.exists())
        self.assertEqual(PatientWalletEntry.objects.count(), 1)

    def test_price_change_during_creation_rolls_back_financial_postings(self):
        patient_wallet_topup(self.patient, "200.00")
        def changed_pricing(**kwargs):
            ConsultationFeeSetting.objects.filter(pk=self.setting.pk).update(platform_fee_percentage="30.00")
            return create_consultation_finance(**kwargs)
        with patch("consultations.serializers.create_consultation_finance", side_effect=changed_pricing):
            response = self.client.post(reverse("book-consultation"), {
                "doctor_id": self.doctor.pk, "expected_total": "120.00",
            }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Consultation.objects.exists())
        self.assertFalse(Payment.objects.exists())
        self.assertFalse(ConsultationFinance.objects.exists())
        self.assertEqual(PatientWallet.objects.get(patient=self.patient).balance, 200)
        self.assertEqual(PatientWalletEntry.objects.count(), 1)


@override_settings(DEBUG=True)
class LocalTestCreditTests(APITestCase):
    def setUp(self):
        self.actor = User.objects.create_user(email="staff@test-credit.test", password="x", is_staff=True)
        self.actor.user_permissions.add(*Permission.objects.filter(content_type__app_label="consultations",
            codename__in=["change_patientwallet", "change_tmcaccount"]))
        self.patient = PatientProfile.objects.create(user=User.objects.create_user(email="patient@test-credit.test", password="x", is_patient=True))
        self.tmc = TMCProfile.objects.create(user=User.objects.create_user(email="tmc@test-credit.test", password="x", is_tmc_operator=True))

    def credit(self, **kwargs):
        options = {"patient_id": self.patient.pk, "amount": "20.00", "actor_email": self.actor.email,
                   "confirm_local": True, "stdout": StringIO()}
        options.update(kwargs)
        if options.get("patient_id") is None:
            options.pop("patient_id", None)
        return call_command("local_test_credit", **options)

    def test_manual_patient_and_tmc_credit_uses_ledger_and_actor_without_gateway(self):
        self.credit()
        self.credit(patient_id=None, tmc_id=self.tmc.pk)
        self.assertEqual(PatientWallet.objects.get(patient=self.patient).balance, 20)
        self.assertEqual(TMCAccount.objects.get(tmc=self.tmc).balance, 20)
        self.assertIn(f"staff #{self.actor.pk}", PatientWalletEntry.objects.get().description)
        self.assertIn("LOCAL TEST CREDIT", TMCAccountEntry.objects.get().description)
        self.assertFalse(Payment.objects.exists())

    def test_production_remote_database_and_missing_confirmation_are_rejected(self):
        with override_settings(DEBUG=False), self.assertRaises(CommandError): self.credit()
        with patch.dict(settings.DATABASES["default"], {"HOST": "remote.invalid"}), self.assertRaises(CommandError): self.credit()
        with self.assertRaises(CommandError): self.credit(confirm_local=False)
        self.assertFalse(PatientWalletEntry.objects.exists())

    def test_invalid_amount_or_unauthorised_actor_cannot_credit(self):
        for amount in ("-1", "0", "NaN", "Infinity", "1.001", "bad"):
            with self.assertRaises(CommandError): self.credit(amount=amount)
        with self.assertRaises(CommandError): self.credit(actor_email=self.patient.user.email)
        with self.assertRaises(CommandError): self.credit(patient_id=999999)
        self.assertFalse(PatientWalletEntry.objects.exists())
