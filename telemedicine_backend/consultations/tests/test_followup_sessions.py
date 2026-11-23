from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase

from consultations.finance import patient_wallet_topup, tmc_account_topup
from consultations.models import Consultation, ConsultationChat, ConsultationFollowUpSession, Prescription
from users.models import DoctorProfile, PatientProfile, TMCProfile, User


class ConsultationFollowUpSessionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.doctor_user = User.objects.create_user(
            email="followup-doctor@test.com",
            password="testpass123",
            is_doctor=True,
            first_name="Follow",
            last_name="Doctor",
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            profile_completed=True,
            admin_verified=True,
            is_approved=True,
        )
        self.patient_user = User.objects.create_user(
            email="followup-patient@test.com",
            password="testpass123",
            is_patient=True,
            first_name="Follow",
            last_name="Patient",
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        patient_wallet_topup(self.patient, "1000.00", "Test balance")
        self.tmc_user = User.objects.create_user(
            email="followup-tmc@test.com",
            password="testpass123",
            is_tmc_operator=True,
            first_name="Follow",
            last_name="TMC",
        )
        self.tmc = TMCProfile.objects.create(user=self.tmc_user)
        tmc_account_topup(self.tmc, "1000.00", "Test TMC balance")
        self.consultation = Consultation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            consultation_type=Consultation.ConsultationType.DIRECT,
            scheduled_time=timezone.now(),
            status=Consultation.StatusChoices.IN_PROGRESS,
        )
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(
            reverse("complete-consultation", kwargs={"consultation_id": self.consultation.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patient_requests_free_followup_and_doctor_resumes_same_chat(self):
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.post(
            reverse("patient-followup-request", kwargs={"consultation_id": self.consultation.id})
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["is_billable"])
        session = ConsultationFollowUpSession.objects.get(id=response.data["follow_up_session_id"])
        self.assertEqual(session.status, ConsultationFollowUpSession.Status.PENDING)

        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(
            reverse("doctor-followup-response", kwargs={"followup_id": session.id}),
            {"action": "ACCEPTED"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.consultation.refresh_from_db()
        session.refresh_from_db()
        self.assertEqual(self.consultation.status, Consultation.StatusChoices.IN_PROGRESS)
        self.assertEqual(session.status, ConsultationFollowUpSession.Status.IN_PROGRESS)

        self.client.force_authenticate(user=self.patient_user)
        response = self.client.post(
            reverse("send-message", kwargs={"consultation_id": self.consultation.id}),
            {"message": "I have a new symptom."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_assigned_tmc_requests_followup_for_completed_tmc_consultation(self):
        tmc_consultation = Consultation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            tmc=self.tmc,
            consultation_type=Consultation.ConsultationType.TMC,
            scheduled_time=timezone.now(),
            status=Consultation.StatusChoices.IN_PROGRESS,
        )
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(
            reverse("complete-consultation", kwargs={"consultation_id": tmc_consultation.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.tmc_user)
        response = self.client.post(
            reverse("patient-followup-request", kwargs={"consultation_id": tmc_consultation.id})
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = ConsultationFollowUpSession.objects.get(id=response.data["follow_up_session_id"])
        self.assertEqual(session.requested_by, self.tmc_user)
        self.assertEqual(session.status, ConsultationFollowUpSession.Status.PENDING)

    def test_followup_prescription_is_separate_from_original_prescription(self):
        self.client.force_authenticate(user=self.doctor_user)
        original = self.client.post(
            reverse("prescription", kwargs={"consultation_id": self.consultation.id}),
            {
                "medicines": [{"medicine_type": "Tab", "name": "A", "strength": "1 mg", "frequency": "OD", "duration_days": "3"}],
                "instructions": "Original prescription.",
            },
            format="json",
        )
        self.assertEqual(original.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.patient_user)
        followup = self.client.post(
            reverse("patient-followup-request", kwargs={"consultation_id": self.consultation.id})
        )
        session = ConsultationFollowUpSession.objects.get(id=followup.data["follow_up_session_id"])

        self.client.force_authenticate(user=self.doctor_user)
        self.client.post(
            reverse("doctor-followup-response", kwargs={"followup_id": session.id}),
            {"action": "ACCEPTED"},
            format="json",
        )
        new_rx = self.client.post(
            reverse("prescription", kwargs={"consultation_id": self.consultation.id}),
            {
                "medicines": [{"medicine_type": "Cap", "name": "B", "strength": "2 mg", "frequency": "BD", "duration_days": "5"}],
                "instructions": "Follow-up prescription.",
            },
            format="json",
        )
        self.assertEqual(new_rx.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Prescription.objects.filter(consultation=self.consultation).count(), 2)
        self.assertTrue(Prescription.objects.filter(consultation=self.consultation, follow_up_session=session).exists())

    def test_prescription_chat_marker_links_exact_prescription(self):
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(
            reverse("prescription", kwargs={"consultation_id": self.consultation.id}),
            {
                "medicines": [{"medicine_type": "Tab", "name": "A", "strength": "1 mg", "frequency": "OD", "duration_days": "3"}],
                "instructions": "Original prescription.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rx_id = response.data["id"]
        marker = ConsultationChat.objects.filter(consultation=self.consultation, message__startswith="PRESCRIPTION_RX:").latest("timestamp")
        self.assertIn(f"PRESCRIPTION_RX:{rx_id}:", marker.message)

        self.client.force_authenticate(user=self.patient_user)
        chat = self.client.get(reverse("chat-history", kwargs={"consultation_id": self.consultation.id}))
        self.assertEqual(chat.status_code, status.HTTP_200_OK)
        rx_messages = [m for m in chat.data["chat_history"] if m.get("is_prescription")]
        self.assertTrue(rx_messages)
        self.assertEqual(rx_messages[-1]["prescription_data"]["id"], rx_id)

    def test_video_join_blocked_after_completion_without_active_followup(self):
        """Video join should be blocked for completed consultations without an active follow-up."""
        self.consultation.status = Consultation.StatusChoices.COMPLETED
        self.consultation.is_completed = True
        self.consultation.save()

        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(
            reverse("consultation-video-join", kwargs={"consultation_id": self.consultation.id})
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Video is not available for completed consultations", response.data["error"])

    def test_video_join_allowed_with_active_followup(self):
        """Video join should be allowed for completed consultations with an active follow-up."""
        self.consultation.status = Consultation.StatusChoices.COMPLETED
        self.consultation.is_completed = True
        self.consultation.save()

        self.client.force_authenticate(user=self.patient_user)
        followup_response = self.client.post(
            reverse("patient-followup-request", kwargs={"consultation_id": self.consultation.id})
        )
        self.assertEqual(followup_response.status_code, status.HTTP_201_CREATED)
        session_id = followup_response.data["follow_up_session_id"]

        self.client.force_authenticate(user=self.doctor_user)
        accept_response = self.client.post(
            reverse("doctor-followup-response", kwargs={"followup_id": session_id}),
            {"action": "ACCEPTED"},
            format="json",
        )
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)

        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, Consultation.StatusChoices.IN_PROGRESS)
        
        active_followup = ConsultationFollowUpSession.objects.filter(
            consultation=self.consultation,
            status=ConsultationFollowUpSession.Status.IN_PROGRESS
        ).first()
        self.assertIsNotNone(active_followup)
