from rest_framework import permissions


class IsStaffUser(permissions.BasePermission):
    """Django admin staff — internal reporting and exports."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_staff)
