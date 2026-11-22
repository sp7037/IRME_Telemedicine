"""Production-only authorised uploads and short-lived, user/path-bound URLs."""
import mimetypes
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, unquote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import FileResponse, Http404
from django.views.decorators.http import require_safe
from rest_framework.renderers import JSONRenderer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import APIException

SALT = "irme-private-media-v1"


class MediaJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        request = (renderer_context or {}).get("request")
        user = getattr(request, "user", None)
        if request and user and user.is_authenticated and user.is_active:
            def transform(value):
                if isinstance(value, dict):
                    return {k: transform(v) for k, v in value.items()}
                if isinstance(value, (list, tuple)):
                    return [transform(v) for v in value]
                if isinstance(value, str):
                    try:
                        parts = urlsplit(value)
                    except ValueError:
                        return value
                    if parts.path.startswith(settings.MEDIA_URL) and (not parts.netloc or parts.netloc == request.get_host()):
                        token = signing.dumps({"u": user.pk, "p": unquote(parts.path[len(settings.MEDIA_URL):])}, salt=SALT)
                        query = [(k, v) for k, v in parse_qsl(parts.query) if k != "access"]
                        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query + [("access", token)]), parts.fragment))
                return value
            data = transform(data)
        return super().render(data, accepted_media_type, renderer_context)


def _may_read(user, name):
    from users.models.profiles import (DoctorProfile, DoctorProfileChangeRequest, TMCProfile,
        TMCProfileChangeRequest, TMCQualificationDocument, TMCQualificationChangeRequest)
    from consultations.models import ConsultationChat, ConsultationRecord
    if DoctorProfile.objects.filter(photo=name, profile_completed=True, admin_verified=True,
        is_approved=True, user__is_active=True).exists():
        return True
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_staff:
        return True
    owners = [
        (DoctorProfile, "user_id", ["photo", "signature", "identity_proof", "registration_certificate"]),
        (DoctorProfileChangeRequest, "doctor__user_id", ["proposed_photo", "proposed_identity_proof", "proposed_registration_certificate"]),
        (TMCProfile, "user_id", ["aadhaar_document", "user_photo", "clinic_front_photo"]),
        (TMCProfileChangeRequest, "tmc__user_id", ["proposed_aadhaar_document", "proposed_user_photo", "proposed_clinic_front_photo"]),
        (TMCQualificationDocument, "tmc__user_id", ["document"]),
        (TMCQualificationChangeRequest, "tmc__user_id", ["document"]),
    ]
    for model, owner, fields in owners:
        query = Q()
        for field in fields:
            query |= Q(**{field: name})
        if model.objects.filter(query, **{owner: user.pk}).exists():
            return True
    participant = (Q(consultation__patient__user_id=user.pk) | Q(consultation__doctor__user_id=user.pk))
    if getattr(user, "is_tmc_operator", False):
        participant |= Q(consultation__tmc__user_id=user.pk)
    return (ConsultationChat.objects.filter(participant, attachment=name).exists()
        or ConsultationRecord.objects.filter(participant).filter(Q(video_recording=name) | Q(prescription=name)).exists())


@require_safe
def media(request, name):
    if not name or name.startswith("/") or "\\" in name or any(p in {".", ".."} for p in name.split("/")):
        raise Http404
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        try:
            auth = JWTAuthentication().authenticate(request)
            if auth:
                user = auth[0]
        except APIException:
            raise Http404
    if request.GET.get("access"):
        try:
            payload = signing.loads(request.GET["access"], salt=SALT, max_age=300)
            if payload["p"] != name:
                raise Http404
            user = get_user_model().objects.get(pk=payload["u"], is_active=True)
        except (signing.BadSignature, KeyError, get_user_model().DoesNotExist):
            raise Http404
    if not _may_read(user, name):
        raise Http404
    try:
        upload = default_storage.open(name, "rb")
    except FileNotFoundError:
        raise Http404 from None
    content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
    inline = content_type in {"image/jpeg", "image/png", "image/gif", "image/webp"}
    response = FileResponse(upload, content_type=content_type, as_attachment=not inline,
        filename=Path(name).name)
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Referrer-Policy"] = "no-referrer"
    return response
