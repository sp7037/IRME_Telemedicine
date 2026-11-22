from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import DoctorProfile, DoctorProfileChangeRequest, User


class DoctorProfileChangeRequestTests(APITestCase):
    @staticmethod
    def profile_photo():
        buffer = BytesIO()
        Image.new("RGB", (2, 2), color="blue").save(buffer, format="PNG")
        return SimpleUploadedFile("profile-test.png", buffer.getvalue(), content_type="image/png")

    def setUp(self):
        self.doctor_user = User.objects.create_user(
            email="profile-change-doctor@test.com",
            password="testpass123",
            is_doctor=True,
            is_email_verified=True,
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            qualification="MBBS",
            degree="MBBS",
            college_university_name="Test Medical College",
            passing_year=2011,
            specialty="Dermatology",
            experience="12",
            license_number="PROFILE-CHANGE-1",
            registration_number="REG-CHANGE-1",
            state_medical_council="Delhi Medical Council",
            identity_proof="doctors/test/identity.pdf",
            registration_certificate="doctors/test/certificate.pdf",
            hospital_or_clinic_name="IRME Clinic",
            clinic_address_street="Test Street",
            city="Delhi",
            state="Delhi",
            pin_code="110001",
            consultation_modes=["VIDEO"],
            consultation_fee="500.00",
            profile_completed=True,
            admin_verified=True,
            is_approved=True,
        )

    def test_completed_profile_edits_create_pending_request_without_changing_live_profile(self):
        self.client.force_authenticate(user=self.doctor_user)

        response = self.client.patch(
            reverse("doctor-profile-completion"),
            {"specialty": "Cardiology", "consultation_fee": "750.00"},
            format="json",
        )

        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.data["change_request_created"])
        self.doctor_profile.refresh_from_db()
        self.assertEqual(self.doctor_profile.specialty, "Dermatology")
        self.assertEqual(str(self.doctor_profile.consultation_fee), "500.00")
        self.assertTrue(self.doctor_profile.has_pending_changes)

        change_request = DoctorProfileChangeRequest.objects.get(doctor=self.doctor_profile)
        self.assertEqual(change_request.status, DoctorProfileChangeRequest.Status.PENDING)
        self.assertEqual(change_request.requested_by, self.doctor_user)
        self.assertEqual(change_request.proposed_data["specialty"], "Cardiology")
        self.assertEqual(change_request.proposed_data["consultation_fee"], "750.00")
        detail = self.client.get(reverse("doctor-profile-completion"))
        self.assertEqual(detail.status_code, 200)
        pending = detail.data.get("pending_change_requests") or []
        row = next((r for r in pending if r.get("id") == change_request.id), None)
        self.assertIsNotNone(row)
        self.assertIn("Specialty", row.get("summary_parts") or [])
        self.assertIn("Consultation fee", row.get("summary_parts") or [])

    def test_photo_only_change_request_summary(self):
        """Full-form uploads must not list every field; only an uploaded file counts as a change."""
        self.client.force_authenticate(user=self.doctor_user)
        minimal_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        photo = SimpleUploadedFile("tiny.png", minimal_png, content_type="image/png")
        response = self.client.patch(
            reverse("doctor-profile-completion"),
            {"photo": photo},
            format="multipart",
        )
        self.assertEqual(response.status_code, 202)
        cr = DoctorProfileChangeRequest.objects.filter(doctor=self.doctor_profile).latest("id")
        self.assertEqual(cr.proposed_data, {})
        self.assertTrue(cr.proposed_photo.name)
        self.assertEqual(cr.get_summary_parts(), ["Profile photo"])
        self.assertEqual(response.data.get("change_request_summary"), ["Profile photo"])

    def test_max_three_pending_change_requests_allowed_fourth_blocked(self):
        self.client.force_authenticate(user=self.doctor_user)
        for i in range(3):
            response = self.client.patch(
                reverse("doctor-profile-completion"),
                {"specialty": f"Spec-{i}"},
                format="json",
            )
            self.assertEqual(response.status_code, 202, msg=getattr(response, "data", response.content))
        fourth = self.client.patch(
            reverse("doctor-profile-completion"),
            {"specialty": "Spec-blocked"},
            format="json",
        )
        self.assertEqual(fourth.status_code, 400)

    def test_photo_only_upload_is_not_blocked_by_unchanged_legacy_modes(self):
        DoctorProfile.objects.filter(pk=self.doctor_profile.pk).update(consultation_modes=["online"])
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.patch(reverse("doctor-profile-completion"), {"photo": self.profile_photo()}, format="multipart")
        self.assertEqual(response.status_code, 202, response.data)
        proposal = DoctorProfileChangeRequest.objects.get(doctor=self.doctor_profile)
        self.assertEqual(proposal.proposed_data, {})
        self.assertTrue(proposal.proposed_photo)
        self.assertEqual(proposal.get_summary_parts(), ["Profile photo"])
        self.doctor_profile.refresh_from_db()
        self.assertFalse(self.doctor_profile.photo)
        self.assertTrue(self.doctor_profile.admin_verified)
        self.assertTrue(self.doctor_profile.is_approved)

    def test_photo_with_valid_multipart_modes_preserves_admin_approval(self):
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.patch(reverse("doctor-profile-completion"),
            {"photo": self.profile_photo(), "consultation_modes": ["VIDEO"]}, format="multipart")
        self.assertEqual(response.status_code, 202, response.data)
        proposal = DoctorProfileChangeRequest.objects.get(doctor=self.doctor_profile)
        self.assertEqual(proposal.proposed_data, {})
        self.assertTrue(proposal.proposed_photo)
        self.doctor_profile.refresh_from_db()
        self.assertFalse(self.doctor_profile.photo)
        self.assertTrue(self.doctor_profile.is_approved)

    def test_invalid_submitted_mode_still_rejects_photo_without_creating_request(self):
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.patch(reverse("doctor-profile-completion"),
            {"photo": self.profile_photo(), "consultation_modes": ["online"]}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("consultation_modes", response.data["error"])
        self.assertFalse(DoctorProfileChangeRequest.objects.filter(doctor=self.doctor_profile).exists())

    def test_staff_verification_applies_latest_pending_profile_change(self):
        DoctorProfileChangeRequest.objects.create(
            doctor=self.doctor_profile,
            requested_by=self.doctor_user,
            proposed_data={"specialty": "Cardiology", "consultation_fee": "750.00"},
        )
        self.doctor_profile.has_pending_changes = True
        self.doctor_profile.save(update_fields=["has_pending_changes", "updated_at"])
        staff = User.objects.create_user(email="profile-change-staff@test.com", password="testpass123", is_staff=True)
        self.client.force_authenticate(user=staff)

        response = self.client.post(
            reverse("staff-doctor-verification", args=[self.doctor_profile.id]),
            {"action": "verify"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.doctor_profile.refresh_from_db()
        self.assertEqual(self.doctor_profile.specialty, "Cardiology")
        self.assertEqual(str(self.doctor_profile.consultation_fee), "750.00")
        self.assertFalse(self.doctor_profile.has_pending_changes)
        self.assertTrue(self.doctor_profile.admin_verified)
        self.assertFalse(self.doctor_profile.is_approved)
        self.assertEqual(
            self.doctor_profile.change_requests.get().status,
            DoctorProfileChangeRequest.Status.APPROVED,
        )

        approve = self.client.post(
            reverse("staff-doctor-verification", args=[self.doctor_profile.id]),
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(approve.status_code, 200)
        self.doctor_profile.refresh_from_db()
        self.assertTrue(self.doctor_profile.is_approved)
