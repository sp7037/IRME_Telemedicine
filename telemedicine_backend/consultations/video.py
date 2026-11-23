import logging
import uuid

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import ConsultationVideoSession

logger = logging.getLogger(__name__)


class VideoProviderError(Exception):
    """Raised when video provider setup or API calls fail."""


def _configured(value):
    value = str(value or "").strip()
    return bool(value and "..." not in value and not value.lower().startswith("your_"))


def _active_provider():
    return str(getattr(settings, "VIDEO_PROVIDER", "cloudflare") or "cloudflare").strip().lower()


def _user_role(user):
    if getattr(user, "is_doctor", False):
        return "doctor"
    if getattr(user, "is_tmc_operator", False):
        return "tmc"
    if getattr(user, "is_patient", False):
        return "patient"
    if getattr(user, "is_staff", False):
        return "staff"
    return "participant"


def _display_name(user):
    name = user.get_full_name() if hasattr(user, "get_full_name") else ""
    return name.strip() or getattr(user, "email", "") or f"User {user.id}"


def _cloudflare_enabled():
    return all(
        _configured(value)
        for value in (
            getattr(settings, "CLOUDFLARE_ACCOUNT_ID", ""),
            getattr(settings, "CLOUDFLARE_API_TOKEN", ""),
            getattr(settings, "CLOUDFLARE_CALLS_APP_ID", ""),
        )
    )


def _cloudflare_base_url():
    return str(
        getattr(
            settings,
            "CLOUDFLARE_REALTIMEKIT_BASE_URL",
            "https://api.cloudflare.com/client/v4",
        )
        or "https://api.cloudflare.com/client/v4"
    ).rstrip("/")


def _cloudflare_headers():
    token = str(getattr(settings, "CLOUDFLARE_API_TOKEN", "") or "").strip().strip('"').strip("'")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _cloudflare_meetings_url():
    return (
        f"{_cloudflare_base_url()}/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}"
        f"/realtime/kit/{settings.CLOUDFLARE_CALLS_APP_ID}/meetings"
    )


def _provider_data(response, action):
    try:
        payload = response.json()
    except ValueError as exc:
        raise VideoProviderError(f"Cloudflare returned an invalid response while trying to {action}.") from exc

    if not response.ok or payload.get("success") is False:
        detail = payload.get("errors") or payload.get("messages") or payload
        logger.error("Cloudflare RealtimeKit %s failed: %s", action, detail)
        raise VideoProviderError(f"Cloudflare RealtimeKit could not {action}: {detail}")

    return payload.get("data") or payload.get("result") or payload


def _cloudflare_request(method, url, *, json=None, action):
    try:
        response = requests.request(
            method,
            url,
            headers=_cloudflare_headers(),
            json=json,
            timeout=20,
        )
    except requests.exceptions.RequestException as exc:
        logger.exception("Cloudflare RealtimeKit request failed while trying to %s", action)
        raise VideoProviderError(f"Cloudflare RealtimeKit is unreachable while trying to {action}.") from exc
    return _provider_data(response, action)


def _cloudflare_create_meeting(consultation):
    payload = {
        "title": f"Consultation #{consultation.id}",
        "status": "ACTIVE",
        "session_keep_alive_time_in_secs": 600,
    }
    data = _cloudflare_request("POST", _cloudflare_meetings_url(), json=payload, action="create a meeting")
    meeting_id = data.get("id")
    if not meeting_id:
        raise VideoProviderError("Cloudflare RealtimeKit did not return a meeting id.")
    return {
        "meeting_id": meeting_id,
        "room_name": f"consultation_{consultation.id}",
        "provider": "cloudflare",
        "raw": data,
    }


def _cloudflare_preset_for_user(user):
    role = _user_role(user)
    if role == "doctor":
        return getattr(settings, "CLOUDFLARE_PRESET_DOCTOR", None) or getattr(
            settings, "DYTE_PRESET_DOCTOR", "group_call_host"
        )
    if role == "tmc":
        return getattr(settings, "CLOUDFLARE_PRESET_TMC", None) or getattr(
            settings, "DYTE_PRESET_TMC", "group_call_participant"
        )
    return getattr(settings, "CLOUDFLARE_PRESET_PATIENT", None) or getattr(
        settings, "DYTE_PRESET_PATIENT", "group_call_participant"
    )


def _cloudflare_add_participant(session, user, consultation):
    role = _user_role(user)
    participant_key = f"{role}_{user.id}_{uuid.uuid4().hex[:8]}"
    payload = {
        "name": _display_name(user),
        "preset_name": _cloudflare_preset_for_user(user),
        "custom_participant_id": participant_key,
    }
    url = f"{_cloudflare_meetings_url()}/{session.external_meeting_id}/participants"
    data = _cloudflare_request("POST", url, json=payload, action="add a participant")

    participant_id = data.get("id")
    token = data.get("token") or data.get("authToken") or data.get("auth_token")
    if not participant_id or not token:
        raise VideoProviderError("Cloudflare RealtimeKit did not return participant credentials.")

    return {
        "participant_id": participant_id,
        "token": token,
        "role": role,
        "preset_name": payload["preset_name"],
        "raw": data,
    }


def video_config_status():
    provider = _active_provider()
    cloudflare_missing = [
        name
        for name in (
            "CLOUDFLARE_ACCOUNT_ID",
            "CLOUDFLARE_API_TOKEN",
            "CLOUDFLARE_CALLS_APP_ID",
        )
        if provider == "cloudflare" and not _configured(getattr(settings, name, ""))
    ]
    return {
        "provider": provider,
        "cloudflare_enabled": _cloudflare_enabled(),
        "ready": provider == "cloudflare" and _cloudflare_enabled(),
        "missing": cloudflare_missing,
    }


VIDEO_UNAVAILABLE_CLIENT_MESSAGE = (
    "Video is temporarily unavailable. Please continue in chat."
)


def _configuration_error_message(provider=None):
    """Log detailed config gaps; return a participant-safe message (no env var names)."""
    status = video_config_status()
    provider = provider or status["provider"]
    missing = ", ".join(status["missing"])
    if missing:
        logger.error(
            "%s video is not configured. Missing or invalid: %s",
            provider,
            missing,
        )
    else:
        logger.error("%s video is not configured correctly.", provider)
    return VIDEO_UNAVAILABLE_CLIENT_MESSAGE


def client_video_error_payload(exc, user=None):
    """
    Build an API error payload for video failures.
    Raw config keys stay in server logs / staff responses only.
    """
    message = str(exc) or VIDEO_UNAVAILABLE_CLIENT_MESSAGE
    status = video_config_status()
    looks_like_config = (
        not status.get("ready")
        or "not configured" in message.lower()
        or "CLOUDFLARE_" in message
        or message == VIDEO_UNAVAILABLE_CLIENT_MESSAGE
    )
    if looks_like_config:
        message = VIDEO_UNAVAILABLE_CLIENT_MESSAGE
    payload = {"error": message}
    if user is not None and getattr(user, "is_staff", False):
        payload["config"] = status
    return payload


def _video_state(session):
    if not session:
        return {"status": "NONE"}
    return {
        "id": session.id,
        "status": session.status,
        "provider": session.provider,
        "requested_at": session.requested_at,
        "responded_at": session.responded_at,
        "created_by": session.created_by_id,
        "responded_by": session.responded_by_id,
    }


def video_state_for_consultation(consultation):
    try:
        session = consultation.video_session
    except ConsultationVideoSession.DoesNotExist:
        session = None
    return _video_state(session)


def request_video_session(consultation, user):
    if not getattr(user, "is_doctor", False) and not getattr(user, "is_staff", False):
        raise VideoProviderError("Only the doctor can start a video request.")

    with transaction.atomic():
        session = ConsultationVideoSession.objects.select_for_update().filter(consultation=consultation).first()
        if session:
            session.status = ConsultationVideoSession.Status.REQUESTED
            session.created_by = user
            session.responded_by = None
            session.responded_at = None
            session.requested_at = timezone.now()
            session.save(
                update_fields=[
                    "status",
                    "created_by",
                    "responded_by",
                    "responded_at",
                    "requested_at",
                    "updated_at",
                ]
            )
        else:
            session = ConsultationVideoSession.objects.create(
                consultation=consultation,
                provider=ConsultationVideoSession.Provider.CLOUDFLARE,
                status=ConsultationVideoSession.Status.REQUESTED,
                created_by=user,
            )
    return _video_state(session)


def respond_to_video_session(consultation, user, action):
    if (
        not getattr(user, "is_patient", False)
        and not getattr(user, "is_tmc_operator", False)
        and not getattr(user, "is_staff", False)
    ):
        raise VideoProviderError("Only the patient or assigned TMC can respond to a video request.")

    normalized = str(action or "").strip().lower()
    with transaction.atomic():
        session = ConsultationVideoSession.objects.select_for_update().filter(consultation=consultation).first()
        if not session or session.status != ConsultationVideoSession.Status.REQUESTED:
            raise VideoProviderError("There is no active video request to respond to.")
        if normalized == "accept":
            session.status = ConsultationVideoSession.Status.ACCEPTED
        elif normalized == "reject":
            session.status = ConsultationVideoSession.Status.REJECTED
        else:
            raise VideoProviderError("action must be accept or reject.")
        session.responded_by = user
        session.responded_at = timezone.now()
        session.save(update_fields=["status", "responded_by", "responded_at", "updated_at"])
    return _video_state(session)


def get_or_create_video_join(consultation, user):
    provider = _active_provider()
    if provider != "cloudflare":
        raise VideoProviderError("Unsupported video provider configured.")
    if not _cloudflare_enabled():
        raise VideoProviderError(_configuration_error_message("cloudflare"))

    with transaction.atomic():
        session = ConsultationVideoSession.objects.select_for_update().filter(consultation=consultation).first()
        if not session:
            raise VideoProviderError("The doctor must request video and the patient or TMC must accept before joining.")
        if session.status != ConsultationVideoSession.Status.ACCEPTED:
            raise VideoProviderError("Video can start only after the patient or TMC accepts the doctor's request.")

        if not session.external_meeting_id:
            room_data = _cloudflare_create_meeting(consultation)
            session.provider = ConsultationVideoSession.Provider.CLOUDFLARE
            session.external_meeting_id = room_data["meeting_id"]
            session.external_payload = room_data
            session.save(update_fields=["provider", "external_meeting_id", "external_payload", "updated_at"])

        participant_data = _cloudflare_add_participant(session, user, consultation)
        key = f"{user.id}_{_user_role(user)}"
        participant_tokens = session.participant_tokens or {}
        participant_ids = session.participant_ids or {}
        participant_tokens[key] = participant_data["token"]
        participant_ids[key] = participant_data["participant_id"]
        session.participant_tokens = participant_tokens
        session.participant_ids = participant_ids
        session.save(update_fields=["participant_tokens", "participant_ids", "updated_at"])

    return {
        "provider": "cloudflare",
        "consultation_id": consultation.id,
        "meeting_id": session.external_meeting_id,
        "session_id": session.external_meeting_id,
        "participant_id": participant_data["participant_id"],
        "participant_token": participant_data["token"],
        "auth_token": participant_data["token"],
        "room_name": session.external_payload.get("room_name") or f"consultation_{consultation.id}",
        "app_id": settings.CLOUDFLARE_CALLS_APP_ID,
        "account_id": settings.CLOUDFLARE_ACCOUNT_ID,
    }
