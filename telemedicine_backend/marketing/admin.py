from django.contrib import admin

from .models import CallbackRequest, MarketingLandingPage


@admin.register(MarketingLandingPage)
class MarketingLandingPageAdmin(admin.ModelAdmin):
    list_display = ("title", "page_type", "state", "city", "slug", "is_active", "priority")
    list_filter = ("page_type", "is_active", "state")
    search_fields = ("title", "h1", "state", "city", "slug", "meta_description")
    prepopulated_fields = {"slug": ("page_type", "state", "city")}
    ordering = ("page_type", "state", "city")


@admin.register(CallbackRequest)
class CallbackRequestAdmin(admin.ModelAdmin):
    list_display = ("created_at", "interest", "name", "phone", "city", "state", "status")
    list_filter = ("interest", "status", "state", "created_at")
    search_fields = ("name", "phone", "email", "city", "state", "message")
    readonly_fields = ("created_at", "updated_at", "source_path")
    ordering = ("-created_at",)

