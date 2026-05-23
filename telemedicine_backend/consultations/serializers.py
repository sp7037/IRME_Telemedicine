import re
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from .models import (
    DoctorAvailability,
    DoctorSchedule,
    Consultation,
    ConsultationFollowUpSession,
    ConsultationChat,
    Prescription,
    PrescriptionVersion,
    Payment,
    ConsultationEvent,
    PatientWallet,
    TMCAccount,
)
from users.models import DoctorProfile, DoctorProfileChangeRequest, PatientProfile, TMCProfile
from .finance import (
    InsufficientBalanceError,
    calculate_platform_fee,
    create_consultation_finance,
    estimate_tmc_consultation_pricing,
    normalize_money,
    resolve_doctor_consultation_amount,
)
from .video import video_state_for_consultation

OPEN_CONSULTATION_STATUSES = [
    Consultation.StatusChoices.PENDING,
    Consultation.StatusChoices.ACCEPTED,
    Consultation.StatusChoices.QUEUED,
    Consultation.StatusChoices.POSTPONED,
    Consultation.StatusChoices.IN_PROGRESS,
]
SAME_DOCTOR_REBOOKING_GAP_MINUTES = 10

# ✅ Serializer for DoctorSchedule (Time Slots)
class DoctorScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSchedule
        fields = [
            'id',
            'day_of_week',
            'start_time',
            'end_time',
            'is_online',
            'consultation_duration_minutes',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, attrs):
        start_time = attrs.get("start_time") or getattr(self.instance, "start_time", None)
        end_time = attrs.get("end_time") or getattr(self.instance, "end_time", None)
        day_of_week = attrs.get("day_of_week") or getattr(self.instance, "day_of_week", None)
        is_online = attrs.get("is_online", getattr(self.instance, "is_online", True))
        is_active = attrs.get("is_active", getattr(self.instance, "is_active", True))
        duration = attrs.get(
            "consultation_duration_minutes",
            getattr(self.instance, "consultation_duration_minutes", 15),
        )

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        if duration and (duration < 5 or duration > 180):
            raise serializers.ValidationError(
                {"consultation_duration_minutes": "Duration must be between 5 and 180 minutes."}
            )

        request = self.context.get("request")
        doctor = getattr(getattr(request, "user", None), "doctor_profile", None)
        if doctor and is_active and day_of_week and start_time and end_time:
            overlaps = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=day_of_week,
                is_online=is_online,
                is_active=True,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
            if self.instance:
                overlaps = overlaps.exclude(pk=self.instance.pk)
            if overlaps.exists():
                raise serializers.ValidationError(
                    {"non_field_errors": ["Schedule overlaps with an existing slot."]}
                )
        return attrs

# ✅ Serializer for DoctorAvailability (General Availability)
class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(read_only=True)  # ✅ Auto-set doctor, remove from request

    class Meta:
        model = DoctorAvailability
        fields = ['id', 'doctor', 'is_available_online', 'is_available_in_clinic', 
                  'next_available_online', 'next_available_in_clinic', 'updated_at']
#========================================
# Serializers for consultation booking & listing
#========================================

class ConsultationSerializer(serializers.ModelSerializer):
    """Basic consultation serializer for generic listing/detail."""

    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    doctor = serializers.PrimaryKeyRelatedField(queryset=DoctorProfile.objects.all())

    class Meta:
        model = Consultation
        fields = [
            'id',
            'patient',
            'doctor',
            'tmc',
            'consultation_type',
            'scheduled_time',
            'status',
            'is_completed',
            'is_free',
        ]
        read_only_fields = ['status', 'is_completed', 'is_free']


class ConsultationBookingSerializer(serializers.Serializer):
    """
    Serializer used specifically for booking a new consultation.

    - Validates doctor existence & basic availability.
    - Validates that the authenticated user has a patient profile.
    - Handles TMC free-quota and Payment creation logic.
    """

    doctor_id = serializers.IntegerField()
    consultation_type = serializers.ChoiceField(
        choices=Consultation.ConsultationType.choices,
        default=Consultation.ConsultationType.DIRECT,
    )
    scheduled_time = serializers.DateTimeField(required=False)
    tmc_id = serializers.IntegerField(required=False, allow_null=True)

    # Optional amount for paid consultations (if not free)
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        # Ensure user has a patient profile
        if not hasattr(user, "patient_profile"):
            raise serializers.ValidationError(
                {"patient": "Authenticated user does not have a patient profile."}
            )

        # Resolve doctor
        try:
            doctor = DoctorProfile.objects.get(id=attrs["doctor_id"])
        except DoctorProfile.DoesNotExist:
            raise serializers.ValidationError({"doctor_id": "Invalid doctor ID."})
        if not (
            doctor.profile_completed
            and doctor.admin_verified
            and doctor.is_approved
            and doctor.user.is_email_verified
        ):
            raise serializers.ValidationError({"doctor": "Doctor is not approved for consultations yet."})

        attrs["doctor"] = doctor
        attrs["patient_profile"] = user.patient_profile

        open_consultation = Consultation.objects.filter(
            patient=user.patient_profile,
            status__in=OPEN_CONSULTATION_STATUSES,
        ).select_related("doctor__user").order_by("-created_at").first()
        if open_consultation:
            doctor_name = open_consultation.doctor.user.get_full_name() or open_consultation.doctor.user.email
            raise serializers.ValidationError(
                {
                    "consultation": (
                        f"You already have an uncompleted consultation with Dr. {doctor_name}. "
                        "Please complete or cancel it before requesting another consultation."
                    )
                }
            )

        recent_same_doctor = Consultation.objects.filter(
            patient=user.patient_profile,
            doctor=doctor,
            created_at__gte=timezone.now() - timedelta(minutes=SAME_DOCTOR_REBOOKING_GAP_MINUTES),
        ).filter(
            Q(status=Consultation.StatusChoices.COMPLETED)
            | Q(status=Consultation.StatusChoices.CANCELED)
            | Q(status=Consultation.StatusChoices.REJECTED)
            | Q(status=Consultation.StatusChoices.REJECTED_BY_PATIENT)
        ).order_by("-created_at").first()
        if recent_same_doctor:
            wait_until = recent_same_doctor.created_at + timedelta(minutes=SAME_DOCTOR_REBOOKING_GAP_MINUTES)
            remaining = max(1, int((wait_until - timezone.now()).total_seconds() // 60) + 1)
            raise serializers.ValidationError(
                {
                    "consultation": (
                        f"Please wait about {remaining} minute(s) before requesting another consultation "
                        "with the same doctor."
                    )
                }
            )

        if attrs.get("consultation_type") == Consultation.ConsultationType.DIRECT:
            fee = normalize_money(
                resolve_doctor_consultation_amount(
                    Consultation.ConsultationType.DIRECT,
                    doctor=doctor,
                    amount=attrs.get("amount"),
                )
            )
            attrs["resolved_amount"] = fee
            payable = normalize_money(fee + calculate_platform_fee(fee))
            if payable > 0:
                wallet = PatientWallet.objects.filter(patient=user.patient_profile).first()
                bal = normalize_money(wallet.balance if wallet else Decimal("0"))
                if bal < payable:
                    raise serializers.ValidationError(
                        {
                            "wallet": (
                                f"Insufficient wallet balance. This consultation requires Rs {payable}; "
                                f"your balance is Rs {bal}. Please ask an administrator to credit your wallet, then try again."
                            )
                        }
                    )

        # Resolve TMC when provided
        tmc = None
        if attrs.get("consultation_type") == Consultation.ConsultationType.TMC:
            tmc_id = attrs.get("tmc_id")
            if not tmc_id:
                raise serializers.ValidationError(
                    {"tmc_id": "tmc_id is required for TMC consultations."}
                )
            try:
                tmc = TMCProfile.objects.get(id=tmc_id)
            except TMCProfile.DoesNotExist:
                raise serializers.ValidationError({"tmc_id": "Invalid TMC ID."})
            fee = normalize_money(
                resolve_doctor_consultation_amount(
                    Consultation.ConsultationType.TMC,
                    doctor=doctor,
                    amount=attrs.get("amount"),
                )
            )
            attrs["resolved_amount"] = fee
            pricing = estimate_tmc_consultation_pricing(tmc, fee)
            if pricing["amount_charged"] > 0:
                account = TMCAccount.objects.filter(tmc=tmc).first()
                bal = normalize_money(account.balance if account else Decimal("0"))
                if bal < pricing["amount_charged"]:
                    raise serializers.ValidationError(
                        {
                            "wallet": (
                                f"Insufficient TMC wallet balance. This consultation requires Rs {pricing['amount_charged']}; "
                                f"available TMC wallet balance is Rs {bal}. Please recharge the TMC wallet first."
                            )
                        }
                    )
        attrs["tmc_profile"] = tmc

        # Determine scheduled time
        scheduled_time = attrs.get("scheduled_time")
        if not scheduled_time:
            scheduled_time = timezone.now() + timezone.timedelta(minutes=10)
        else:
            # Ensure timezone-aware
            if timezone.is_naive(scheduled_time):
                scheduled_time = timezone.make_aware(scheduled_time, timezone.get_current_timezone())
        attrs["scheduled_time"] = scheduled_time

        # Basic doctor availability check
        doctor = attrs["doctor"]

        availability_ok = ConsultationBookingSerializer._doctor_is_available(doctor, scheduled_time)
        if not availability_ok:
            # Try fallback doctor
            fallback = ConsultationBookingSerializer._find_fallback_doctor(doctor, scheduled_time)
            if fallback:
                attrs["doctor"] = fallback
            else:
                raise serializers.ValidationError(
                    {"doctor": "Selected doctor is unavailable at the requested time."}
                )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        doctor: DoctorProfile = validated_data["doctor"]
        patient_profile: PatientProfile = validated_data["patient_profile"]
        tmc: TMCProfile | None = validated_data.get("tmc_profile")
        consultation_type = validated_data["consultation_type"]
        scheduled_time = validated_data["scheduled_time"]
        amount = normalize_money(
            validated_data.get("resolved_amount")
            or resolve_doctor_consultation_amount(
                consultation_type,
                doctor=doctor,
                amount=validated_data.get("amount"),
            )
        )

        is_free = False
        payment = None

        try:
            with transaction.atomic():
                # TMC quota & payment logic
                if consultation_type == Consultation.ConsultationType.TMC and tmc:
                    if tmc.free_consultations_remaining > 0:
                        is_free = True
                        tmc.free_consultations_used += 1
                        tmc.save(update_fields=["free_consultations_used"])

                consultation = Consultation.objects.create(
                    patient=patient_profile,
                    doctor=doctor,
                    tmc=tmc,
                    consultation_type=consultation_type,
                    scheduled_time=scheduled_time,
                    status=Consultation.StatusChoices.PENDING,
                    is_free=is_free,
                )

                if amount > 0 and not is_free:
                    payment = Payment.objects.create(
                        consultation=consultation,
                        amount=amount,
                        status=Payment.Status.PENDING,
                        paid_by_tmc=consultation_type == Consultation.ConsultationType.TMC,
                    )

                create_consultation_finance(
                    consultation=consultation,
                    payment=payment,
                    amount=amount,
                )
        except InsufficientBalanceError as exc:
            raise serializers.ValidationError({"wallet": str(exc)})

        validated_data["consultation"] = consultation
        validated_data["payment"] = payment
        return consultation

    # ------------------------
    # Helper methods
    # ------------------------

    @staticmethod
    def _doctor_is_available(doctor: DoctorProfile, scheduled_time):
        availability = getattr(doctor, "availability", None)
        if availability and not availability.is_available_online:
            return False

        local_dt = timezone.localtime(scheduled_time)
        scheduled_day = local_dt.strftime("%A")
        scheduled_clock = local_dt.time()
        schedules = DoctorSchedule.objects.filter(
            doctor=doctor,
            day_of_week=scheduled_day,
            is_online=True,
            is_active=True,
        )
        if schedules.exists() and not schedules.filter(
            start_time__lte=scheduled_clock,
            end_time__gt=scheduled_clock,
        ).exists():
            return False
        schedule = schedules.filter(
            start_time__lte=scheduled_clock,
            end_time__gt=scheduled_clock,
        ).order_by("start_time").first()
        duration = schedule.consultation_duration_minutes if schedule else 15
        if schedule:
            consultation_end = datetime.combine(local_dt.date(), scheduled_clock) + timedelta(minutes=duration)
            schedule_end = datetime.combine(local_dt.date(), schedule.end_time)
            if consultation_end > schedule_end:
                return False

        # Daily limit
        max_per_day = doctor.max_daily_consultations
        day_start = scheduled_time.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        todays_count = Consultation.objects.filter(
            doctor=doctor,
            scheduled_time__gte=day_start,
            scheduled_time__lt=day_end,
        ).exclude(
            status__in=[
                Consultation.StatusChoices.CANCELED,
                Consultation.StatusChoices.REJECTED,
            ]
        ).count()
        if todays_count >= max_per_day:
            return False

        # Conflicting slot
        conflict_start = scheduled_time - timedelta(minutes=duration)
        conflict_end = scheduled_time + timedelta(minutes=duration)
        conflict = Consultation.objects.filter(
            doctor=doctor,
            scheduled_time__gt=conflict_start,
            scheduled_time__lt=conflict_end,
            status__in=[
                Consultation.StatusChoices.PENDING,
                Consultation.StatusChoices.ACCEPTED,
                Consultation.StatusChoices.QUEUED,
                Consultation.StatusChoices.POSTPONED,
            ],
        ).exists()
        if conflict:
            return False

        return True

    @staticmethod
    def _find_fallback_doctor(original_doctor: DoctorProfile, scheduled_time):
        """Attempt to find another doctor in same specialty who is available."""
        specialty = original_doctor.specialty
        candidates = DoctorProfile.objects.exclude(id=original_doctor.id)
        if specialty:
            candidates = candidates.filter(specialty=specialty)

        for doctor in candidates:
            if ConsultationBookingSerializer._doctor_is_available(doctor, scheduled_time):
                return doctor
        return None


#=========================================
# COnsultation History serializer
#=========================================

class ConsultationHistorySerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()  # ✅ Fetch Doctor's Full Name
    doctor = serializers.SerializerMethodField()  # ✅ Include doctor ID for matching
    patient_name = serializers.SerializerMethodField()  # ✅ Fetch Patient's Full Name
    patient_email = serializers.SerializerMethodField()
    patient_phone = serializers.SerializerMethodField()
    formatted_time = serializers.SerializerMethodField()  # ✅ Format Date & Time
    formatted_suggested_time = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    queue_number = serializers.IntegerField(read_only=True)
    estimated_waiting_time = serializers.SerializerMethodField()  # ✅ Estimated waiting time in minutes
    tmc_name = serializers.SerializerMethodField()
    consultation_label = serializers.SerializerMethodField()
    billing_type = serializers.SerializerMethodField()
    amount_charged = serializers.SerializerMethodField()
    doctor_fee = serializers.SerializerMethodField()
    platform_fee = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    admin_subsidy_amount = serializers.SerializerMethodField()
    follow_up = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = [
            'id', 'doctor', 'doctor_name', 'patient_name', 'patient_email', 'patient_phone',
            'consultation_type', 'formatted_time', 'formatted_suggested_time',
            'status', 'is_completed', 'is_free', 'scheduled_time', 'new_suggested_time',
            'created_at', 'created_at_formatted', 'queue_number', 'estimated_waiting_time',
            'tmc_name', 'consultation_label', 'billing_type', 'amount_charged',
            'doctor_fee', 'platform_fee', 'discount_amount', 'admin_subsidy_amount', 'follow_up',
            'video'
        ]
    
    def get_doctor(self, obj):
        """Return doctor ID for matching."""
        return obj.doctor.id

    def get_doctor_name(self, obj):
        return f"{obj.doctor.user.first_name} {obj.doctor.user.last_name}"

    def get_patient_name(self, obj):
        return f"{obj.patient.user.first_name} {obj.patient.user.last_name}"
    
    def get_patient_email(self, obj):
        return obj.patient.user.email
    
    def get_patient_phone(self, obj):
        return obj.patient.user.phone_number

    def get_formatted_time(self, obj):
        return obj.scheduled_time.strftime("%d-%b-%Y %I:%M %p") if obj.scheduled_time else None
    
    def get_formatted_suggested_time(self, obj):
        return obj.new_suggested_time.strftime("%d-%b-%Y %I:%M %p") if obj.new_suggested_time else None
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime("%d-%b-%Y %I:%M %p") if obj.created_at else None
    
    def get_estimated_waiting_time(self, obj):
        """Calculate estimated waiting time based on queue position (5 minutes per consultation)."""
        from .models import Consultation
        if obj.status == Consultation.StatusChoices.QUEUED and obj.queue_number:
            # Each consultation takes approximately 5 minutes
            return (obj.queue_number - 1) * 5  # Waiting time for people ahead
        return None

    def get_tmc_name(self, obj):
        if obj.tmc:
            return obj.tmc.user.get_full_name() or obj.tmc.user.email
        return None

    def get_consultation_label(self, obj):
        if obj.status == Consultation.StatusChoices.QUEUED and obj.queue_number:
            return f"In queue (#{obj.queue_number})"
        if obj.status == Consultation.StatusChoices.IN_PROGRESS:
            return "Consultation is live"
        return obj.get_status_display()

    def get_billing_type(self, obj):
        if hasattr(obj, "finance"):
            return obj.finance.billing_type
        return "FREE" if obj.is_free else "PAID"

    def get_amount_charged(self, obj):
        if hasattr(obj, "finance"):
            return str(obj.finance.amount_charged)
        payment = getattr(obj, "payment", None)
        if payment:
            return str(payment.amount)
        return "0.00"

    def get_doctor_fee(self, obj):
        if hasattr(obj, "finance"):
            return str(obj.finance.doctor_fee)
        return self.get_amount_charged(obj)

    def get_platform_fee(self, obj):
        if hasattr(obj, "finance"):
            return str(obj.finance.platform_fee)
        return "0.00"

    def get_discount_amount(self, obj):
        if hasattr(obj, "finance"):
            return str(obj.finance.discount_amount)
        return "0.00"

    def get_admin_subsidy_amount(self, obj):
        if hasattr(obj, "finance"):
            return str(obj.finance.admin_subsidy_amount)
        return "0.00"

    def get_follow_up(self, obj):
        sessions = list(getattr(obj, "_prefetched_objects_cache", {}).get("follow_up_sessions", []))
        if not sessions:
            sessions = list(obj.follow_up_sessions.order_by("-requested_at")[:20])
        active = next((s for s in sessions if s.status in [
            ConsultationFollowUpSession.Status.PENDING,
            ConsultationFollowUpSession.Status.IN_PROGRESS,
        ]), None)
        completed = [s for s in sessions if s.status == ConsultationFollowUpSession.Status.COMPLETED]
        first_completed_event = obj.events.filter(
            event_type=ConsultationEvent.EventType.COMPLETED
        ).order_by("created_at").first()
        base_completed_at = first_completed_event.created_at if first_completed_event else obj.updated_at
        free_deadline = base_completed_at + timedelta(days=5) if base_completed_at else None
        completed_in_window = [
            s for s in completed
            if free_deadline and s.requested_at and s.requested_at <= free_deadline and not s.is_billable
        ]
        free_remaining = max(0, 3 - len(completed_in_window))
        next_is_billable = not (
            obj.status == Consultation.StatusChoices.COMPLETED
            and free_deadline
            and timezone.now() <= free_deadline
            and free_remaining > 0
        )
        return {
            "active_session_id": active.id if active else None,
            "active_status": active.status if active else None,
            "active_sequence_number": active.sequence_number if active else None,
            "free_remaining": free_remaining,
            "free_deadline": free_deadline,
            "next_is_billable": next_is_billable,
            "last_amount_charged": str(active.amount_charged) if active else "0.00",
            "can_request": obj.status == Consultation.StatusChoices.COMPLETED and active is None,
        }

    def get_video(self, obj):
        return video_state_for_consultation(obj)

#===================================================================
# Mark consultation status complete by doctor and cancel by patient
#===================================================================

class ConsultationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer used for updating status / suggested time.
    Validation of who can change what is enforced in the views.
    """

    class Meta:
        model = Consultation
        fields = ['status', 'new_suggested_time']
        
#======================================
# Chat history serializers
#======================================
from consultations.models import ConsultationChat

class ConsultationChatSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.email')  # ✅ Show sender's email instead of ID
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    sender_name = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()
    is_prescription = serializers.SerializerMethodField()
    prescription_data = serializers.SerializerMethodField()

    class Meta:
        model = ConsultationChat
        # Include attachment fields only if they exist in model
        fields = ['id', 'message', 'sender', 'sender_id', 'sender_name', 'timestamp', 'is_read']
        # Will add attachment fields after migration
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add attachment fields if they exist in the model
        if hasattr(ConsultationChat, 'attachment'):
            if 'attachment' not in self.Meta.fields:
                self.Meta.fields = list(self.Meta.fields) + ['attachment', 'attachment_type', 'attachment_url']
        # Add prescription fields
        if 'is_prescription' not in self.Meta.fields:
            self.Meta.fields = list(self.Meta.fields) + ['is_prescription', 'prescription_data']
    
    def get_sender_name(self, obj):
        """Return sender's full name if available"""
        if hasattr(obj.sender, 'first_name') and hasattr(obj.sender, 'last_name'):
            return f"{obj.sender.first_name} {obj.sender.last_name}".strip()
        return obj.sender.email
    
    def get_attachment_url(self, obj):
        """Return full URL for attachment if it exists"""
        if hasattr(obj, 'attachment') and obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None

    def get_is_prescription(self, obj):
        """Check if this message is a prescription marker"""
        return obj.message and (
            obj.message.startswith("PRESCRIPTION:")
            or obj.message.startswith("PRESCRIPTION_RX:")
        )

    def get_prescription_data(self, obj):
        """If this is a prescription message, fetch the prescription data"""
        if self.get_is_prescription(obj):
            try:
                marker = re.match(r"^PRESCRIPTION_RX:(\d+):", obj.message or "")
                if marker:
                    prescription = Prescription.objects.filter(
                        consultation=obj.consultation,
                        id=int(marker.group(1)),
                    ).first()
                else:
                    prescription = Prescription.objects.filter(consultation=obj.consultation).order_by("-updated_at", "-id").first()
                if not prescription:
                    return None
                serializer = PrescriptionSerializer(prescription, context=self.context)
                return serializer.data
            except Prescription.DoesNotExist:
                return None
        return None

class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending messages"""
    message = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    attachment = serializers.FileField(required=False)

#======================================
# ---Prescription serializers---
#======================================

class PrescriptionSerializer(serializers.ModelSerializer):
    doctor = serializers.CharField(source="doctor.user.email", read_only=True)
    doctor_name = serializers.SerializerMethodField()
    doctor_qualification = serializers.CharField(source="doctor.qualification", read_only=True)
    doctor_license_number = serializers.CharField(source="doctor.license_number", read_only=True)
    doctor_city = serializers.CharField(source="doctor.city", read_only=True)
    doctor_state = serializers.CharField(source="doctor.state", read_only=True)
    patient = serializers.CharField(source="patient.user.email", read_only=True)
    patient_name = serializers.SerializerMethodField()
    consultation_id = serializers.IntegerField(source="consultation.id", read_only=True)
    follow_up_session_id = serializers.IntegerField(source="follow_up_session.id", read_only=True)
    version_row_count = serializers.SerializerMethodField()
    edit_deadline = serializers.SerializerMethodField()
    can_edit_current = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            "id", "consultation_id", "consultation", "doctor", "doctor_name",
            "doctor_qualification", "doctor_license_number", "doctor_city", "doctor_state",
            "patient", "patient_name", "follow_up_session_id", "medicines", "instructions", "created_at",
            "updated_at", "version_row_count", "edit_deadline", "can_edit_current",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "version_row_count", "edit_deadline", "can_edit_current"]

    def get_doctor_name(self, obj):
        return f"{obj.doctor.user.first_name} {obj.doctor.user.last_name}".strip()

    def get_patient_name(self, obj):
        return f"{obj.patient.user.first_name} {obj.patient.user.last_name}".strip()

    def get_version_row_count(self, obj):
        return obj.versions.count()

    def get_edit_deadline(self, obj):
        return obj.updated_at + timezone.timedelta(minutes=30) if obj.updated_at else None

    def get_can_edit_current(self, obj):
        deadline = self.get_edit_deadline(obj)
        return bool(deadline and timezone.now() <= deadline)


class PrescriptionVersionSerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)

    class Meta:
        model = PrescriptionVersion
        fields = [
            "id",
            "version_number",
            "medicines",
            "instructions",
            "created_by_email",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "version_number",
            "medicines",
            "instructions",
            "created_by_email",
            "created_at",
        ]


_EVENT_HIGHLIGHT = frozenset(
    {
        ConsultationEvent.EventType.COMPLETED,
        ConsultationEvent.EventType.CANCELED,
        ConsultationEvent.EventType.REJECTED,
        ConsultationEvent.EventType.STARTED,
        ConsultationEvent.EventType.ACCEPTED,
        ConsultationEvent.EventType.QUEUED,
        ConsultationEvent.EventType.PRESCRIPTION_CREATED,
        ConsultationEvent.EventType.PRESCRIPTION_UPDATED,
    }
)


class ConsultationEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", read_only=True)
    display_label = serializers.SerializerMethodField()
    actor_display = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    highlight = serializers.SerializerMethodField()
    display_time = serializers.SerializerMethodField()

    class Meta:
        model = ConsultationEvent
        fields = [
            "id",
            "event_type",
            "display_label",
            "from_status",
            "to_status",
            "actor_email",
            "actor_display",
            "summary",
            "highlight",
            "display_time",
            "note",
            "suggested_time",
            "metadata",
            "created_at",
        ]

    def get_display_label(self, obj):
        return dict(ConsultationEvent.EventType.choices).get(obj.event_type, obj.event_type)

    def get_actor_display(self, obj):
        if not obj.actor:
            return "System"
        u = obj.actor
        name = (u.get_full_name() or "").strip()
        return name or u.email

    def get_summary(self, obj):
        actor = self.get_actor_display(obj)
        labels = dict(ConsultationEvent.EventType.choices)
        label = labels.get(obj.event_type, obj.event_type)
        if obj.event_type == ConsultationEvent.EventType.POSTPONED and obj.suggested_time:
            return f"{actor}: proposed a new time ({obj.suggested_time})."
        if obj.event_type == ConsultationEvent.EventType.REQUESTED:
            return f"{actor}: requested a consultation."
        if obj.from_status and obj.to_status:
            return f"{actor}: {label} ({obj.from_status} → {obj.to_status})."
        return f"{actor}: {label}."

    def get_highlight(self, obj):
        return obj.event_type in _EVENT_HIGHLIGHT

    def get_display_time(self, obj):
        if not obj.created_at:
            return ""
        dt = timezone.localtime(obj.created_at)
        return dt.strftime("%d %b %Y, %I:%M %p")

#======================================
# Doctor Profile Completion Serializer
#======================================
class DoctorProfileCompletionSerializer(serializers.ModelSerializer):
    """
    Serializer for completing doctor profile after login.
    Includes all required fields for profile completion.
    """
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    pending_fields = serializers.SerializerMethodField()
    filled_fields = serializers.SerializerMethodField()
    consultation_modes = serializers.ListField(
        child=serializers.ChoiceField(choices=["VIDEO", "AUDIO", "CHAT", "PHYSICAL"]),
        required=False,
        allow_empty=False,
    )
    photo = serializers.FileField(required=False, allow_null=True)
    identity_proof = serializers.FileField(required=False, allow_null=True)
    registration_certificate = serializers.FileField(required=False, allow_null=True)
    pending_change_requests = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'qualification', 'degree', 'college_university_name', 'passing_year',
            'specialty', 'experience', 'license_number', 'registration_number',
            'state_medical_council', 'identity_proof', 'registration_certificate',
            'major_diseases_specializations', 'previous_hospitals_served', 'photo',
            'hospital_or_clinic_name', 'clinic_address_street', 'city', 'state', 'pin_code',
            'consultation_modes', 'consultation_fee',
            'profile_completed', 'admin_verified', 'is_approved', 'admin_verified_at',
            'has_pending_changes', 'pending_changes_updated_at',
            'max_daily_consultations', 'completion_percentage',
            'pending_fields', 'filled_fields', 'pending_change_requests',
        ]
        read_only_fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'profile_completed', 'admin_verified', 'is_approved', 'admin_verified_at',
            'has_pending_changes', 'pending_changes_updated_at',
            'completion_percentage', 'pending_fields', 'filled_fields',
            'pending_change_requests',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        for field in ["photo", "identity_proof", "registration_certificate"]:
            value = getattr(instance, field, None)
            if value:
                data[field] = request.build_absolute_uri(value.url) if request else value.url
            else:
                data[field] = None
        return data

    def get_completion_percentage(self, obj):
        """Get profile completion percentage."""
        return obj.get_profile_completion_percentage()

    def get_pending_change_requests(self, obj):
        qs = obj.change_requests.filter(status=DoctorProfileChangeRequest.Status.PENDING).order_by(
            "-requested_at"
        )
        return [
            {
                "id": cr.id,
                "requested_at": cr.requested_at,
                "summary_parts": cr.get_summary_parts(),
            }
            for cr in qs
        ]

    def get_pending_fields(self, obj):
        """Get list of pending field names."""
        return obj.get_pending_fields()

    def get_filled_fields(self, obj):
        """Get dictionary of filled fields with their values."""
        filled = {}
        
        # Check text fields
        if obj.qualification:
            filled['qualification'] = obj.qualification
        for field in [
            'degree', 'college_university_name', 'passing_year', 'state_medical_council',
            'hospital_or_clinic_name', 'clinic_address_street', 'city', 'state', 'pin_code',
            'consultation_modes', 'consultation_fee'
        ]:
            value = getattr(obj, field, None)
            if value:
                filled[field] = value
        if obj.specialty:
            filled['specialty'] = obj.specialty
        if obj.experience:
            filled['experience'] = obj.experience
        if obj.license_number:
            filled['license_number'] = obj.license_number
        if obj.registration_number:
            filled['registration_number'] = obj.registration_number
        if obj.major_diseases_specializations:
            filled['major_diseases_specializations'] = obj.major_diseases_specializations
        
        # Check file fields - use try/except to handle potential errors
        if obj.photo:
            try:
                filled['photo'] = obj.photo.url if obj.photo else None
            except (ValueError, AttributeError):
                # File field exists but URL can't be generated
                filled['photo'] = True
        if obj.registration_certificate:
            try:
                filled['registration_certificate'] = obj.registration_certificate.url if obj.registration_certificate else None
            except (ValueError, AttributeError):
                # File field exists but URL can't be generated
                filled['registration_certificate'] = True
        if obj.identity_proof:
            try:
                filled['identity_proof'] = obj.identity_proof.url if obj.identity_proof else None
            except (ValueError, AttributeError):
                filled['identity_proof'] = True
        
        return filled

    def validate_license_number(self, value):
        """Validate license number format if provided."""
        if value and value.strip():
            # Convert to uppercase for validation
            value_upper = value.strip().upper()
            from django.core.validators import RegexValidator
            from django.core.exceptions import ValidationError
            
            # Validate format
            validator = RegexValidator(
                regex='^[A-Z0-9-]+$',
                message='License number must contain only uppercase letters, numbers, and hyphens.'
            )
            try:
                validator(value_upper)
            except ValidationError as e:
                raise serializers.ValidationError(str(e))
            
            # Check uniqueness (excluding current instance)
            instance = self.instance
            if instance:
                existing = DoctorProfile.objects.filter(license_number=value_upper).exclude(pk=instance.pk).exists()
            else:
                existing = DoctorProfile.objects.filter(license_number=value_upper).exists()
            
            if existing:
                raise serializers.ValidationError('This license number is already registered.')
            
            return value_upper
        return value
    
    def validate(self, attrs):
        """Validate that all required fields are provided for profile completion."""
        year = attrs.get("passing_year")
        if year and (year < 1950 or year > timezone.now().year):
            raise serializers.ValidationError({"passing_year": "Passing year is invalid."})
        modes = attrs.get("consultation_modes")
        if modes is not None:
            allowed = {"VIDEO", "AUDIO", "CHAT", "PHYSICAL"}
            if not isinstance(modes, list) or not modes:
                raise serializers.ValidationError({"consultation_modes": "Select at least one consultation mode."})
            invalid = [mode for mode in modes if mode not in allowed]
            if invalid:
                raise serializers.ValidationError({"consultation_modes": f"Invalid modes: {', '.join(invalid)}"})
        fee = attrs.get("consultation_fee")
        if fee is not None and fee < 0:
            raise serializers.ValidationError({"consultation_fee": "Consultation fee cannot be negative."})
        return attrs

    def update(self, instance, validated_data):
        """Update doctor profile and mark as completed if all fields are filled."""
        from django.utils import timezone

        # Track if any changes were made
        has_changes = False
        
        # Update fields - skip empty strings to preserve existing values
        for attr, value in validated_data.items():
            # For file fields, always update if provided
            if attr in ['photo', 'identity_proof', 'registration_certificate']:
                current_value = getattr(instance, attr, None)
                if current_value != value:
                    setattr(instance, attr, value)
                    has_changes = True
            # For text fields, skip empty strings (don't overwrite existing values)
            elif value != '':
                current_value = getattr(instance, attr, None)
                if current_value != value:
                    setattr(instance, attr, value)
                    has_changes = True
        
        # If changes were made and profile was previously verified, mark as pending approval
        if has_changes and instance.admin_verified:
            instance.has_pending_changes = True
            instance.pending_changes_updated_at = timezone.now()
            # Unverify until admin approves — consultations disabled until re-approved
            instance.admin_verified = False
            instance.is_approved = False
        
        # Check if profile is complete after update
        required_fields = [
            instance.degree or instance.qualification,
            instance.college_university_name,
            instance.passing_year,
            instance.specialty,
            instance.experience,
            instance.license_number,
            instance.registration_number,
            instance.state_medical_council,
            instance.identity_proof,
            instance.registration_certificate,
            instance.hospital_or_clinic_name,
            instance.clinic_address_street,
            instance.city,
            instance.state,
            instance.pin_code,
            instance.consultation_modes,
            instance.consultation_fee,
        ]
        
        # Mark as completed if all required fields are filled
        if all(required_fields):
            instance.profile_completed = True
        else:
            # If not complete, ensure flag is False
            instance.profile_completed = False
        
        instance.save()

        return instance
