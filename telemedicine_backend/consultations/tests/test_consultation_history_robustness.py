"""Regression tests: GET /consultations/history/ must not 500 on legacy/edge rows."""
from unittest.mock import patch

from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import User, DoctorProfile, PatientProfile, TMCProfile
from consultations.models import (
    Consultation,
    ConsultationChat,
    ConsultationFinance,
    Payment,
)
from consultations.serializers import ConsultationHistorySerializer


@override_settings(
    CLOUDFLARE_ACCOUNT_ID="",
    CLOUDFLARE_API_TOKEN="",
    CLOUDFLARE_CALLS_APP_ID="",
    CLOUDFLARE_REALTIMEKIT_ENABLED=False,
)
class ConsultationHistoryRobustnessTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()
        self.doctor_user = User.objects.create_user(
            email="doc-hist@test.com",
            password="testpass123",
            is_doctor=True,
            first_name="Doc",
            last_name="Tor",
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            profile_completed=True,
            admin_verified=True,
            is_approved=True,
        )
        self.patient_user = User.objects.create_user(
            email="patient-hist@test.com",
            password="testpass123",
            is_patient=True,
            first_name="Pat",
            last_name="Ient",
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        self.tmc_user = User.objects.create_user(
            email="tmc-hist@test.com",
            password="testpass123",
            is_tmc_operator=True,
            first_name="Tmc",
            last_name="Op",
        )
        self.tmc = TMCProfile.objects.create(user=self.tmc_user, free_consultation_quota=5)

    def _mk_consultation(self, *, with_tmc=False, status=None, is_free=False):
        return Consultation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            tmc=self.tmc if with_tmc else None,
            consultation_type=(
                Consultation.ConsultationType.TMC
                if with_tmc
                else Consultation.ConsultationType.DIRECT
            ),
            scheduled_time=timezone.now(),
            status=status or Consultation.StatusChoices.COMPLETED,
            is_completed=True,
            is_free=is_free,
        )

    def test_history_200_no_chats_no_payment_no_finance_patient(self):
        self._mk_consultation()
        self.client.force_authenticate(self.patient_user)
        response = self.client.get("/consultations/history/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertIsNone(row.get("latest_chat_message"))
        self.assertEqual(row.get("unread_from_peer"), 0)
        self.assertEqual(row.get("amount_charged"), "0.00")
        self.assertIn(row.get("billing_type"), ("FREE", "PAID"))

    def test_history_200_attachment_only_chat(self):
        consultation = self._mk_consultation()
        ConsultationChat.objects.create(
            consultation=consultation,
            sender=self.doctor_user,
            message=None,
            is_read=False,
        )
        ConsultationChat.objects.create(
            consultation=consultation,
            sender=self.patient_user,
            message="",
            is_read=False,
        )
        self.client.force_authenticate(self.patient_user)
        response = self.client.get("/consultations/history/")
        self.assertEqual(response.status_code, 200)
        row = response.data[0]
        self.assertIsNotNone(row["latest_chat_message"])
        self.assertEqual(row["latest_chat_message"]["message"], "[Attachment]")
        self.assertEqual(row["latest_chat_message"]["sender_role"], "patient")
        self.assertGreaterEqual(row["unread_from_peer"], 0)

    def test_history_200_with_finance_and_without_payment(self):
        consultation = self._mk_consultation()
        ConsultationFinance.objects.create(
            consultation=consultation,
            source_type=ConsultationFinance.SourceType.DIRECT_PATIENT,
            billing_type=ConsultationFinance.BillingType.PAID,
            payer_entity=ConsultationFinance.PayerEntity.PATIENT,
            payment_status=ConsultationFinance.PaymentStatus.SUCCESS,
            amount_charged="150.00",
            doctor_fee="120.00",
            platform_fee="30.00",
        )
        self.assertFalse(Payment.objects.filter(consultation=consultation).exists())
        self.client.force_authenticate(self.doctor_user)
        response = self.client.get("/consultations/history/")
        self.assertEqual(response.status_code, 200)
        row = response.data[0]
        self.assertEqual(row["amount_charged"], "150.00")
        self.assertEqual(row["doctor_fee"], "120.00")
        self.assertEqual(row["platform_fee"], "30.00")
        self.assertEqual(row["billing_type"], ConsultationFinance.BillingType.PAID)

    def test_history_200_tmc_consultation_for_all_viewers(self):
        consultation = self._mk_consultation(with_tmc=True, is_free=True)
        ConsultationChat.objects.create(
            consultation=consultation,
            sender=self.doctor_user,
            message="TMC chat hello",
            is_read=False,
        )
        for user in (self.patient_user, self.doctor_user, self.tmc_user):
            self.client.force_authenticate(user)
            response = self.client.get("/consultations/history/")
            self.assertEqual(response.status_code, 200, msg=f"viewer={user.email}")
            self.assertIsInstance(response.data, list)
            self.assertEqual(len(response.data), 1, msg=f"viewer={user.email}")
            row = response.data[0]
            self.assertEqual(row["latest_chat_message"]["message"], "TMC chat hello")
            self.assertEqual(row["tmc_name"], self.tmc_user.get_full_name() or self.tmc_user.email)

    def test_history_200_legacy_completed_direct_mix(self):
        """Older-style completed rows: no finance/payment, mixed chat shapes."""
        bare = self._mk_consultation(status=Consultation.StatusChoices.COMPLETED)
        with_chat = self._mk_consultation(status=Consultation.StatusChoices.CANCELED)
        ConsultationChat.objects.create(
            consultation=with_chat,
            sender=self.doctor_user,
            message="PRESCRIPTION_RX:legacy",
            is_read=True,
        )
        attachment = self._mk_consultation(status=Consultation.StatusChoices.REJECTED)
        ConsultationChat.objects.create(
            consultation=attachment,
            sender=self.patient_user,
            message="   ",
            is_read=False,
        )
        self.client.force_authenticate(self.patient_user)
        response = self.client.get("/consultations/history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        messages = {
            (row["id"], (row["latest_chat_message"] or {}).get("message"))
            for row in response.data
        }
        self.assertIn((bare.id, None), messages)
        self.assertIn((with_chat.id, "Prescription shared"), messages)
        self.assertIn((attachment.id, "[Attachment]"), messages)

    def test_history_skips_row_when_serializer_raises(self):
        good = self._mk_consultation()
        bad = self._mk_consultation()
        ConsultationChat.objects.create(
            consultation=good,
            sender=self.doctor_user,
            message="still visible",
            is_read=False,
        )

        original = ConsultationHistorySerializer.to_representation

        def flaky(self, instance):
            if instance.id == bad.id:
                raise RuntimeError("simulated legacy serialize failure")
            return original(self, instance)

        self.client.force_authenticate(self.patient_user)
        with patch.object(ConsultationHistorySerializer, "to_representation", flaky):
            response = self.client.get("/consultations/history/")
        self.assertEqual(response.status_code, 200)
        ids = {row["id"] for row in response.data}
        self.assertIn(good.id, ids)
        self.assertNotIn(bad.id, ids)

    def test_serializer_chat_helpers_swallow_unexpected_errors(self):
        consultation = self._mk_consultation()
        ConsultationChat.objects.create(
            consultation=consultation,
            sender=self.doctor_user,
            message="should not surface on boom",
            is_read=False,
        )
        request = type("R", (), {"user": self.patient_user})()
        serializer = ConsultationHistorySerializer(consultation, context={"request": request})

        with patch.object(
            ConsultationHistorySerializer,
            "_peer_user_ids",
            side_effect=RuntimeError("peer boom"),
        ):
            self.assertEqual(serializer.get_unread_from_peer(consultation), 0)

        # Force a failure after the chat row is loaded (same path as bad sender/legacy data).
        with patch.object(
            ConsultationHistorySerializer,
            "_chat_preview_text",
            side_effect=RuntimeError("preview boom"),
        ):
            self.assertIsNone(serializer.get_latest_chat_message(consultation))
