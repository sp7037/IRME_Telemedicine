from rest_framework import permissions


def get_owned_tmc_profile(user):
    """Resolve a centre only from an active authenticated operator, never a request ID."""
    if not (
        user and user.is_authenticated and user.is_active
        and getattr(user, "is_tmc_operator", False)
    ):
        return None
    profile = getattr(user, "tmc_profile", None) or getattr(user, "tmcprofile_profile", None)
    return profile if profile and profile.user_id == user.pk else None


class IsStaffUser(permissions.BasePermission):
    """Django admin staff — internal reporting and exports."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_active and u.is_staff)


class FinancialWritePermission(permissions.BasePermission):
    """Apply the admin permission map to the corresponding staff write API."""
    message = "The specific financial permission is required for this action."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        required = getattr(view, "financial_write_permission", None)
        return bool(required and request.user.has_perm(required))
