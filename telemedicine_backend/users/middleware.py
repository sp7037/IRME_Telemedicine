from django.http import JsonResponse


class DoctorOnboardingGateMiddleware:
    """
    Blocks authenticated doctors from consultation APIs until email/profile/admin
    onboarding gates are satisfied.
    """

    EXEMPT_PREFIXES = (
        "/admin/",
        "/media/",
        "/static/",
        "/users/",
        "/consultations/doctor/profile/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        route = request.path[4:] if request.path.startswith("/api/") else request.path
        if (
            user
            and user.is_authenticated
            and getattr(user, "is_doctor", False)
            and route.startswith("/consultations/")
            and not route.startswith(self.EXEMPT_PREFIXES)
        ):
            profile = getattr(user, "doctor_profile", None)
            if not getattr(user, "is_email_verified", False):
                return JsonResponse(
                    {"error": "Email verification is required.", "next_step": "VERIFY_EMAIL"},
                    status=403,
                )
            if not profile or not profile.profile_completed:
                return JsonResponse(
                    {"error": "Complete your doctor profile before using this feature.", "next_step": "COMPLETE_PROFILE"},
                    status=403,
                )
            if not profile.admin_verified:
                return JsonResponse(
                    {
                        "error": "Your profile is awaiting admin verification.",
                        "next_step": "AWAIT_PROFILE_VERIFICATION",
                    },
                    status=403,
                )
            if not profile.is_approved:
                return JsonResponse(
                    {
                        "error": "Admin approval is required before consultation features are enabled.",
                        "next_step": "AWAIT_CONSULTATION_APPROVAL",
                    },
                    status=403,
                )
        return self.get_response(request)
