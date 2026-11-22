"""Serialised release step for hosts without a console. Never changes existing passwords."""
import os
import uuid
import psycopg2
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import BaseCommand, CommandError, call_command
from django.db import connection, transaction

LOCK_ID = 607419822113


def verify_upload_storage():
    name = "_deployment-health/" + uuid.uuid4().hex
    saved = default_storage.save(name, ContentFile(b"irme-storage-check"))
    try:
        with default_storage.open(saved, "rb") as upload:
            if upload.read() != b"irme-storage-check":
                raise CommandError("Upload storage readback failed.")
    finally:
        default_storage.delete(saved)


def bootstrap_admin():
    if os.getenv("BOOTSTRAP_ADMIN_ENABLED", "false") != "true":
        return
    User = get_user_model()
    # A subsequent restart cannot reset or promote anyone, even if env values change.
    if User.objects.filter(is_superuser=True).exists():
        return
    email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    if not email or len(password) < 14:
        raise CommandError("Initial admin requires an email and a unique password of at least 14 characters.")
    user = User(email=email)
    try:
        user.full_clean(exclude=["password", "last_login", "date_joined"])
        validate_password(password, user=user)
    except ValidationError:
        raise CommandError("Initial admin details failed validation; no existing account was modified.") from None
    with transaction.atomic():
        User.objects.create_superuser(email=email, password=password, is_active=True, is_email_verified=True)


class Command(BaseCommand):
    help = "Verify storage, migrate under a PostgreSQL session lock, optionally create the first admin."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("Deployment release requires PostgreSQL.")
        if not settings.DEBUG and getattr(settings, "UPLOAD_STORAGE", None) == "s3":
            try:
                verify_upload_storage()
            except Exception:
                raise CommandError("Private upload storage check failed; verify bucket settings and permissions.") from None
        # Dedicated connection retains its session lock if migrate closes a Django connection.
        try:
            lock_connection = psycopg2.connect(**connection.get_connection_params())
        except psycopg2.Error:
            raise CommandError("Release database connection failed; verify server environment and SSL.") from None
        try:
            lock_connection.autocommit = True
            with lock_connection.cursor() as cursor:
                cursor.execute("SELECT pg_try_advisory_lock(%s)", [LOCK_ID])
                if not cursor.fetchone()[0]:
                    raise CommandError("Another release is running; retry after it completes.")
            call_command("migrate", interactive=False, verbosity=0)
            bootstrap_admin()
        finally:
            lock_connection.close()  # PostgreSQL releases the session lock on every exit path.
        self.stdout.write("Release checks and migrations completed.")
