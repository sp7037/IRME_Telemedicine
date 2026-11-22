import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models.users import EmailVerificationOTP


OTP_TTL_MINUTES = 15
OTP_MAX_ATTEMPTS = 5


def _hash_otp(otp):
    return hashlib.sha256(f"{settings.SECRET_KEY}:{otp}".encode("utf-8")).hexdigest()


def create_registration_otp(user, purpose):
    EmailVerificationOTP.objects.filter(
        user=user,
        purpose=purpose,
        consumed_at__isnull=True,
    ).update(consumed_at=timezone.now())
    otp = f"{secrets.randbelow(1000000):06d}"
    EmailVerificationOTP.objects.create(
        user=user,
        purpose=purpose,
        otp_hash=_hash_otp(otp),
        expires_at=timezone.now() + timedelta(minutes=OTP_TTL_MINUTES),
    )
    return otp


def create_doctor_email_otp(user):
    return create_registration_otp(user, EmailVerificationOTP.Purpose.DOCTOR_EMAIL_VERIFICATION)


def create_patient_email_otp(user):
    return create_registration_otp(user, EmailVerificationOTP.Purpose.PATIENT_EMAIL_VERIFICATION)


def create_tmc_email_otp(user):
    return create_registration_otp(user, EmailVerificationOTP.Purpose.TMC_EMAIL_VERIFICATION)


def _frontend_url(path, **query):
    base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
    url = f"{base}{path}"
    cleaned_query = {key: value for key, value in query.items() if value not in (None, "")}
    if cleaned_query:
        url = f"{url}?{urlencode(cleaned_query)}"
    return url


def _send_templated_email(subject, template_base, context, recipients):
    text_body = render_to_string(f"emails/{template_base}.txt", context)
    html_body = render_to_string(f"emails/{template_base}.html", context)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "IRME Telemedicine <no-reply@irme.in>"),
        to=recipients,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)


def send_doctor_verification_email(user, otp):
    context = {
        "user": user,
        "otp": otp,
        "ttl_minutes": OTP_TTL_MINUTES,
        "verify_url": _frontend_url("/verify-email", email=user.email),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "Verify your IRME doctor account",
        "doctor_email_verification",
        context,
        [user.email],
    )


def send_patient_verification_email(user, otp):
    context = {
        "user": user,
        "otp": otp,
        "ttl_minutes": OTP_TTL_MINUTES,
        "verify_url": _frontend_url("/verify-email", email=user.email),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "Verify your IRME patient account",
        "patient_email_verification",
        context,
        [user.email],
    )


def send_tmc_verification_email(user, otp):
    context = {
        "user": user,
        "otp": otp,
        "ttl_minutes": OTP_TTL_MINUTES,
        "verify_url": _frontend_url("/verify-email", email=user.email),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "Verify your IRME telemedicine center account",
        "tmc_email_verification",
        context,
        [user.email],
    )


def send_doctor_email_verified_success_email(user):
    context = {
        "user": user,
        "login_url": _frontend_url("/login"),
        # Require sign-in first so JWT matches the doctor (email links have no session).
        "profile_url": _frontend_url("/login", next="/doctor/profile"),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "Your IRME doctor email is verified",
        "doctor_email_verified_success",
        context,
        [user.email],
    )


def send_patient_email_verified_success_email(user):
    context = {
        "user": user,
        "login_url": _frontend_url("/login"),
        "dashboard_url": _frontend_url("/login", next="/dashboard/patient"),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "Welcome to IRME — patient email verified",
        "patient_email_verified_success",
        context,
        [user.email],
    )


def send_tmc_email_verified_success_email(user):
    context = {
        "user": user,
        "login_url": _frontend_url("/login"),
        "dashboard_url": _frontend_url("/login", next="/dashboard/tmc"),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "Welcome to IRME — center account verified",
        "tmc_email_verified_success",
        context,
        [user.email],
    )


def send_doctor_profile_completed_email(user):
    context = {
        "user": user,
        "login_url": _frontend_url("/login"),
        "dashboard_url": _frontend_url("/login", next="/dashboard/doctor"),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "Your IRME doctor profile is complete",
        "doctor_profile_completed",
        context,
        [user.email],
    )


def send_doctor_profile_admin_verified_email(user):
    context = {
        "user": user,
        "login_url": _frontend_url("/login"),
        "dashboard_url": _frontend_url("/login", next="/dashboard/doctor"),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "Your IRME doctor profile is verified",
        "doctor_profile_admin_verified",
        context,
        [user.email],
    )


def send_doctor_consultations_approved_email(user):
    context = {
        "user": user,
        "login_url": _frontend_url("/login"),
        "dashboard_url": _frontend_url("/login", next="/dashboard/doctor"),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "You can take consultations on IRME",
        "doctor_consultations_approved",
        context,
        [user.email],
    )


def send_doctor_profile_change_request_submitted_email(user, summary_parts):
    context = {
        "user": user,
        "summary_parts": list(summary_parts or []),
        "profile_url": _frontend_url("/login", next="/doctor/profile"),
        "dashboard_url": _frontend_url("/login", next="/dashboard/doctor"),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "We received your IRME profile change request",
        "doctor_profile_change_request_submitted",
        context,
        [user.email],
    )


def send_doctor_profile_changes_approved_email(user, summary_parts):
    context = {
        "user": user,
        "summary_parts": list(summary_parts or []),
        "profile_url": _frontend_url("/login", next="/doctor/profile"),
        "dashboard_url": _frontend_url("/login", next="/dashboard/doctor"),
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@irme.in"),
    }
    _send_templated_email(
        "Your IRME profile updates are approved",
        "doctor_profile_changes_approved",
        context,
        [user.email],
    )


def _send_registration_verified_success_email(user):
    if user.is_doctor:
        send_doctor_email_verified_success_email(user)
    elif user.is_patient:
        send_patient_email_verified_success_email(user)
    elif user.is_tmc_operator:
        send_tmc_email_verified_success_email(user)


def _consume_otp_verify_user(user, purpose, otp):
    row = EmailVerificationOTP.objects.filter(
        user=user,
        purpose=purpose,
        consumed_at__isnull=True,
    ).order_by("-created_at").first()
    if not row:
        raise ValueError("No active verification OTP found. Please request a new OTP.")
    if row.is_expired:
        raise ValueError("OTP has expired. Please request a new OTP.")
    if row.attempts >= OTP_MAX_ATTEMPTS:
        raise ValueError("Too many failed attempts. Please request a new OTP.")

    row.attempts += 1
    if row.otp_hash != _hash_otp(str(otp).strip()):
        row.save(update_fields=["attempts"])
        raise ValueError("Invalid OTP.")

    row.consumed_at = timezone.now()
    row.save(update_fields=["attempts", "consumed_at"])
    user.is_email_verified = True
    user.email_verified_at = timezone.now()
    user.save(update_fields=["is_email_verified", "email_verified_at"])
    _send_registration_verified_success_email(user)


def verify_registration_email_otp(email, otp):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        raise ValueError("Account not found.")
    if user.is_email_verified:
        return user
    if user.is_doctor:
        purpose = EmailVerificationOTP.Purpose.DOCTOR_EMAIL_VERIFICATION
    elif user.is_patient:
        purpose = EmailVerificationOTP.Purpose.PATIENT_EMAIL_VERIFICATION
    elif user.is_tmc_operator:
        purpose = EmailVerificationOTP.Purpose.TMC_EMAIL_VERIFICATION
    else:
        raise ValueError("Account not found.")
    _consume_otp_verify_user(user, purpose, otp)
    return user


def resend_registration_otp_for_user(user):
    if user.is_doctor:
        otp = create_doctor_email_otp(user)
        send_doctor_verification_email(user, otp)
        return otp
    if user.is_patient:
        otp = create_patient_email_otp(user)
        send_patient_verification_email(user, otp)
        return otp
    if user.is_tmc_operator:
        otp = create_tmc_email_otp(user)
        send_tmc_verification_email(user, otp)
        return otp
    raise ValueError("Unsupported account type.")


def verify_doctor_email_otp(email, otp):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.filter(email__iexact=email, is_doctor=True).first()
    if not user:
        raise ValueError("Doctor account not found.")
    verify_registration_email_otp(email, otp)
    user.refresh_from_db()
    return user
