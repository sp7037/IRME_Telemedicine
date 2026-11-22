from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MarketingLandingPage
from .serializers import CallbackRequestSerializer, MarketingLandingPageSerializer


def _lead_recipient():
    return (
        getattr(settings, "MARKETING_LEAD_EMAIL", "")
        or getattr(settings, "EMAIL_HOST_USER", "")
        or getattr(settings, "SERVER_EMAIL", "")
        or getattr(settings, "DEFAULT_FROM_EMAIL", "")
    )


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _rate_limit(key, limit, window_seconds):
    cache_key = f"marketing-callback:{key}"
    current = cache.get(cache_key, 0)
    if current >= limit:
        return False
    if current == 0:
        cache.set(cache_key, 1, window_seconds)
    else:
        cache.incr(cache_key)
    return True


class CallbackRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ip_limit = int(getattr(settings, "MARKETING_CALLBACK_IP_LIMIT", 8))
        ip_window = int(getattr(settings, "MARKETING_CALLBACK_IP_WINDOW_SECONDS", 3600))
        phone_limit = int(getattr(settings, "MARKETING_CALLBACK_PHONE_DAILY_LIMIT", 3))

        client_ip = _client_ip(request)
        if not _rate_limit(f"ip:{client_ip}", ip_limit, ip_window):
            return Response(
                {"detail": "Too many callback requests. Please try again later or use WhatsApp."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = CallbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_digits = "".join(ch for ch in serializer.validated_data["phone"] if ch.isdigit())
        if not _rate_limit(f"phone:{phone_digits}", phone_limit, 86400):
            return Response(
                {"detail": "Too many callback requests for this phone number today. Please use WhatsApp."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        lead = serializer.save()

        recipient = _lead_recipient()
        if recipient:
            subject = f"IRME callback request - {lead.get_interest_display()}"
            body = (
                f"Interest: {lead.get_interest_display()}\n"
                f"Name: {lead.name}\n"
                f"Phone: {lead.phone}\n"
                f"Email: {lead.email or '-'}\n"
                f"Location: {lead.city or '-'}, {lead.state or '-'}\n"
                f"Source: {lead.source_path or '-'}\n\n"
                f"Message:\n{lead.message or '-'}\n"
            )
            try:
                send_mail(
                    subject,
                    body,
                    getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    [recipient],
                    fail_silently=True,
                )
            except Exception:
                pass

        return Response({"message": "Callback request received."}, status=status.HTTP_201_CREATED)


class MarketingLandingPageListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        page_type = (request.query_params.get("type") or "").upper()
        pages = MarketingLandingPage.objects.filter(is_active=True)
        if page_type in {"TMC", "COURSE"}:
            pages = pages.filter(page_type=page_type)
        serializer = MarketingLandingPageSerializer(pages, many=True)
        return Response(serializer.data)


class MarketingLandingPageDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            page = MarketingLandingPage.objects.get(slug=slug, is_active=True)
        except MarketingLandingPage.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = MarketingLandingPageSerializer(page)
        return Response(serializer.data)
