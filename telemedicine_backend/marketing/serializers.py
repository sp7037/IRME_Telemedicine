import time

from rest_framework import serializers

from .models import CallbackRequest, MarketingLandingPage


class CallbackRequestSerializer(serializers.ModelSerializer):
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)
    started_at = serializers.FloatField(required=False, write_only=True)

    class Meta:
        model = CallbackRequest
        fields = [
            "interest",
            "name",
            "phone",
            "email",
            "state",
            "city",
            "message",
            "source_path",
            "website",
            "started_at",
        ]

    def validate(self, attrs):
        if attrs.pop("website", ""):
            raise serializers.ValidationError("Unable to submit callback request.")

        started_at = attrs.pop("started_at", None)
        if started_at:
            started_at_seconds = started_at / 1000 if started_at > 9999999999 else started_at
            if time.time() - started_at_seconds < 3:
                raise serializers.ValidationError("Please review the form before submitting.")
        return attrs

    def validate_phone(self, value):
        cleaned = "".join(ch for ch in value if ch.isdigit() or ch == "+")
        digits = "".join(ch for ch in cleaned if ch.isdigit())
        if len(digits) < 10:
            raise serializers.ValidationError("Enter a valid mobile number.")
        return cleaned


class MarketingLandingPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketingLandingPage
        fields = [
            "page_type",
            "state",
            "city",
            "slug",
            "title",
            "meta_description",
            "h1",
            "intro",
            "body",
        ]
