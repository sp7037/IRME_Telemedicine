"""Narrow tests for consultation-flow UX backend helpers (video errors, chat signals)."""
from unittest.mock import MagicMock

from django.test import SimpleTestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import User, DoctorProfile, PatientProfile
from consultations.models import Consultation, ConsultationChat, ConsultationVideoSession
from consultations.video import (
    VIDEO_UNAVAILABLE_CLIENT_MESSAGE,
    VideoProviderError,
    _configuration_error_message,
    client_video_error_payload,
)
from consultations.serializers import ConsultationHistorySerializer


class VideoClientErrorPayloadTests(SimpleTestCase):
    def test_configuration_error_hides_env_var_names(self):
        message = _configuration_error_message("cloudflare")
        self.assertEqual(message, VIDEO_UNAVAILABLE_CLIENT_MESSAGE)
        self.assertNotIn("CLOUDFLARE_", message)

    def test_client_payload_omits_config_for_participants(self):
        patient = MagicMock(is_staff=False)
        payload = client_video_error_payload(
            VideoProviderError("cloudflare video is not configured. Missing or invalid: CLOUDFLARE_ACCOUNT_ID."),
            patient,
        )
        self.assertEqual(payload["error"], VIDEO_UNAVAILABLE_CLIENT_MESSAGE)
        self.assertNotIn("config", payload)
        self.assertNotIn("CLOUDFLARE_", payload["error"])

    def test_client_payload_includes_config_for_staff(self):
        staff = MagicMock(is_staff=True)
        payload = client_video_error_payload(
            VideoProviderError(VIDEO_UNAVAILABLE_CLIENT_MESSAGE),
            staff,
        )
        self.assertEqual(payload["error"], VIDEO_UNAVAILABLE_CLIENT_MESSAGE)
        self.assertIn("config", payload)


@override_settings(
    CLOUDFLARE_ACCOUNT_ID="",
    CLOUDFLARE_API_TOKEN="",
    CLOUDFLARE_CALLS_APP_ID="",
    CLOUDFLARE_REALTIMEKIT_ENABLED=False,
)
class ConsultationChatSignalTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()
        self.doctor_user = User.objects.create_user(
            email="doc-flow-ux@test.com", password="testpass123", is_doctor=True, first_name="Asha", last_name="Mehta"
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            profile_completed=True,
            admin_verified=True,
            is_approved=True,
        )
        self.patient_user = User.objects.create_user(
            email="patient-flow-ux@test.com", password="testpass123", is_patient=True, first_name="Ravi", last_name="Shah"
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        self.consultation = Consultation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            consultation_type=Consultation.ConsultationType.DIRECT,
            scheduled_time=timezone.now(),
            status=Consultation.StatusChoices.IN_PROGRESS,
        )

    def test_history_exposes_latest_message_and_unread_for_patient(self):
        ConsultationChat.objects.create(
            consultation=self.consultation,
            sender=self.doctor_user,
            message="Please share your symptoms.",
            is_read=False,
        )
        request = MagicMock(user=self.patient_user)
        data = ConsultationHistorySerializer(self.consultation, context={"request": request}).data
        self.assertIsNotNone(data["latest_chat_message"])
        self.assertEqual(data["latest_chat_message"]["sender_role"], "doctor")
        self.assertIn("symptoms", data["latest_chat_message"]["message"])
        self.assertEqual(data["unread_from_peer"], 1)

    def test_chat_history_marks_peer_messages_read(self):
        chat = ConsultationChat.objects.create(
            consultation=self.consultation,
            sender=self.doctor_user,
            message="Hello from doctor",
            is_read=False,
        )
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(f"/consultations/chat-history/{self.consultation.id}/")
        self.assertEqual(response.status_code, 200)
        chat.refresh_from_db()
        self.assertTrue(chat.is_read)

    def test_video_join_returns_friendly_unavailable_message(self):
        ConsultationVideoSession.objects.create(
            consultation=self.consultation,
            provider=ConsultationVideoSession.Provider.CLOUDFLARE,
            status=ConsultationVideoSession.Status.ACCEPTED,
            created_by=self.doctor_user,
            responded_by=self.patient_user,
        )
        self.client.force_authenticate(self.patient_user)
        response = self.client.post(f"/consultations/video/join/{self.consultation.id}/")
        # Without provider credentials join must fail safely for participants
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), VIDEO_UNAVAILABLE_CLIENT_MESSAGE)
        self.assertNotIn("CLOUDFLARE_", str(response.data))
        self.assertNotIn("config", response.data)
