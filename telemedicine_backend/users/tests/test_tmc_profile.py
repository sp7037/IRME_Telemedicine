import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import PatientProfile, TMCProfile, TMCProfileChangeRequest, TMCQualificationChangeRequest, TMCQualificationDocument, User


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TMCProfileAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="tmc-profile@test.com",
            password="testpass123",
            is_tmc_operator=True,
        )
        self.profile = TMCProfile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)

    def test_tmc_profile_accepts_clinic_details_and_documents(self):
        pdf = SimpleUploadedFile("aadhaar.pdf", b"%PDF-1.4\n%test\n", content_type="application/pdf")
        image = SimpleUploadedFile(
            "photo.gif",
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )

        response = self.client.patch(
            reverse("tmc-profile"),
            {
                "clinic_name": "IRME Rural Clinic",
                "clinic_address_street": "Main Road",
                "city": "Deoband",
                "state": "Uttar Pradesh",
                "pin_code": "247554",
                "tmc_details": "Assisted telemedicine center",
                "aadhaar_document": pdf,
                "user_photo": image,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.clinic_name, "IRME Rural Clinic")
        self.assertFalse(self.profile.profile_completed)

    def test_tmc_qualification_requires_pdf(self):
        bad_file = SimpleUploadedFile("marksheet.txt", b"not pdf", content_type="text/plain")

        response = self.client.post(
            reverse("tmc-qualification-documents"),
            {
                "exam_name": TMCQualificationDocument.ExamName.SECONDARY,
                "board_or_university": "State Board",
                "percentage": "72.50",
                "document": bad_file,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("document", response.data)

    def test_verified_tmc_profile_changes_create_admin_request(self):
        self.profile.admin_verified = True
        self.profile.is_approved = True
        self.profile.clinic_name = "Approved Clinic"
        self.profile.save(update_fields=["admin_verified", "is_approved", "clinic_name"])

        response = self.client.patch(
            reverse("tmc-profile"),
            {"clinic_name": "Changed Clinic"},
            format="multipart",
        )

        self.assertEqual(response.status_code, 202)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.clinic_name, "Approved Clinic")
        self.assertTrue(TMCProfileChangeRequest.objects.filter(tmc=self.profile, status="PENDING").exists())

    def test_verified_tmc_document_delete_creates_admin_request(self):
        self.profile.admin_verified = True
        self.profile.is_approved = True
        self.profile.save(update_fields=["admin_verified", "is_approved"])
        doc = TMCQualificationDocument.objects.create(
            tmc=self.profile,
            exam_name=TMCQualificationDocument.ExamName.SECONDARY,
            board_or_university="State Board",
            percentage="72.50",
            document=SimpleUploadedFile("marksheet.pdf", b"%PDF-1.4\n", content_type="application/pdf"),
        )

        response = self.client.delete(reverse("tmc-qualification-document-detail", kwargs={"pk": doc.id}))

        self.assertEqual(response.status_code, 202)
        self.assertTrue(TMCQualificationDocument.objects.filter(pk=doc.id).exists())
        self.assertTrue(TMCQualificationChangeRequest.objects.filter(tmc=self.profile, target_document=doc).exists())

    def test_tmc_patient_list_only_returns_own_created_patients(self):
        other_user = User.objects.create_user(email="other-patient@test.com", password="testpass123", is_patient=True)
        PatientProfile.objects.create(user=other_user)

        create_response = self.client.post(
            reverse("tmc-patients"),
            {"name": "Aliya Salauddi", "age": 31, "gender": "F"},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)

        list_response = self.client.get(reverse("tmc-patients"))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["name"], "Aliya Salauddi")
