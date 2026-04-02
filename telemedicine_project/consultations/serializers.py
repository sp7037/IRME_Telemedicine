from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import (
    DoctorAvailability,
    DoctorSchedule,
    Consultation,
    ConsultationChat,
    Prescription,
    PrescriptionVersion,
    Payment,
    ConsultationEvent,
)
from users.models import DoctorProfile, PatientProfile, TMCProfile
from .finance import create_consultation_finance

# ✅ Serializer for DoctorSchedule (Time Slots)
class DoctorScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSchedule
        fields = ['id', 'day_of_week', 'start_time', 'end_time', 'is_online']

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

        attrs["doctor"] = doctor
        attrs["patient_profile"] = user.patient_profile

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

        availability_ok = self._doctor_is_available(doctor, scheduled_time)
        if not availability_ok:
            # Try fallback doctor
            fallback = self._find_fallback_doctor(doctor, scheduled_time)
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
        amount = validated_data.get("amount")

        is_free = False
        payment = None

        # TMC quota & payment logic
        if consultation_type == Consultation.ConsultationType.TMC and tmc:
            # Check free quota
            if tmc.free_consultations_remaining > 0:
                is_free = True
                tmc.free_consultations_used += 1
                tmc.save(update_fields=["free_consultations_used"])
            else:
                # Create a paid payment record (simulate successful payment)
                payment_amount = amount if amount is not None else 0
                # Consultation must be created before Payment; create with is_free=False first

        # Direct consultations should create payment records (if amount > 0)
        needs_direct_payment = (
            consultation_type == Consultation.ConsultationType.DIRECT
            and (amount is not None and amount > 0)
        )

        # Create consultation
        consultation = Consultation.objects.create(
            patient=patient_profile,
            doctor=doctor,
            tmc=tmc,
            consultation_type=consultation_type,
            scheduled_time=scheduled_time,
            status=Consultation.StatusChoices.PENDING,
            is_free=is_free,
        )

        # Create payment for direct consultations when amount > 0
        if needs_direct_payment:
            payment = Payment.objects.create(
                consultation=consultation,
                amount=amount,
                status=Payment.Status.PAID,
                paid_by_tmc=False,
            )

        # If no free quota and this is a TMC booking, create a Payment
        if consultation_type == Consultation.ConsultationType.TMC and tmc and not is_free:
            payment_amount = amount if amount is not None else Decimal("0.00")
            payment = Payment.objects.create(
                consultation=consultation,
                amount=payment_amount,
                status=Payment.Status.PAID,
                paid_by_tmc=True,
            )

        # Additive finance truth layer (keeps Payment backward-compatible)
        create_consultation_finance(
            consultation=consultation,
            payment=payment,
            amount=amount if amount is not None else Decimal("0.00"),
        )

        validated_data["consultation"] = consultation
        validated_data["payment"] = payment
        return consultation

    # ------------------------
    # Helper methods
    # ------------------------

    def _doctor_is_available(self, doctor: DoctorProfile, scheduled_time):
        availability = getattr(doctor, "availability", None)
        if availability and not availability.is_available_online:
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
        conflict = Consultation.objects.filter(
            doctor=doctor,
            scheduled_time=scheduled_time,
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

    def _find_fallback_doctor(self, original_doctor, scheduled_time):
        """Attempt to find another doctor in same specialty who is available."""
        specialty = original_doctor.specialty
        candidates = DoctorProfile.objects.exclude(id=original_doctor.id)
        if specialty:
            candidates = candidates.filter(specialty=specialty)

        for doctor in candidates:
            if self._doctor_is_available(doctor, scheduled_time):
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

    class Meta:
        model = Consultation
        fields = [
            'id', 'doctor', 'doctor_name', 'patient_name', 'patient_email', 'patient_phone',
            'consultation_type', 'formatted_time', 'formatted_suggested_time',
            'status', 'is_completed', 'scheduled_time', 'new_suggested_time',
            'created_at', 'created_at_formatted', 'queue_number', 'estimated_waiting_time',
            'tmc_name', 'consultation_label', 'billing_type', 'amount_charged'
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
        return obj.message and obj.message.startswith("PRESCRIPTION:")

    def get_prescription_data(self, obj):
        """If this is a prescription message, fetch the prescription data"""
        if self.get_is_prescription(obj):
            try:
                prescription = Prescription.objects.get(consultation=obj.consultation)
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
    version_row_count = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            "id", "consultation_id", "consultation", "doctor", "doctor_name",
            "doctor_qualification", "doctor_license_number", "doctor_city", "doctor_state",
            "patient", "patient_name", "medicines", "instructions", "created_at",
            "updated_at", "version_row_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "version_row_count"]

    def get_doctor_name(self, obj):
        return f"{obj.doctor.user.first_name} {obj.doctor.user.last_name}".strip()

    def get_patient_name(self, obj):
        return f"{obj.patient.user.first_name} {obj.patient.user.last_name}".strip()

    def get_version_row_count(self, obj):
        return obj.versions.count()


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
        read_only_fields = fields


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
    photo = serializers.SerializerMethodField()
    registration_certificate = serializers.SerializerMethodField()
    
    def get_photo(self, obj):
        """Return full URL for photo if it exists."""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def get_registration_certificate(self, obj):
        """Return full URL for registration certificate if it exists."""
        if obj.registration_certificate:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.registration_certificate.url)
            return obj.registration_certificate.url
        return None

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'qualification', 'specialty', 'experience',
            'license_number', 'registration_number',
            'registration_certificate', 'major_diseases_specializations',
            'previous_hospitals_served', 'photo', 'hospital_or_clinic_name', 'city', 'state',
            'profile_completed', 'admin_verified', 'admin_verified_at',
            'has_pending_changes', 'pending_changes_updated_at',
            'max_daily_consultations', 'completion_percentage', 
            'pending_fields', 'filled_fields'
        ]
        read_only_fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number', 
            'profile_completed', 'admin_verified', 'admin_verified_at',
            'has_pending_changes', 'pending_changes_updated_at',
            'completion_percentage', 'pending_fields', 'filled_fields'
        ]

    def get_completion_percentage(self, obj):
        """Get profile completion percentage."""
        return obj.get_profile_completion_percentage()

    def get_pending_fields(self, obj):
        """Get list of pending field names."""
        return obj.get_pending_fields()

    def get_filled_fields(self, obj):
        """Get dictionary of filled fields with their values."""
        filled = {}
        
        # Check text fields
        if obj.qualification:
            filled['qualification'] = obj.qualification
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
        # Allow partial updates - don't enforce all fields at once
        # The completion check happens in the update method
        return attrs

    def update(self, instance, validated_data):
        """Update doctor profile and mark as completed if all fields are filled."""
        from django.utils import timezone
        
        # Track if any changes were made
        has_changes = False
        
        # Update fields - skip empty strings to preserve existing values
        for attr, value in validated_data.items():
            # For file fields, always update if provided
            if attr in ['photo', 'registration_certificate']:
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
            # Unverify until admin approves
            instance.admin_verified = False
        
        # Check if profile is complete after update
        required_fields = [
            instance.qualification, instance.specialty, instance.experience,
            instance.license_number, instance.registration_number,
            instance.major_diseases_specializations, instance.photo,
            instance.registration_certificate
        ]
        
        # Mark as completed if all required fields are filled
        if all(required_fields):
            instance.profile_completed = True
        else:
            # If not complete, ensure flag is False
            instance.profile_completed = False
        
        instance.save()
        return instance