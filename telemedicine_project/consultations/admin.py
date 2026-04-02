from django.contrib import admin

from .models import (
    DoctorAvailability,
    DoctorSchedule,
    Consultation,
    ConsultationRecord,
    ConsultationChat,
    Prescription,
    Payment,
    ConsultationEvent,
    ConsultationFinance,
    PatientWallet,
    PatientWalletEntry,
    TMCAccount,
    TMCAccountEntry,
    DoctorEarning,
)


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


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "patient", "tmc", "consultation_type", "status", "is_free", "scheduled_time", "created_at")
    list_filter = ("status", "consultation_type", "is_free", "created_at")
    search_fields = ("doctor__user__email", "patient__user__email", "tmc__user__email")
    ordering = ("-created_at",)


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


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("consultation", "doctor", "patient", "created_at")
    search_fields = ("doctor__user__email", "patient__user__email", "medicines")
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
    list_display = ("consultation", "source_type", "billing_type", "payer_entity", "payment_status", "amount_charged")
    list_filter = ("source_type", "billing_type", "payer_entity", "payment_status")
    search_fields = ("consultation__id", "consultation__doctor__user__email", "consultation__patient__user__email")


@admin.register(PatientWallet)
class PatientWalletAdmin(admin.ModelAdmin):
    list_display = ("patient", "balance", "total_credited", "total_debited", "updated_at")
    search_fields = ("patient__user__email",)


@admin.register(PatientWalletEntry)
class PatientWalletEntryAdmin(admin.ModelAdmin):
    list_display = ("wallet", "entry_type", "amount", "balance_after", "consultation", "created_at")
    list_filter = ("entry_type",)
    search_fields = ("wallet__patient__user__email", "consultation__id", "description")


@admin.register(TMCAccount)
class TMCAccountAdmin(admin.ModelAdmin):
    list_display = ("tmc", "balance", "total_charged", "total_credited", "total_debited", "updated_at")
    search_fields = ("tmc__user__email",)


@admin.register(TMCAccountEntry)
class TMCAccountEntryAdmin(admin.ModelAdmin):
    list_display = ("account", "entry_type", "amount", "balance_after", "consultation", "created_at")
    list_filter = ("entry_type",)
    search_fields = ("account__tmc__user__email", "consultation__id", "description")


@admin.register(DoctorEarning)
class DoctorEarningAdmin(admin.ModelAdmin):
    list_display = ("consultation", "doctor", "source_type", "billing_type", "earning_amount", "status")
    list_filter = ("source_type", "billing_type", "status")
    search_fields = ("doctor__user__email", "consultation__id")
