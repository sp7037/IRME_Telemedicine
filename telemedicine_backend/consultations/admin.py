from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction

from .admin_safety import NoDeleteAdminMixin, ReadOnlyFinancialAdminMixin

from .models import (
    ConsultationFeeSetting,
    DoctorAvailability,
    DoctorSchedule,
    Consultation,
    ConsultationFollowUpSession,
    ConsultationRecord,
    ConsultationChat,
    Prescription,
    PrescriptionVersion,
    Payment,
    ConsultationEvent,
    ConsultationFinance,
    AdminPlatformAccount,
    AdminPlatformEntry,
    PatientWallet,
    PatientWalletEntry,
    PatientWalletRechargeRequest,
    TMCAccount,
    TMCAccountEntry,
    TMCRechargeRequest,
    DoctorEarning,
)


@admin.register(ConsultationFeeSetting)
class ConsultationFeeSettingAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("name", "direct_patient_fee", "tmc_consultation_fee", "platform_fee_percentage", "currency", "is_active", "created_at")
    list_filter = ("is_active", "currency")
    search_fields = ("name",)
    ordering = ("-created_at",)
    readonly_fields = ("created_by", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("doctor", "is_available_online", "is_available_in_clinic", "updated_at")
    search_fields = ("doctor__user__email",)
    ordering = ("doctor__user__email",)


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ("doctor", "day_of_week", "start_time", "end_time", "is_online")
    search_fields = ("doctor__user__email", "day_of_week")
    list_filter = ("day_of_week", "is_online")
    ordering = ("doctor__user__email", "day_of_week", "start_time")


class ConsultationFinanceInline(ReadOnlyFinancialAdminMixin, admin.StackedInline):
    model = ConsultationFinance
    extra = 0
    can_delete = False
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("payment",)


@admin.register(Consultation)
class ConsultationAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = ("id", "doctor", "patient", "tmc", "consultation_type", "status", "is_free", "scheduled_time", "created_at")
    list_filter = ("status", "consultation_type", "is_free", "created_at")
    search_fields = ("doctor__user__email", "patient__user__email", "tmc__user__email")
    ordering = ("-created_at",)
    inlines = (ConsultationFinanceInline,)


@admin.register(ConsultationRecord)
class ConsultationRecordAdmin(admin.ModelAdmin):
    list_display = ("consultation", "video_recording", "created_at")
    search_fields = ("consultation__doctor__user__email", "consultation__patient__user__email")
    ordering = ("-created_at",)


@admin.register(ConsultationChat)
class ConsultationChatAdmin(admin.ModelAdmin):
    list_display = ("consultation", "sender", "message", "timestamp", "is_read")
    search_fields = ("sender__email", "message")
    list_filter = ("is_read",)
    ordering = ("-timestamp",)


@admin.register(ConsultationFollowUpSession)
class ConsultationFollowUpSessionAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = ("id", "consultation", "sequence_number", "status", "is_billable", "amount_charged", "requested_at")
    list_filter = ("status", "is_billable", "requested_at")
    search_fields = ("consultation__id", "consultation__doctor__user__email", "consultation__patient__user__email")
    raw_id_fields = ("consultation", "requested_by", "started_by", "completed_by")
    ordering = ("-requested_at",)


class PrescriptionVersionInline(admin.TabularInline):
    model = PrescriptionVersion
    extra = 0
    can_delete = False
    readonly_fields = ("version_number", "medicines", "instructions", "created_by", "created_at")
    ordering = ("-version_number",)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("consultation", "follow_up_session", "doctor", "patient", "created_at", "updated_at")
    search_fields = ("doctor__user__email", "patient__user__email", "medicines")
    ordering = ("-created_at",)
    inlines = (PrescriptionVersionInline,)


@admin.register(PrescriptionVersion)
class PrescriptionVersionAdmin(admin.ModelAdmin):
    list_display = ("prescription", "version_number", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("prescription__id",)
    raw_id_fields = ("prescription", "created_by")
    ordering = ("-created_at",)


@admin.register(Payment)
class PaymentAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = ("consultation", "amount", "currency", "status", "paid_by_tmc", "created_at")
    list_filter = ("status", "paid_by_tmc", "currency")
    search_fields = ("consultation__id", "consultation__doctor__user__email", "consultation__patient__user__email")
    ordering = ("-created_at",)


@admin.register(ConsultationEvent)
class ConsultationEventAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = ("consultation", "event_type", "actor", "from_status", "to_status", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("consultation__id", "actor__email", "note")
    ordering = ("-created_at",)


@admin.register(ConsultationFinance)
class ConsultationFinanceAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = (
        "consultation", "source_type", "billing_type", "payer_entity", "payment_status",
        "doctor_fee", "platform_fee", "discount_amount", "admin_subsidy_amount", "amount_charged"
    )
    list_filter = ("source_type", "billing_type", "payer_entity", "payment_status")
    search_fields = ("consultation__id", "consultation__doctor__user__email", "consultation__patient__user__email")


@admin.register(AdminPlatformAccount)
class AdminPlatformAccountAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = (
        "name", "balance", "total_credited", "total_debited",
        "total_platform_fees", "total_doctor_subsidies", "updated_at"
    )
    search_fields = ("name",)


@admin.register(AdminPlatformEntry)
class AdminPlatformEntryAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = ("account", "entry_type", "amount", "balance_after", "consultation", "created_at")
    list_filter = ("entry_type",)
    search_fields = ("description", "consultation__id")


@admin.register(PatientWallet)
class PatientWalletAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = ("patient", "balance", "total_credited", "total_debited", "updated_at")
    search_fields = ("patient__user__email",)


@admin.register(PatientWalletEntry)
class PatientWalletEntryAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = ("wallet", "entry_type", "amount", "balance_after", "consultation", "created_at")
    list_filter = ("entry_type",)
    search_fields = ("wallet__patient__user__email", "consultation__id", "description")


class ManualRechargeAdminMixin(ReadOnlyFinancialAdminMixin):
    actions = ("approve_manual_recharges", "reject_manual_recharges")

    def has_process_recharge_permission(self, request):
        opts = self.model._meta
        return bool(
            request.user.is_active and request.user.is_staff
            and request.user.has_perm(f"{opts.app_label}.change_{opts.model_name}")
        )

    def _process_manual_recharges(self, request, queryset, approve):
        if not self.has_process_recharge_permission(request):
            raise PermissionDenied("Recharge processing permission required.")
        from .finance import process_patient_recharge_request, process_tmc_recharge_request

        processor = (process_patient_recharge_request
                     if self.model is PatientWalletRechargeRequest else process_tmc_recharge_request)
        processed_count = 0
        for recharge in queryset.order_by("pk"):
            try:
                with transaction.atomic():
                    processed, _ = processor(
                        recharge, approve=approve, processed_by=request.user,
                        admin_note="Manual recharge decision through Django admin action.",
                    )
                    self.log_change(request, processed, f"Manual recharge {processed.status.lower()} via finance service.")
                processed_count += 1
            except ValueError:
                self.message_user(request, f"Recharge #{recharge.pk} skipped: not pending manual funding.", messages.WARNING)
        self.message_user(request, f"{processed_count} manual recharge request(s) processed.", messages.SUCCESS)

    @admin.action(description="Approve pending manual recharges", permissions=["process_recharge"])
    def approve_manual_recharges(self, request, queryset):
        self._process_manual_recharges(request, queryset, approve=True)

    @admin.action(description="Reject pending manual recharges", permissions=["process_recharge"])
    def reject_manual_recharges(self, request, queryset):
        self._process_manual_recharges(request, queryset, approve=False)


@admin.register(PatientWalletRechargeRequest)
class PatientWalletRechargeRequestAdmin(ManualRechargeAdminMixin, admin.ModelAdmin):
    list_display = ("patient", "amount", "status", "provider", "requested_by", "processed_by", "created_at", "processed_at")
    list_filter = ("status", "provider", "created_at")
    search_fields = ("patient__user__email", "reference_note", "admin_note", "gateway_order_id", "gateway_payment_id")
    raw_id_fields = ("patient", "requested_by", "processed_by")
    ordering = ("-created_at",)



@admin.register(TMCAccount)
class TMCAccountAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = ("tmc", "balance", "total_charged", "total_credited", "total_debited", "updated_at")
    search_fields = ("tmc__user__email",)


@admin.register(TMCAccountEntry)
class TMCAccountEntryAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = ("account", "entry_type", "amount", "balance_after", "consultation", "created_at")
    list_filter = ("entry_type",)
    search_fields = ("account__tmc__user__email", "consultation__id", "description")


@admin.register(TMCRechargeRequest)
class TMCRechargeRequestAdmin(ManualRechargeAdminMixin, admin.ModelAdmin):
    list_display = ("tmc", "amount", "status", "requested_by", "processed_by", "created_at", "processed_at")
    list_filter = ("status", "created_at")
    search_fields = ("tmc__user__email", "reference_note", "admin_note")
    raw_id_fields = ("tmc", "requested_by", "processed_by")
    ordering = ("-created_at",)



@admin.register(DoctorEarning)
class DoctorEarningAdmin(ReadOnlyFinancialAdminMixin, admin.ModelAdmin):
    list_display = ("consultation", "doctor", "source_type", "billing_type", "earning_amount", "status")
    list_filter = ("source_type", "billing_type", "status")
    search_fields = ("doctor__user__email", "consultation__id")
