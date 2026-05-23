import base64
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import ConsultationVideoSession


class VideoProviderError(Exception):
    pass


def _dyte_headers():
    token = base64.b64encode(
        f"{settings.DYTE_ORGANIZATION_ID}:{settings.DYTE_API_KEY}".encode("utf-8")
    ).decode("ascii")
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def _cloudflare_headers():
    token = str(settings.CLOUDFLARE_API_TOKEN or "").strip().strip('"').strip("'")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _cloudflare_meetings_url():
    return (
        f"{settings.CLOUDFLARE_REALTIMEKIT_BASE_URL}/accounts/"
        f"{settings.CLOUDFLARE_ACCOUNT_ID}/realtime/kit/"
        f"{settings.CLOUDFLARE_CALLS_APP_ID}/meetings"
    )


def _json_request(method, url, payload=None, headers=None):
    body = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
    req = Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise VideoProviderError(f"Video provider request failed ({exc.code}): {detail}") from exc
    except URLError as exc:
        raise VideoProviderError(f"Video provider is unreachable: {exc.reason}") from exc
    return json.loads(raw or "{}")


def _active_provider():
    return (settings.VIDEO_PROVIDER or "cloudflare").lower()


def _configured(value):
    value = str(value or "").strip()
    return bool(value and "..." not in value and not value.lower().startswith("your_"))


def _provider_model_value():
    if _active_provider() == "cloudflare":
        return ConsultationVideoSession.Provider.CLOUDFLARE
    return ConsultationVideoSession.Provider.DYTE


def _configuration_error_message(provider=None):
    status = video_config_status()
    missing = status.get("missing") or []
    provider = provider or status.get("provider") or "video"
    if missing:
        return (
            f"{provider.title()} credentials are not configured on the backend. "
            f"Missing or invalid: {', '.join(missing)}."
        )
    return f"{provider.title()} credentials are not configured on the backend."


def _meeting_from_response(data):
    return data.get("data") or data.get("result") or data.get("meeting") or data


def _participant_from_response(data):
    return data.get("data") or data.get("result") or data.get("participant") or data


def _dyte_create_meeting(consultation):
    payload = {
        "title": f"IRME consultation #{consultation.id}",
        "preferred_region": "ap-south-1",
        "record_on_start": False,
    }
    data = _json_request(
        "POST",
        f"{settings.DYTE_BASE_URL}/meetings",
        payload,
        headers=_dyte_headers(),
    )
    meeting = data.get("data") or {}
    meeting_id = meeting.get("id")
    if not meeting_id:
        raise VideoProviderError("Dyte did not return a meeting id.")
    return meeting_id, data


def _cloudflare_create_meeting(consultation):
    payload = {
        "title": f"IRME consultation #{consultation.id}",
        "preferred_region": "ap-south-1",
        "record_on_start": False,
    }
    data = _json_request(
        "POST",
        _cloudflare_meetings_url(),
        payload,
        headers=_cloudflare_headers(),
    )
    meeting = _meeting_from_response(data)
    meeting_id = meeting.get("id") or meeting.get("meeting_id") or meeting.get("room_id")
    if not meeting_id:
        raise VideoProviderError("Cloudflare RealtimeKit did not return a meeting id.")
    return meeting_id, data


def _create_meeting(consultation):
    if _active_provider() == "cloudflare":
        return _cloudflare_create_meeting(consultation)
    return _dyte_create_meeting(consultation)


def _display_name_for(user):
    name = (user.get_full_name() or "").strip()
    return name or user.email or f"User {user.id}"


def _participant_role(user, consultation):
    if getattr(user, "doctor_profile", None) and consultation.doctor_id == user.doctor_profile.id:
        return "doctor"
    if getattr(user, "patient_profile", None) and consultation.patient_id == user.patient_profile.id:
        return "patient"
    tmc = getattr(user, "tmc_profile", None) or getattr(user, "tmcprofile_profile", None)
    if tmc and consultation.tmc_id == tmc.id:
        return "tmc"
    if user.is_staff:
        return "staff"
    return "participant"


def _preset_for(role):
    if role == "doctor":
        return settings.DYTE_PRESET_DOCTOR
    if role == "tmc":
        return settings.DYTE_PRESET_TMC
    return settings.DYTE_PRESET_PATIENT


def _dyte_add_participant(session, user, consultation):
    role = _participant_role(user, consultation)
    payload = {
        "name": _display_name_for(user),
        "preset_name": _preset_for(role),
        "custom_participant_id": f"{role}-{user.id}-consultation-{consultation.id}",
    }
    data = _json_request(
        "POST",
        f"{settings.DYTE_BASE_URL}/meetings/{session.external_meeting_id}/participants",
        payload,
        headers=_dyte_headers(),
    )
    participant = data.get("data") or {}
    participant_id = participant.get("id")
    token = participant.get("token") or participant.get("authToken") or participant.get("auth_token")
    if not token:
        raise VideoProviderError("Dyte did not return a participant token.")

    key = str(user.id)
    tokens = dict(session.participant_tokens or {})
    participant_ids = dict(session.participant_ids or {})
    tokens[key] = token
    if participant_id:
        participant_ids[key] = participant_id
    session.participant_tokens = tokens
    session.participant_ids = participant_ids
    session.save(update_fields=["participant_tokens", "participant_ids", "updated_at"])
    return token, participant_id, role


def _cloudflare_add_participant(session, user, consultation):
    role = _participant_role(user, consultation)
    payload = {
        "name": _display_name_for(user),
        "preset_name": _preset_for(role),
        "custom_participant_id": f"{role}-{user.id}-consultation-{consultation.id}",
    }
    data = _json_request(
        "POST",
        f"{_cloudflare_meetings_url()}/{session.external_meeting_id}/participants",
        payload,
        headers=_cloudflare_headers(),
    )
    participant = _participant_from_response(data)
    participant_id = participant.get("id") or participant.get("participant_id")
    token = (
        participant.get("token")
        or participant.get("authToken")
        or participant.get("auth_token")
        or participant.get("participant_token")
    )
    if not token:
        raise VideoProviderError("Cloudflare RealtimeKit did not return a participant token.")

    key = str(user.id)
    tokens = dict(session.participant_tokens or {})
    participant_ids = dict(session.participant_ids or {})
    tokens[key] = token
    if participant_id:
        participant_ids[key] = participant_id
    session.participant_tokens = tokens
    session.participant_ids = participant_ids
    session.save(update_fields=["participant_tokens", "participant_ids", "updated_at"])
    return token, participant_id, role


def _add_participant(session, user, consultation):
    if _active_provider() == "cloudflare":
        return _cloudflare_add_participant(session, user, consultation)
    return _dyte_add_participant(session, user, consultation)


def video_config_status():
    provider = _active_provider()
    cloudflare_missing = [
        name
        for name, value in {
            "CLOUDFLARE_ACCOUNT_ID": settings.CLOUDFLARE_ACCOUNT_ID,
            "CLOUDFLARE_API_TOKEN": settings.CLOUDFLARE_API_TOKEN,
            "CLOUDFLARE_CALLS_APP_ID": settings.CLOUDFLARE_CALLS_APP_ID,
        }.items()
        if provider == "cloudflare" and not _configured(value)
    ]
    dyte_missing = [
        name
        for name, value in {
            "DYTE_ORGANIZATION_ID": settings.DYTE_ORGANIZATION_ID,
            "DYTE_API_KEY": settings.DYTE_API_KEY,
        }.items()
        if provider == "dyte" and not value
    ]
    return {
        "provider": provider,
        "cloudflare_enabled": settings.CLOUDFLARE_REALTIMEKIT_ENABLED,
        "dyte_enabled": settings.DYTE_ENABLED,
        "configured": (
            provider == "cloudflare" and settings.CLOUDFLARE_REALTIMEKIT_ENABLED
        ) or (
            provider == "dyte" and settings.DYTE_ENABLED
        ),
        "missing": cloudflare_missing + dyte_missing,
    }


def _video_state(session):
    if not session:
        return {"status": "NONE"}
    return {
        "status": session.status,
        "provider": session.provider,
        "requested_by": session.created_by_id,
        "responded_by": session.responded_by_id,
        "requested_at": session.requested_at,
        "responded_at": session.responded_at,
    }


def video_state_for_consultation(consultation):
    return _video_state(getattr(consultation, "video_session", None))


def _is_doctor(user, consultation):
    return getattr(user, "doctor_profile", None) and consultation.doctor_id == user.doctor_profile.id


def _can_respond(user, consultation):
    if getattr(user, "patient_profile", None) and consultation.patient_id == user.patient_profile.id:
        return True
    tmc = getattr(user, "tmc_profile", None) or getattr(user, "tmcprofile_profile", None)
    return bool(tmc and consultation.tmc_id == tmc.id)


@transaction.atomic
def request_video_session(consultation, user):
    if not (_is_doctor(user, consultation) or user.is_staff):
        raise VideoProviderError("Only the doctor can start a video request.")
    session = ConsultationVideoSession.objects.select_for_update().filter(consultation=consultation).first()
    if session:
        session.status = ConsultationVideoSession.Status.REQUESTED
        session.created_by = user
        session.responded_by = None
        session.responded_at = None
        session.requested_at = timezone.now()
        session.save(update_fields=["status", "created_by", "responded_by", "responded_at", "requested_at", "updated_at"])
    else:
        session = ConsultationVideoSession.objects.create(
            consultation=consultation,
            provider=_provider_model_value(),
            status=ConsultationVideoSession.Status.REQUESTED,
            created_by=user,
        )
    return _video_state(session)


@transaction.atomic
def respond_to_video_session(consultation, user, action):
    if not _can_respond(user, consultation):
        raise VideoProviderError("Only the patient or assigned TMC can respond to a video request.")
    session = ConsultationVideoSession.objects.select_for_update().filter(consultation=consultation).first()
    if not session or session.status != ConsultationVideoSession.Status.REQUESTED:
        raise VideoProviderError("There is no active video request to respond to.")
    if action == "accept":
        session.status = ConsultationVideoSession.Status.ACCEPTED
    elif action == "reject":
        session.status = ConsultationVideoSession.Status.REJECTED
    else:
        raise VideoProviderError("action must be accept or reject.")
    session.responded_by = user
    session.responded_at = timezone.now()
    session.save(update_fields=["status", "responded_by", "responded_at", "updated_at"])
    return _video_state(session)


@transaction.atomic
def get_or_create_video_join(consultation, user):
    provider = _active_provider()
    if provider not in {"cloudflare", "dyte"}:
        raise VideoProviderError("Unsupported video provider configured.")

    session = ConsultationVideoSession.objects.select_for_update().filter(consultation=consultation).first()
    if not session:
        raise VideoProviderError("The doctor must request video and the patient or TMC must accept before joining.")
    if session.status != ConsultationVideoSession.Status.ACCEPTED:
        raise VideoProviderError("Video can start only after the patient or TMC accepts the doctor's request.")
    if provider == "cloudflare" and not settings.CLOUDFLARE_REALTIMEKIT_ENABLED:
        raise VideoProviderError(_configuration_error_message("cloudflare"))
    if provider == "dyte" and not settings.DYTE_ENABLED:
        raise VideoProviderError(_configuration_error_message("dyte"))
    if not session.external_meeting_id:
        meeting_id, payload = _create_meeting(consultation)
        session.provider = _provider_model_value()
        session.external_meeting_id = meeting_id
        session.external_payload = payload
        session.save(update_fields=["provider", "external_meeting_id", "external_payload", "updated_at"])

    key = str(user.id)
    role = _participant_role(user, consultation)
    token = (session.participant_tokens or {}).get(key)
    participant_id = (session.participant_ids or {}).get(key)
    if not token:
        token, participant_id, role = _add_participant(session, user, consultation)

    return {
        "provider": provider,
        "consultation_id": consultation.id,
        "meeting_id": session.external_meeting_id,
        "participant_id": participant_id,
        "role": role,
        "auth_token": token,
    }
