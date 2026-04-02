from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models.users import User  # Updated import path
from .models.profiles import DoctorProfile, PatientProfile, TMCProfile  # Updated import path
from consultations.models import (
    DoctorAvailability,
    DoctorSchedule,
    Consultation,
    ConsultationRecord,
    ConsultationChat,
    Prescription,
    Payment,
)  # ✅ Import Consultation Models

# -------------------------------------
# Custom UserAdmin for the User model
# -------------------------------------
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_doctor', 'is_patient', 'is_tmc_operator', 'is_active')
    list_filter = ('is_doctor', 'is_patient', 'is_tmc_operator', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')  # Updated field name
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),  # Updated field name
        ('Roles', {'fields': ('is_doctor', 'is_patient', 'is_tmc_operator')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_doctor', 'is_patient', 'is_tmc_operator', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

# -------------------------------------
# DoctorProfileAdmin for managing doctor profiles
# -------------------------------------
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'qualification', 'specialty', 'license_number', 
        'registration_number', 'hospital_or_clinic_name', 
        'profile_completed', 'admin_verified', 'has_pending_changes', 'is_active', 'created_at'
    )
    list_filter = ('profile_completed', 'admin_verified', 'has_pending_changes', 'is_active', 'specialty', 'created_at')
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name', 
        'qualification', 'specialty', 'license_number', 'registration_number',
        'hospital_or_clinic_name'
    )
    ordering = ('user__email',)
    readonly_fields = ('created_at', 'updated_at', 'admin_verified_at', 'admin_verified_by', 'pending_changes_updated_at', 'completion_percentage_display')
    actions = ['verify_profiles', 'unverify_profiles', 'approve_pending_changes']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_active', 'profile_completed')
        }),
        ('Admin Verification', {
            'fields': ('admin_verified', 'admin_verified_at', 'admin_verified_by', 'has_pending_changes', 'pending_changes_updated_at', 'completion_percentage_display')
        }),
        ('Professional Details', {
            'fields': (
                'qualification', 'specialty', 'experience', 
                'license_number', 'registration_number',
                'hospital_or_clinic_name', 'practice_type'
            )
        }),
        ('Specializations', {
            'fields': ('major_diseases_specializations', 'previous_hospitals_served')
        }),
        ('Documents & Media', {
            'fields': ('photo', 'registration_certificate', 'signature')
        }),
        ('Settings', {
            'fields': ('max_daily_consultations', 'date_of_birth')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def completion_percentage_display(self, obj):
        """Display completion percentage in admin."""
        percentage = obj.get_profile_completion_percentage()
        color = "green" if percentage == 100 else "orange" if percentage >= 50 else "red"
        from django.utils.html import format_html
        return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, percentage)
    completion_percentage_display.short_description = 'Completion %'

    def verify_profiles(self, request, queryset):
        """Admin action to verify selected doctor profiles."""
        from django.utils import timezone
        updated = queryset.update(
            admin_verified=True,
            admin_verified_at=timezone.now(),
            admin_verified_by=request.user
        )
        self.message_user(request, f'{updated} profile(s) verified successfully.')
    verify_profiles.short_description = "Verify selected profiles"

    def unverify_profiles(self, request, queryset):
        """Admin action to unverify selected doctor profiles."""
        updated = queryset.update(
            admin_verified=False,
            admin_verified_at=None,
            admin_verified_by=None
        )
        self.message_user(request, f'{updated} profile(s) unverified.')
    unverify_profiles.short_description = "Unverify selected profiles"
    
    def approve_pending_changes(self, request, queryset):
        """Admin action to approve pending changes and verify profiles."""
        from django.utils import timezone
        updated = queryset.filter(has_pending_changes=True).update(
            admin_verified=True,
            admin_verified_at=timezone.now(),
            admin_verified_by=request.user,
            has_pending_changes=False
        )
        self.message_user(request, f'{updated} profile(s) with pending changes approved and verified.')
    approve_pending_changes.short_description = 'Approve pending changes and verify'

# -------------------------------------
# PatientProfileAdmin for managing patient profiles
# -------------------------------------
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'age', 'address', 'is_active', 'created_at')
    list_filter = ('gender', 'is_active', 'created_at')
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name', 
        'gender', 'address'
    )
    ordering = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_active')
        }),
        ('Personal Details', {
            'fields': ('gender', 'age', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# -------------------------------------
# TMCProfileAdmin for managing TMC operator profiles
# -------------------------------------
class TMCProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'free_consultation_quota', 'free_consultations_used', 
        'free_consultations_remaining', 'is_active', 'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name', 
        'tmc_details'
    )
    ordering = ('user__email',)
    readonly_fields = ('created_at', 'updated_at', 'free_consultations_remaining')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_active')
        }),
        ('TMC Details', {
            'fields': ('tmc_details',)
        }),
        ('Free Consultation Quota', {
            'fields': (
                'free_consultation_quota', 'free_consultations_used', 
                'free_consultations_remaining'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

"""
Note: Consultation-related models are now registered in `consultations/admin.py`
using per-app admin modules. We only need the models imported here for referencing
in user admin if needed, not for registration.
"""

admin.site.register(User, UserAdmin)
admin.site.register(DoctorProfile, DoctorProfileAdmin)
admin.site.register(PatientProfile, PatientProfileAdmin)
admin.site.register(TMCProfile, TMCProfileAdmin)
