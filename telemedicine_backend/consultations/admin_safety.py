"""Admin boundaries for financial evidence; postings belong to finance services."""
from django.core.exceptions import PermissionDenied


class NoDeleteAdminMixin:
    """Also cover ancestors whose deletion would cascade into financial evidence."""

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def delete_model(self, request, obj):
        raise PermissionDenied("Financial history must be retained. Deactivate accounts instead.")

    def delete_queryset(self, request, queryset):
        raise PermissionDenied("Financial history must be retained. Deactivate accounts instead.")


class ReadOnlyFinancialAdminMixin(NoDeleteAdminMixin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields) + tuple(
            field.name for field in self.model._meta.many_to_many
        )

    def save_model(self, request, obj, form, change):
        raise PermissionDenied("Use the authorised financial or consultation workflow.")


class FinancialOwnerAdminMixin(NoDeleteAdminMixin):
    def get_readonly_fields(self, request, obj=None):
        fields = tuple(super().get_readonly_fields(request, obj))
        return fields + (("user",) if obj else ())
