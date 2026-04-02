from django.test import TransactionTestCase
from rest_framework.test import APIClient

from users.models import User, DoctorProfile, PatientProfile
from consultations.models import Consultation, ConsultationEvent


class ConsultationTransitionTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()
        self.doctor_user = User.objects.create_user(
            email="doc-queue@test.com", password="testpass123", is_doctor=True
        )
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, profile_completed=True)

        self.patient_user = User.objects.create_user(
            email="patient-queue@test.com", password="testpass123", is_patient=True
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user)

        self.patient2_user = User.objects.create_user(
            email="patient-queue2@test.com", password="testpass123", is_patient=True
        )
        self.patient2 = PatientProfile.objects.create(user=self.patient2_user)

    def _mk_consultation(self, patient):
        c = Consultation.objects.create(
            patient=patient,
            doctor=self.doctor,
            consultation_type=Consultation.ConsultationType.DIRECT,
            scheduled_time="2026-01-01T10:00:00Z",
            status=Consultation.StatusChoices.PENDING,
        )
        ConsultationEvent.objects.create(
            consultation=c,
            event_type=ConsultationEvent.EventType.REQUESTED,
            actor=patient.user,
            to_status=Consultation.StatusChoices.PENDING,
        )
        return c

    def test_accept_starts_when_no_active_or_queue(self):
        c = self._mk_consultation(self.patient)
        self.client.force_authenticate(self.doctor_user)
        response = self.client.patch(f"/consultations/doctor-response/{c.id}/", {"status": "ACCEPTED"}, format="json")
        self.assertEqual(response.status_code, 200)
        c.refresh_from_db()
        self.assertEqual(c.status, Consultation.StatusChoices.IN_PROGRESS)

    def test_accept_queues_when_active_exists(self):
        active = self._mk_consultation(self.patient)
        active.status = Consultation.StatusChoices.IN_PROGRESS
        active.save(update_fields=["status"])

        queued_candidate = self._mk_consultation(self.patient2)
        self.client.force_authenticate(self.doctor_user)
        response = self.client.patch(
            f"/consultations/doctor-response/{queued_candidate.id}/",
            {"status": "ACCEPTED"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        queued_candidate.refresh_from_db()
        self.assertEqual(queued_candidate.status, Consultation.StatusChoices.QUEUED)
        self.assertEqual(queued_candidate.queue_number, 1)
