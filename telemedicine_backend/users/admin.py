from django.contrib import admin
import logging

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models.users import EmailVerificationOTP, User  # Updated import path
from .models.profiles import (
    DoctorProfile,
    DoctorProfileChangeRequest,
    PatientProfile,
    TMCProfile,
    TMCProfileChangeRequest,
    TMCQualificationChangeRequest,
    TMCQualificationDocument,
)  # Updated import path
from consultations.models import (
    DoctorAvailability,
    DoctorSchedule,
    Consultation,
    ConsultationRecord,
    ConsultationChat,
    Prescription,
    Payment,
)  # ✅ Import Consultation Models

logger = logging.getLogger(__name__)


def _notify_doctor_verified_email(user):
    try:
        from users.email_verification import send_doctor_profile_admin_verified_email

        send_doctor_profile_admin_verified_email(user)
    except Exception:
        logger.exception("Django admin: profile-verified email failed for %s", getattr(user, "email", user))


def _notify_doctor_consultations_approved_email(user):
    try:
        from users.email_verification import send_doctor_consultations_approved_email

        send_doctor_consultations_approved_email(user)
    except Exception:
        logger.exception("Django admin: consultations-approved email failed for %s", getattr(user, "email", user))


def _sync_doctor_pending_after_change_review(doctor):
    """Recompute has_pending_changes after a change request is rejected from the single-object admin."""
    from django.utils import timezone

    has_pending = doctor.change_requests.filter(
        status=DoctorProfileChangeRequest.Status.PENDING
    ).exists()
    doctor.has_pending_changes = has_pending
    doctor.pending_changes_updated_at = timezone.now() if has_pending else None
    doctor.save(update_fields=["has_pending_changes", "pending_changes_updated_at", "updated_at"])


# -------------------------------------
# Custom UserAdmin for the User model
# -------------------------------------
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_doctor', 'is_patient', 'is_tmc_operator', 'is_email_verified', 'is_active')
    list_filter = ('is_doctor', 'is_patient', 'is_tmc_operator', 'is_email_verified', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')  # Updated field name
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),  # Updated field name
        ('Roles', {'fields': ('is_doctor', 'is_patient', 'is_tmc_operator')}),
        ('Verification', {'fields': ('is_email_verified', 'email_verified_at')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_doctor', 'is_patient', 'is_tmc_operator', 'is_email_verified', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

# -------------------------------------
# DoctorProfileAdmin for managing doctor profiles
# -------------------------------------
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'qualification', 'specialty', 'license_number', 
        'registration_number', 'hospital_or_clinic_name', 
        'profile_completed', 'admin_verified', 'is_approved', 'has_pending_changes', 'is_active', 'created_at'
    )
    list_filter = ('profile_completed', 'admin_verified', 'is_approved', 'has_pending_changes', 'is_active', 'specialty', 'created_at')
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name', 
        'qualification', 'specialty', 'license_number', 'registration_number',
        'hospital_or_clinic_name'
    )
    ordering = ('user__email',)
    readonly_fields = ('created_at', 'updated_at', 'admin_verified_at', 'admin_verified_by', 'pending_changes_updated_at', 'completion_percentage_display')
    actions = ['verify_profiles', 'approve_consultations', 'unverify_profiles', 'approve_pending_changes']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_active', 'profile_completed')
        }),
        ('Admin Verification', {
            'fields': ('admin_verified', 'is_approved', 'admin_verified_at', 'admin_verified_by', 'has_pending_changes', 'pending_changes_updated_at', 'completion_percentage_display')
        }),
        ('Professional Details', {
            'fields': (
                'qualification', 'degree', 'college_university_name', 'passing_year',
                'specialty', 'experience', 'license_number', 'registration_number',
                'state_medical_council',
                'hospital_or_clinic_name', 'practice_type'
            )
        }),
        ('Clinic & Consultation', {
            'fields': ('clinic_address_street', 'city', 'state', 'pin_code', 'consultation_modes', 'consultation_fee')
        }),
        ('Specializations', {
            'fields': ('major_diseases_specializations', 'previous_hospitals_served')
        }),
        ('Documents & Media', {
            'fields': ('photo', 'identity_proof', 'registration_certificate', 'signature')
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

    def save_model(self, request, obj, form, change):
        """Send the same notification emails as the staff API when flags change here."""
        old_verified = False
        old_approved = False
        if change and obj.pk:
            row = DoctorProfile.objects.filter(pk=obj.pk).values_list("admin_verified", "is_approved").first()
            if row:
                old_verified, old_approved = row

        super().save_model(request, obj, form, change)

        if not change:
            return

        if not old_verified and obj.admin_verified:
            _notify_doctor_verified_email(obj.user)

        if not old_approved and obj.is_approved and obj.admin_verified:
            _notify_doctor_consultations_approved_email(obj.user)

    def verify_profiles(self, request, queryset):
        """Mark profiles as admin-verified (documents/details). Does not enable consultations."""
        from django.utils import timezone

        newly_verified_ids = list(queryset.filter(admin_verified=False).values_list("pk", flat=True))
        updated = queryset.filter(pk__in=newly_verified_ids).update(
            admin_verified=True,
            admin_verified_at=timezone.now(),
        )
        for pk in newly_verified_ids:
            profile = DoctorProfile.objects.select_related("user").filter(pk=pk).first()
            if profile:
                _notify_doctor_verified_email(profile.user)
        self.message_user(request, f"{updated} profile(s) marked verified.")
    verify_profiles.short_description = "Verify selected profiles (profile only)"

    def approve_consultations(self, request, queryset):
        """Allow verified doctors to receive consultations."""
        total = queryset.count()
        newly_approved_ids = list(
            queryset.filter(admin_verified=True, is_approved=False).values_list("pk", flat=True)
        )
        updated = queryset.filter(pk__in=newly_approved_ids).update(is_approved=True)
        skipped = total - len(newly_approved_ids)
        for pk in newly_approved_ids:
            profile = DoctorProfile.objects.select_related("user").filter(pk=pk).first()
            if profile:
                _notify_doctor_consultations_approved_email(profile.user)
        self.message_user(
            request,
            f"{updated} doctor(s) approved for consultations."
            + (f" {skipped} skipped (not profile-verified or already approved)." if skipped else ""),
        )
    approve_consultations.short_description = "Approve consultations (verified profiles only)"

    def unverify_profiles(self, request, queryset):
        """Admin action to unverify selected doctor profiles."""
        updated = queryset.update(
            admin_verified=False,
            is_approved=False,
            admin_verified_at=None,
            admin_verified_by=None
        )
        self.message_user(request, f'{updated} profile(s) unverified.')
    unverify_profiles.short_description = "Unverify selected profiles"
    
    def approve_pending_changes(self, request, queryset):
        """Admin action to approve pending changes and verify profiles."""
        updated = 0
        for profile in queryset.filter(has_pending_changes=True):
            change_request = profile.change_requests.filter(
                status=DoctorProfileChangeRequest.Status.PENDING
            ).order_by("-requested_at").first()
            if change_request:
                change_request.apply_to_profile(reviewed_by=request.user)
                updated += 1
        self.message_user(request, f'{updated} profile change request(s) approved and applied.')
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
        'user', 'clinic_name', 'city', 'state', 'profile_completed', 'admin_verified',
        'is_approved', 'has_pending_changes', 'free_consultation_quota', 'free_consultations_used',
        'discount_percentage', 'discounted_consultation_quota', 'discounted_consultations_used',
        'is_active', 'created_at'
    )
    list_filter = ('is_active', 'profile_completed', 'admin_verified', 'is_approved', 'has_pending_changes', 'state', 'created_at')
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name', 
        'tmc_details', 'clinic_name', 'city', 'state', 'pin_code'
    )
    ordering = ('user__email',)
    readonly_fields = ('created_at', 'updated_at', 'free_consultations_remaining')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_active')
        }),
        ('TMC Details', {
            'fields': (
                'tmc_details', 'clinic_name', 'clinic_address_street', 'city', 'state',
                'pin_code', 'aadhaar_document', 'user_photo', 'clinic_front_photo',
                'profile_completed', 'admin_verified', 'is_approved',
                'has_pending_changes', 'pending_changes_updated_at'
            )
        }),
        ('Free Consultation Quota', {
            'fields': (
                'free_consultation_quota', 'free_consultations_used', 
                'free_consultations_remaining'
            )
        }),
        ('Discounted Consultation Quota', {
            'fields': (
                'discount_percentage', 'discounted_consultation_quota',
                'discounted_consultations_used'
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


@admin.register(TMCQualificationDocument)
class TMCQualificationDocumentAdmin(admin.ModelAdmin):
    list_display = ("tmc", "exam_name", "board_or_university", "percentage", "created_at")
    list_filter = ("exam_name", "created_at")
    search_fields = ("tmc__user__email", "board_or_university")
    raw_id_fields = ("tmc",)


@admin.register(TMCProfileChangeRequest)
class TMCProfileChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("tmc", "requested_by", "status", "requested_at", "reviewed_at", "reviewed_by")
    list_filter = ("status", "requested_at")
    search_fields = ("tmc__user__email", "tmc__clinic_name")
    readonly_fields = ("requested_at", "reviewed_at", "reviewed_by")
    actions = ("approve_selected_requests", "reject_selected_requests")

    def save_model(self, request, obj, form, change):
        old_status = None
        if change and obj.pk:
            old_status = TMCProfileChangeRequest.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        super().save_model(request, obj, form, change)
        if change and obj.status == TMCProfileChangeRequest.Status.APPROVED and old_status != obj.status:
            obj.apply_to_profile(reviewed_by=request.user, admin_note=obj.admin_note)

    def approve_selected_requests(self, request, queryset):
        for obj in queryset.filter(status=TMCProfileChangeRequest.Status.PENDING):
            obj.apply_to_profile(reviewed_by=request.user, admin_note="Approved from admin bulk action.")

    def reject_selected_requests(self, request, queryset):
        from django.utils import timezone

        queryset.filter(status=TMCProfileChangeRequest.Status.PENDING).update(
            status=TMCProfileChangeRequest.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            admin_note="Rejected from admin bulk action.",
        )


@admin.register(TMCQualificationChangeRequest)
class TMCQualificationChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("tmc", "action", "target_document", "status", "requested_at", "reviewed_at", "reviewed_by")
    list_filter = ("status", "action", "requested_at")
    search_fields = ("tmc__user__email", "tmc__clinic_name", "board_or_university")
    readonly_fields = ("requested_at", "reviewed_at", "reviewed_by")
    actions = ("approve_selected_requests", "reject_selected_requests")

    def save_model(self, request, obj, form, change):
        old_status = None
        if change and obj.pk:
            old_status = TMCQualificationChangeRequest.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        super().save_model(request, obj, form, change)
        if change and obj.status == TMCQualificationChangeRequest.Status.APPROVED and old_status != obj.status:
            obj.apply(reviewed_by=request.user, admin_note=obj.admin_note)

    def approve_selected_requests(self, request, queryset):
        for obj in queryset.filter(status=TMCQualificationChangeRequest.Status.PENDING):
            obj.apply(reviewed_by=request.user, admin_note="Approved from admin bulk action.")

    def reject_selected_requests(self, request, queryset):
        from django.utils import timezone

        queryset.filter(status=TMCQualificationChangeRequest.Status.PENDING).update(
            status=TMCQualificationChangeRequest.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            admin_note="Rejected from admin bulk action.",
        )


@admin.register(DoctorProfileChangeRequest)
class DoctorProfileChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("doctor", "requested_by", "status", "requested_at", "reviewed_at", "reviewed_by")
    list_filter = ("status", "requested_at", "reviewed_at")
    search_fields = ("doctor__user__email", "doctor__user__first_name", "doctor__user__last_name")
    readonly_fields = ("requested_at", "reviewed_at", "reviewed_by")
    actions = ("approve_selected_requests", "reject_selected_requests")

    def save_model(self, request, obj, form, change):
        """Applying proposals must run when staff sets status to Approved (not only via bulk actions)."""
        old_status = None
        if change and obj.pk:
            old_status = DoctorProfileChangeRequest.objects.filter(pk=obj.pk).values_list("status", flat=True).first()

        super().save_model(request, obj, form, change)

        if not change:
            return

        obj.refresh_from_db()

        if old_status != DoctorProfileChangeRequest.Status.PENDING:
            return

        if obj.status == DoctorProfileChangeRequest.Status.APPROVED:
            obj.apply_to_profile(reviewed_by=request.user, admin_note=obj.admin_note)
        elif obj.status == DoctorProfileChangeRequest.Status.REJECTED:
            from django.utils import timezone

            DoctorProfileChangeRequest.objects.filter(pk=obj.pk).update(
                reviewed_by=request.user,
                reviewed_at=timezone.now(),
            )
            obj.refresh_from_db()
            _sync_doctor_pending_after_change_review(obj.doctor)

    def approve_selected_requests(self, request, queryset):
        updated = 0
        for change_request in queryset.filter(status=DoctorProfileChangeRequest.Status.PENDING):
            change_request.apply_to_profile(reviewed_by=request.user)
            updated += 1
        self.message_user(request, f"{updated} pending doctor profile change request(s) approved.")
    approve_selected_requests.short_description = "Approve selected pending requests"

    def reject_selected_requests(self, request, queryset):
        from django.utils import timezone

        updated = queryset.filter(status=DoctorProfileChangeRequest.Status.PENDING).update(
            status=DoctorProfileChangeRequest.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            admin_note="Rejected from Django admin action.",
        )
        doctor_ids = queryset.values_list("doctor_id", flat=True).distinct()
        for doctor in DoctorProfile.objects.filter(id__in=doctor_ids):
            has_pending = doctor.change_requests.filter(status=DoctorProfileChangeRequest.Status.PENDING).exists()
            doctor.has_pending_changes = has_pending
            doctor.pending_changes_updated_at = timezone.now() if has_pending else None
            doctor.save(update_fields=["has_pending_changes", "pending_changes_updated_at", "updated_at"])
        self.message_user(request, f"{updated} pending doctor profile change request(s) rejected.")
    reject_selected_requests.short_description = "Reject selected pending requests"


@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "expires_at", "attempts", "consumed_at", "created_at")
    list_filter = ("purpose", "consumed_at", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("otp_hash", "created_at")
