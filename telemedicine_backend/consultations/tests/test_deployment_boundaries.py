import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.conf import settings
from django.core import signing
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIRequestFactory

from users.models import User, DoctorProfile, PatientProfile
from consultations.models import Consultation, ConsultationChat
from django.utils import timezone
from telemedicine_project.protected_media import MediaJSONRenderer, SALT


class DeploymentBoundaryTests(TransactionTestCase):
    def get(self, *args, **kwargs):
        response = self.client.get(*args, **kwargs)
        self.addCleanup(response.close)
        return response

    def setUp(self):
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / "index.html").write_text('<div id="root">app</div>', encoding="utf-8")
        self.override = override_settings(ROOT_URLCONF="telemedicine_project.production_urls",
            MEDIA_ROOT=self.root, MEDIA_URL="/media/", FRONTEND_DIST=self.root)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.directory.cleanup)
        self.doctor_user = User.objects.create_user(email="doctor@deployment.test", password="x", is_doctor=True)
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, photo="photo.png", identity_proof="identity.pdf")
        self.other = User.objects.create_user(email="other@deployment.test", password="x", is_patient=True)
        for name in ("photo.png", "identity.pdf", "chat.pdf", "name space.pdf"):
            (self.root / name).write_bytes(b"synthetic test upload")

    def token(self, user, name):
        return signing.dumps({"u": user.pk, "p": name}, salt=SALT)

    def test_spa_admin_and_api_routes_are_distinct_and_unknown_api_is_not_html(self):
        self.assertEqual(self.get("/admin/patients").status_code, 200)
        self.assertEqual(self.get("/patient/book").status_code, 200)
        self.assertEqual(self.get("/api/admin/").status_code, 302)
        self.assertEqual(self.get("/api/unknown/").status_code, 404)
        self.assertEqual(self.get("/static/missing.js").status_code, 404)

    def test_health_checks_database_and_does_not_disclose_connection_details(self):
        response = self.get("/api/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_private_document_requires_authorised_user_and_approved_photo_is_public(self):
        self.assertEqual(self.get("/media/identity.pdf").status_code, 404)
        self.assertEqual(self.get("/media/photo.png").status_code, 404)
        self.doctor.profile_completed = self.doctor.admin_verified = self.doctor.is_approved = True
        self.doctor.save(update_fields=["profile_completed", "admin_verified", "is_approved"])
        self.assertEqual(self.get("/media/photo.png").status_code, 200)
        token = self.token(self.doctor_user, "identity.pdf")
        response = self.get("/media/identity.pdf", {"access": token})
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_signed_url_cannot_grant_another_user_access_or_change_its_path(self):
        self.assertEqual(self.get("/media/identity.pdf", {"access": self.token(self.other, "identity.pdf")}).status_code, 404)
        self.assertEqual(self.get("/media/photo.png", {"access": self.token(self.doctor_user, "identity.pdf")}).status_code, 404)
        self.assertEqual(self.get("/media/../outside.txt").status_code, 404)
        token = self.token(self.doctor_user, "identity.pdf")
        with patch("django.core.signing.TimestampSigner.unsign", side_effect=signing.SignatureExpired()):
            self.assertEqual(self.get("/media/identity.pdf", {"access": token}).status_code, 404)

    def test_deactivated_token_owner_loses_file_access(self):
        token = self.token(self.doctor_user, "identity.pdf")
        self.doctor_user.is_active = False; self.doctor_user.save(update_fields=["is_active"])
        self.assertEqual(self.get("/media/identity.pdf", {"access": token}).status_code, 404)

    def test_chat_attachment_is_available_only_to_consultation_participants(self):
        patient = PatientProfile.objects.create(user=self.other)
        c = Consultation.objects.create(patient=patient, doctor=self.doctor, scheduled_time=timezone.now())
        ConsultationChat.objects.create(consultation=c, sender=self.doctor_user, attachment="chat.pdf")
        self.assertEqual(self.get("/media/chat.pdf", {"access": self.token(self.other, "chat.pdf")}).status_code, 200)
        outsider = User.objects.create_user(email="outsider@deployment.test", password="x", is_patient=True)
        self.assertEqual(self.get("/media/chat.pdf", {"access": self.token(outsider, "chat.pdf")}).status_code, 404)

    def test_renderer_signs_relative_file_urls_without_modifying_text_or_foreign_urls(self):
        request = APIRequestFactory().get("/")
        request.user = self.doctor_user
        data = {"file": "/media/name%20space.pdf", "text": "https://[invalid", "external": "https://elsewhere.test/media/x"}
        result = json.loads(MediaJSONRenderer().render(data, renderer_context={"request": request}))
        self.assertIn("access=", result["file"])
        self.assertEqual(result["text"], data["text"])
        self.assertEqual(result["external"], data["external"])

    def test_production_settings_fail_closed_without_secret_and_accept_explicit_config(self):
        env = {**os.environ, "DJANGO_SETTINGS_MODULE": "telemedicine_project.production_settings",
            "SECRET_KEY": "test-only-production-check-0000000000000000000000000000000000000000",
            "DB_NAME": "unused", "DB_USER": "unused", "DB_PASSWORD": "test-only", "DB_HOST": "127.0.0.1",
            "MEDIA_ROOT": str(self.root), "RAZORPAY_KEY_ID": "", "RAZORPAY_KEY_SECRET": "",
            "DEPLOYMENT_STAGE": "staging", "FRONTEND_BASE_URL": "https://telemedicine.irme.in"}
        env.update(UPLOAD_STORAGE="filesystem", ALLOW_PERSISTENT_FILESYSTEM="true", DATABASE_URL="")
        command = [sys.executable, "-c", "from django.conf import settings; assert not settings.DEBUG; assert settings.ROOT_URLCONF == 'telemedicine_project.production_urls'"]
        result = subprocess.run(command, cwd=settings.BASE_DIR, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        env.pop("SECRET_KEY")
        result = subprocess.run(command, cwd=settings.BASE_DIR, env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY", result.stderr)

    def test_database_url_decodes_credentials_and_rejects_unencrypted_external_db(self):
        env = {**os.environ, "DJANGO_SETTINGS_MODULE": "telemedicine_project.production_settings",
            "SECRET_KEY": "test-only-00000000000000000000000000000000000000000000000000",
            "UPLOAD_STORAGE": "filesystem", "ALLOW_PERSISTENT_FILESYSTEM": "true",
            "DATABASE_URL": "postgresql://test%40user:fake%2Fpassword@database.example.test/example?sslmode=require",
            "FRONTEND_BASE_URL": "https://telemedicine.irme.in",
            "RAZORPAY_KEY_ID": "", "RAZORPAY_KEY_SECRET": "", "DEPLOYMENT_STAGE": "staging"}
        command = [sys.executable, "-c", "from django.conf import settings; d=settings.DATABASES['default']; assert d['USER']=='test@user'; assert d['PASSWORD']=='fake/password'; assert d['OPTIONS']['sslmode']=='require'"]
        result = subprocess.run(command, cwd=settings.BASE_DIR, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        env["DATABASE_URL"] = env["DATABASE_URL"].replace("sslmode=require", "sslmode=disable")
        result = subprocess.run(command, cwd=settings.BASE_DIR, env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("require SSL", result.stderr)

    def test_s3_url_keeps_private_objects_behind_application_acl(self):
        from telemedicine_project.upload_storage import PrivateS3Storage
        storage = PrivateS3Storage(bucket_name="synthetic-test", access_key="test-only", secret_key="test-only")
        self.assertEqual(storage.url("private/name space.pdf"), "/media/private/name%20space.pdf")
        # Exercise the authorisation path with a non-filesystem storage double.
        from django.core.files.base import ContentFile
        with patch("telemedicine_project.protected_media.default_storage") as remote:
            remote.open.return_value = ContentFile(b"private object")
            self.assertEqual(self.get("/media/identity.pdf").status_code, 404)
            remote.open.assert_not_called()
            response = self.get("/media/identity.pdf", {"access": self.token(self.doctor_user, "identity.pdf")})
            self.assertEqual(response.status_code, 200)
            remote.open.assert_called_once_with("identity.pdf", "rb")

    def test_release_is_serialised_and_does_not_reset_initial_admin(self):
        from django.core.management import call_command, CommandError
        from consultations.management.commands.deploy_release import LOCK_ID
        from django.db import connection
        import psycopg2
        with patch("consultations.management.commands.deploy_release.call_command") as migrate, patch.dict(os.environ, {
            "BOOTSTRAP_ADMIN_ENABLED": "true", "BOOTSTRAP_ADMIN_EMAIL": "admin@deployment.test",
            "BOOTSTRAP_ADMIN_PASSWORD": "Only-for-synthetic-test-7243!"}):
            call_command("deploy_release", verbosity=0)
            admin = User.objects.get(email="admin@deployment.test")
            self.assertTrue(admin.is_superuser and admin.check_password("Only-for-synthetic-test-7243!"))
            first_hash = admin.password
            with patch.dict(os.environ, {"BOOTSTRAP_ADMIN_PASSWORD": "Different-test-password-8492!"}):
                call_command("deploy_release", verbosity=0)
            admin.refresh_from_db()
            self.assertEqual(admin.password, first_hash)
            self.assertEqual(migrate.call_count, 2)
            with psycopg2.connect(**connection.get_connection_params()) as competing:
                competing.autocommit = True
                with competing.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_lock(%s)", [LOCK_ID])
                with self.assertRaisesMessage(CommandError, "Another release"):
                    call_command("deploy_release", verbosity=0)
            competing.close()
            self.assertEqual(migrate.call_count, 2)
