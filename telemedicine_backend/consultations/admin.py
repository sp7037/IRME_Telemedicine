from django.contrib import admin

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
class ConsultationFeeSettingAdmin(admin.ModelAdmin):
    list_display = ("name", "direct_patient_fee", "tmc_consultation_fee", "platform_fee_percentage", "currency", "is_active", "created_at")
    list_filter = ("is_active", "currency")
    search_fields = ("name",)
    ordering = ("-created_at",)


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


class ConsultationFinanceInline(admin.StackedInline):
    model = ConsultationFinance
    extra = 0
    can_delete = False
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("payment",)


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
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
class ConsultationFollowUpSessionAdmin(admin.ModelAdmin):
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
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("consultation", "amount", "currency", "status", "paid_by_tmc", "created_at")
    list_filter = ("status", "paid_by_tmc", "currency")
    search_fields = ("consultation__id", "consultation__doctor__user__email", "consultation__patient__user__email")
    ordering = ("-created_at",)


@admin.register(ConsultationEvent)
class ConsultationEventAdmin(admin.ModelAdmin):
    list_display = ("consultation", "event_type", "actor", "from_status", "to_status", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("consultation__id", "actor__email", "note")
    ordering = ("-created_at",)


@admin.register(ConsultationFinance)
class ConsultationFinanceAdmin(admin.ModelAdmin):
    list_display = (
        "consultation", "source_type", "billing_type", "payer_entity", "payment_status",
        "doctor_fee", "platform_fee", "discount_amount", "admin_subsidy_amount", "amount_charged"
    )
    list_filter = ("source_type", "billing_type", "payer_entity", "payment_status")
    search_fields = ("consultation__id", "consultation__doctor__user__email", "consultation__patient__user__email")


@admin.register(AdminPlatformAccount)
class AdminPlatformAccountAdmin(admin.ModelAdmin):
    list_display = (
        "name", "balance", "total_credited", "total_debited",
        "total_platform_fees", "total_doctor_subsidies", "updated_at"
    )
    search_fields = ("name",)


@admin.register(AdminPlatformEntry)
class AdminPlatformEntryAdmin(admin.ModelAdmin):
    list_display = ("account", "entry_type", "amount", "balance_after", "consultation", "created_at")
    list_filter = ("entry_type",)
    search_fields = ("description", "consultation__id")


@admin.register(PatientWallet)
class PatientWalletAdmin(admin.ModelAdmin):
    list_display = ("patient", "balance", "total_credited", "total_debited", "updated_at")
    search_fields = ("patient__user__email",)


@admin.register(PatientWalletEntry)
class PatientWalletEntryAdmin(admin.ModelAdmin):
    list_display = ("wallet", "entry_type", "amount", "balance_after", "consultation", "created_at")
    list_filter = ("entry_type",)
    search_fields = ("wallet__patient__user__email", "consultation__id", "description")


@admin.register(PatientWalletRechargeRequest)
class PatientWalletRechargeRequestAdmin(admin.ModelAdmin):
    list_display = ("patient", "amount", "status", "provider", "requested_by", "processed_by", "created_at", "processed_at")
    list_filter = ("status", "provider", "created_at")
    search_fields = ("patient__user__email", "reference_note", "admin_note", "gateway_order_id", "gateway_payment_id")
    raw_id_fields = ("patient", "requested_by", "processed_by")
    ordering = ("-created_at",)

    def save_model(self, request, obj, form, change):
        old_status = None
        if change and obj.pk:
            old_status = PatientWalletRechargeRequest.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        super().save_model(request, obj, form, change)
        if obj.status == PatientWalletRechargeRequest.Status.APPROVED and old_status != PatientWalletRechargeRequest.Status.APPROVED:
            from .finance import reconcile_approved_patient_recharges

            reconcile_approved_patient_recharges(obj.patient)


@admin.register(TMCAccount)
class TMCAccountAdmin(admin.ModelAdmin):
    list_display = ("tmc", "balance", "total_charged", "total_credited", "total_debited", "updated_at")
    search_fields = ("tmc__user__email",)


@admin.register(TMCAccountEntry)
class TMCAccountEntryAdmin(admin.ModelAdmin):
    list_display = ("account", "entry_type", "amount", "balance_after", "consultation", "created_at")
    list_filter = ("entry_type",)
    search_fields = ("account__tmc__user__email", "consultation__id", "description")


@admin.register(TMCRechargeRequest)
class TMCRechargeRequestAdmin(admin.ModelAdmin):
    list_display = ("tmc", "amount", "status", "requested_by", "processed_by", "created_at", "processed_at")
    list_filter = ("status", "created_at")
    search_fields = ("tmc__user__email", "reference_note", "admin_note")
    raw_id_fields = ("tmc", "requested_by", "processed_by")
    ordering = ("-created_at",)

    def save_model(self, request, obj, form, change):
        old_status = None
        if change and obj.pk:
            old_status = TMCRechargeRequest.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        super().save_model(request, obj, form, change)
        if obj.status == TMCRechargeRequest.Status.APPROVED and old_status != TMCRechargeRequest.Status.APPROVED:
            from .finance import reconcile_approved_tmc_recharges

            reconcile_approved_tmc_recharges(obj.tmc)


@admin.register(DoctorEarning)
class DoctorEarningAdmin(admin.ModelAdmin):
    list_display = ("consultation", "doctor", "source_type", "billing_type", "earning_amount", "status")
    list_filter = ("source_type", "billing_type", "status")
    search_fields = ("doctor__user__email", "consultation__id")
