from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from users.models import DoctorProfile, PatientProfile, TMCProfile


class ConsultationFeeSetting(models.Model):
    """
    Active consultation fee configuration managed by staff/admin.

    The newest active row is used as the default fee when booking requests do
    not explicitly provide an amount.
    """

    name = models.CharField(max_length=100, default="Default consultation fees")
    direct_patient_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tmc_consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Platform/service fee percentage charged on the doctor's consultation fee.",
    )
    currency = models.CharField(max_length=10, default="INR")
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="consultation_fee_settings_created",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.name}: direct={self.direct_patient_fee} "
            f"tmc={self.tmc_consultation_fee} {self.currency}"
        )

    @classmethod
    def active(cls):
        setting = cls.objects.filter(is_active=True).order_by("-created_at").first()
        if setting:
            return setting
        return cls(
            name="System default fees",
            direct_patient_fee=0,
            tmc_consultation_fee=0,
            platform_fee_percentage=0,
            currency="INR",
            is_active=True,
        )


#==================================
# Doctor Availability Model
#==================================
class DoctorAvailability(models.Model):
    doctor = models.OneToOneField(
        DoctorProfile, on_delete=models.CASCADE, related_name="availability"
    )

    # Availability toggles
    is_available_online = models.BooleanField(default=True)
    is_available_in_clinic = models.BooleanField(default=True)

    # Next availability if unavailable
    next_available_online = models.DateTimeField(null=True, blank=True)
    next_available_in_clinic = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_available_online", "is_available_in_clinic"]),
        ]

    def __str__(self):
        return (
            f"{self.doctor.user.email} - Online: {self.is_available_online}, "
            f"Clinic: {self.is_available_in_clinic}"
        )

#==================================
# Doctor Schedule Model
#==================================

class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="schedules"
    )

    day_of_week = models.CharField(
        max_length=10,
        choices=[
            ("Monday", "Monday"),
            ("Tuesday", "Tuesday"),
            ("Wednesday", "Wednesday"),
            ("Thursday", "Thursday"),
            ("Friday", "Friday"),
            ("Saturday", "Saturday"),
            ("Sunday", "Sunday"),
        ],
    )
    start_time = models.TimeField()
    end_time = models.TimeField()

    is_online = models.BooleanField(default=True)  # True if online, False if in-clinic
    consultation_duration_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Default duration for each consultation booked inside this slot.",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["doctor", "day_of_week", "is_online", "is_active"]),
        ]

    def __str__(self):
        return (
            f"{self.doctor.user.email} - {self.day_of_week}: "
            f"{self.start_time} to {self.end_time} "
            f"({'Online' if self.is_online else 'Clinic'})"
        )


#=====================================
# Consultation Booking Model
#=====================================
class Consultation(models.Model):
    class ConsultationType(models.TextChoices):
        DIRECT = "DIRECT", "Direct by Patient"
        TMC = "TMC", "Via Telemedicine Center"

    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Waiting for Doctor"
        ACCEPTED = "ACCEPTED", "Accepted by Doctor"
        QUEUED = "QUEUED", "Doctor Put in Queue"
        IN_PROGRESS = "IN_PROGRESS", "Consultation In Progress"
        POSTPONED = "POSTPONED", "Doctor Suggested Another Time"
        CANCELED = "CANCELED", "Canceled by Patient/TMC"
        COMPLETED = "COMPLETED", "Consultation Completed"
        REJECTED = "REJECTED", "Rejected by Doctor"
        REJECTED_BY_PATIENT = "REJECTED_BY_PATIENT", "Postponed Time Rejected by Patient"

    patient = models.ForeignKey(
        PatientProfile, on_delete=models.CASCADE, related_name="consultations"
    )
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="consultations"
    )
    tmc = models.ForeignKey(
        TMCProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultations",
    )

    consultation_type = models.CharField(
        max_length=10,
        choices=ConsultationType.choices,
        default=ConsultationType.DIRECT,
    )
    scheduled_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        db_index=True,
    )

    new_suggested_time = models.DateTimeField(
        null=True, blank=True
    )  # Only set if doctor postpones

    queue_number = models.IntegerField(
        null=True, blank=True,
        help_text="Queue position when consultation is queued. Calculated based on order of acceptance."
    )

    is_completed = models.BooleanField(default=False)
    is_free = models.BooleanField(
        default=False,
        help_text="True if this consultation is covered by a free TMC quota.",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_status_changed_at = models.DateTimeField(default=timezone.now)
    status_changed_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="consultations_status_changed",
    )
    terminal_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Optional reason for terminal statuses like cancel/reject.",
    )

    class Meta:
        indexes = [
            models.Index(fields=["doctor", "scheduled_time"]),
            models.Index(fields=["patient", "created_at"]),
            models.Index(fields=["tmc", "created_at"]),
        ]

    def __str__(self):
        return (
            f"Consultation {self.id} - {self.status} - "
            f"{self.patient.user.email} with {self.doctor.user.email}"
        )


#==================================
# Consultation Record Model
#==================================
class ConsultationRecord(models.Model):
    consultation = models.OneToOneField(
        "consultations.Consultation",  # ✅ Use the full app reference
        on_delete=models.CASCADE,
        related_name="record"
    )
    video_recording = models.FileField(upload_to="consultations/videos/", null=True, blank=True)
    chat_logs = models.JSONField(null=True, blank=True)
    prescription = models.FileField(upload_to="consultations/prescriptions/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation Record for {self.consultation}"


class ConsultationVideoSession(models.Model):
    class Provider(models.TextChoices):
        DYTE = "DYTE", "Dyte"
        CLOUDFLARE = "CLOUDFLARE", "Cloudflare Calls"

    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    consultation = models.OneToOneField(
        "consultations.Consultation",
        on_delete=models.CASCADE,
        related_name="video_session",
    )
    provider = models.CharField(max_length=30, choices=Provider.choices, default=Provider.DYTE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED, db_index=True)
    external_meeting_id = models.CharField(max_length=120, null=True, blank=True, db_index=True)
    external_payload = models.JSONField(default=dict, blank=True)
    participant_tokens = models.JSONField(default=dict, blank=True)
    participant_ids = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="video_sessions_created",
    )
    responded_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="video_sessions_responded",
    )
    requested_at = models.DateTimeField(default=timezone.now, db_index=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["provider", "external_meeting_id"]),
        ]

    def __str__(self):
        return f"{self.provider} video session for consultation #{self.consultation_id}"
    

#=================================
# Realtime chat for consultation
#================================
class ConsultationChat(models.Model):
    consultation = models.ForeignKey(
        "Consultation", on_delete=models.CASCADE, related_name="chats"
    )
    sender = models.ForeignKey("users.User", on_delete=models.CASCADE)  # Doctor or Patient
    message = models.TextField(blank=True, null=True)  # Allow empty if only file is sent
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # ✅ Read receipts added
    
    # File attachments
    attachment = models.FileField(
        upload_to="chat_attachments/%Y/%m/%d/",
        null=True,
        blank=True,
        help_text="Image or PDF file attachment"
    )
    attachment_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Type of attachment: image, pdf, or other"
    )

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"Chat {self.id} - {self.sender.email} - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        # Auto-detect attachment type based on file extension
        if self.attachment and not self.attachment_type:
            file_name = self.attachment.name.lower()
            if file_name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                self.attachment_type = 'image'
            elif file_name.endswith('.pdf'):
                self.attachment_type = 'pdf'
            else:
                self.attachment_type = 'other'
        super().save(*args, **kwargs)


#================================
# Follow-up session model
#================================
class ConsultationFollowUpSession(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Waiting for Doctor"
        IN_PROGRESS = "IN_PROGRESS", "Follow-up In Progress"
        COMPLETED = "COMPLETED", "Follow-up Completed"
        REJECTED = "REJECTED", "Follow-up Rejected"
        CANCELED = "CANCELED", "Follow-up Canceled"

    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="follow_up_sessions"
    )
    sequence_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    requested_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requested_consultation_followups",
    )
    started_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="started_consultation_followups",
    )
    completed_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="completed_consultation_followups",
    )
    is_billable = models.BooleanField(default=False)
    amount_charged = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charge_note = models.CharField(max_length=255, blank=True, default="")
    requested_at = models.DateTimeField(default=timezone.now, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-requested_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["consultation", "sequence_number"],
                name="uniq_consultation_followup_sequence",
            )
        ]
        indexes = [
            models.Index(fields=["consultation", "status", "-requested_at"]),
            models.Index(fields=["status", "-requested_at"]),
        ]

    def __str__(self):
        return f"Follow-up #{self.sequence_number} for consultation {self.consultation_id}"


#================================
#---- Prescription model-----
#================================
class Prescription(models.Model):
    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="prescriptions"
    )
    follow_up_session = models.ForeignKey(
        ConsultationFollowUpSession,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="prescriptions",
        help_text="Null for the original consultation prescription; set for follow-up prescriptions.",
    )
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    medicines = models.JSONField(
        default=list,
        help_text="List of medicines with name, dosage, frequency, duration, etc."
    )
    instructions = models.TextField(
        help_text="General instructions for the patient", blank=True, null=True,
        default="Take medicines as prescribed. Follow up if symptoms persist."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Prescription for {self.patient.user.email} by {self.doctor.user.email}"


class PrescriptionVersion(models.Model):
    """
    Immutable snapshot of prescription content. Version 1 is captured at creation;
    each subsequent save archives the prior state before applying updates.
    """

    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField(db_index=True)
    medicines = models.JSONField(default=list)
    instructions = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="prescription_versions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["prescription", "version_number"],
                name="uniq_prescription_version_number",
            ),
        ]
        indexes = [
            models.Index(fields=["prescription", "version_number"]),
        ]

    def __str__(self):
        return f"PrescriptionVersion(rx={self.prescription_id}, v={self.version_number})"


#================================
# Payment model
#================================
class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"

    consultation = models.OneToOneField(
        Consultation,
        on_delete=models.CASCADE,
        related_name="payment",
        help_text="Consultation this payment is associated with.",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    paid_by_tmc = models.BooleanField(
        default=False,
        help_text=(
            "True if payment is handled by the TMC "
            "(e.g., free quota or centralized billing)."
        ),
    )
    provider = models.CharField(max_length=30, default="WALLET", db_index=True)
    gateway_order_id = models.CharField(max_length=120, null=True, blank=True, db_index=True)
    gateway_payment_id = models.CharField(max_length=120, null=True, blank=True)
    gateway_signature = models.CharField(max_length=255, null=True, blank=True)
    gateway_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for consultation {self.consultation_id} - {self.status}"


class TMCRechargeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELED = "CANCELED", "Canceled"

    class Provider(models.TextChoices):
        MANUAL = "MANUAL", "Manual / Admin Approval"
        RAZORPAY = "RAZORPAY", "Razorpay"

    tmc = models.ForeignKey(TMCProfile, on_delete=models.CASCADE, related_name="recharge_requests")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    provider = models.CharField(max_length=30, choices=Provider.choices, default=Provider.MANUAL, db_index=True)
    reference_note = models.CharField(max_length=255, blank=True, null=True)
    gateway_order_id = models.CharField(max_length=120, null=True, blank=True, db_index=True)
    gateway_payment_id = models.CharField(max_length=120, null=True, blank=True)
    gateway_signature = models.CharField(max_length=255, null=True, blank=True)
    gateway_payload = models.JSONField(default=dict, blank=True)
    requested_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tmc_recharges_requested",
    )
    processed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tmc_recharges_processed",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tmc", "status", "-created_at"]),
        ]

    def __str__(self):
        return f"TMCRechargeRequest({self.tmc.user.email}, {self.amount}, {self.status})"


class PatientWalletRechargeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELED = "CANCELED", "Canceled"

    class Provider(models.TextChoices):
        MANUAL = "MANUAL", "Manual / Admin Approval"
        RAZORPAY = "RAZORPAY", "Razorpay"

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="wallet_recharge_requests")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    provider = models.CharField(max_length=30, choices=Provider.choices, default=Provider.MANUAL, db_index=True)
    reference_note = models.CharField(max_length=255, blank=True, null=True)
    gateway_order_id = models.CharField(max_length=120, null=True, blank=True, db_index=True)
    gateway_payment_id = models.CharField(max_length=120, null=True, blank=True)
    gateway_signature = models.CharField(max_length=255, null=True, blank=True)
    gateway_payload = models.JSONField(default=dict, blank=True)
    requested_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_wallet_recharges_requested",
    )
    processed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_wallet_recharges_processed",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "status", "-created_at"]),
            models.Index(fields=["provider", "status", "-created_at"]),
        ]

    def __str__(self):
        return f"PatientWalletRechargeRequest({self.patient.user.email}, {self.amount}, {self.status})"


class ConsultationEvent(models.Model):
    class EventType(models.TextChoices):
        REQUESTED = "REQUESTED", "Consultation Requested"
        ACCEPTED = "ACCEPTED", "Doctor Accepted"
        QUEUED = "QUEUED", "Moved to Queue"
        STARTED = "STARTED", "Consultation Started"
        POSTPONED = "POSTPONED", "Doctor Postponed"
        POSTPONE_ACCEPTED = "POSTPONE_ACCEPTED", "Patient Accepted Postponed Time"
        POSTPONE_REJECTED = "POSTPONE_REJECTED", "Patient Rejected Postponed Time"
        REJECTED = "REJECTED", "Doctor Rejected"
        CANCELED = "CANCELED", "Consultation Canceled"
        COMPLETED = "COMPLETED", "Consultation Completed"
        MESSAGE_SENT = "MESSAGE_SENT", "Message Sent"
        FOLLOWUP_REQUESTED = "FOLLOWUP_REQUESTED", "Follow-up Requested"
        FOLLOWUP_STARTED = "FOLLOWUP_STARTED", "Follow-up Started"
        FOLLOWUP_COMPLETED = "FOLLOWUP_COMPLETED", "Follow-up Completed"
        PRESCRIPTION_CREATED = "PRESCRIPTION_CREATED", "Prescription Created"
        PRESCRIPTION_REISSUED = "PRESCRIPTION_REISSUED", "Prescription Reissued"
        PRESCRIPTION_UPDATED = "PRESCRIPTION_UPDATED", "Prescription Updated"

    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="events"
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)
    from_status = models.CharField(max_length=20, null=True, blank=True)
    to_status = models.CharField(max_length=20, null=True, blank=True)
    actor = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="consultation_events",
    )
    note = models.TextField(null=True, blank=True)
    suggested_time = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consultation", "-created_at"]),
            models.Index(fields=["event_type", "-created_at"]),
        ]

    def __str__(self):
        return f"ConsultationEvent({self.consultation_id}, {self.event_type})"


class ConsultationFinance(models.Model):
    class SourceType(models.TextChoices):
        DIRECT_PATIENT = "DIRECT_PATIENT", "Direct Patient"
        TMC = "TMC", "TMC"

    class BillingType(models.TextChoices):
        FREE = "FREE", "Free"
        PAID = "PAID", "Paid"

    class PaymentStatus(models.TextChoices):
        NOT_REQUIRED = "NOT_REQUIRED", "Not Required"
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"
        PARTIAL_REFUND = "PARTIAL_REFUND", "Partial Refund"
        SETTLED = "SETTLED", "Settled"

    class PayerEntity(models.TextChoices):
        PATIENT = "PATIENT", "Patient"
        TMC = "TMC", "TMC"
        ADMIN = "ADMIN", "Admin / Platform"
        NONE = "NONE", "None"

    class DoctorEarningStatus(models.TextChoices):
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"
        PENDING = "PENDING", "Pending"
        EARNED = "EARNED", "Earned"
        SETTLED = "SETTLED", "Settled"

    consultation = models.OneToOneField(
        Consultation, on_delete=models.CASCADE, related_name="finance"
    )
    source_type = models.CharField(max_length=20, choices=SourceType.choices, db_index=True)
    billing_type = models.CharField(max_length=10, choices=BillingType.choices, db_index=True)
    payer_entity = models.CharField(max_length=10, choices=PayerEntity.choices, db_index=True)
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, db_index=True
    )
    doctor_earning_status = models.CharField(
        max_length=20,
        choices=DoctorEarningStatus.choices,
        default=DoctorEarningStatus.NOT_APPLICABLE,
        db_index=True,
    )
    amount_charged = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    doctor_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    admin_subsidy_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wallet_used = models.BooleanField(default=False)
    tmc_billed = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="finance_records"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ConsultationFinance({self.consultation_id}, {self.billing_type}, {self.payment_status})"


class PatientWallet(models.Model):
    patient = models.OneToOneField(
        PatientProfile, on_delete=models.CASCADE, related_name="wallet"
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_credited = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_debited = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PatientWallet({self.patient.user.email}, balance={self.balance})"


class PatientWalletEntry(models.Model):
    class EntryType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"
        REFUND = "REFUND", "Refund"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        FREE_RECORD = "FREE_RECORD", "Free Consultation Record"

    wallet = models.ForeignKey(
        PatientWallet, on_delete=models.CASCADE, related_name="entries"
    )
    entry_type = models.CharField(max_length=20, choices=EntryType.choices, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    consultation = models.ForeignKey(
        Consultation, on_delete=models.SET_NULL, null=True, blank=True, related_name="patient_wallet_entries"
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PatientWalletEntry({self.wallet_id}, {self.entry_type}, {self.amount})"


class TMCAccount(models.Model):
    tmc = models.OneToOneField(TMCProfile, on_delete=models.CASCADE, related_name="account")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_charged = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_credited = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_debited = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TMCAccount({self.tmc.user.email}, balance={self.balance})"


class TMCAccountEntry(models.Model):
    class EntryType(models.TextChoices):
        CHARGE = "CHARGE", "Consultation Charge"
        CREDIT = "CREDIT", "Credit"
        REFUND = "REFUND", "Refund"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        FREE_RECORD = "FREE_RECORD", "Free Consultation Record"

    account = models.ForeignKey(
        TMCAccount, on_delete=models.CASCADE, related_name="entries"
    )
    entry_type = models.CharField(max_length=20, choices=EntryType.choices, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    consultation = models.ForeignKey(
        Consultation, on_delete=models.SET_NULL, null=True, blank=True, related_name="tmc_account_entries"
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"TMCAccountEntry({self.account_id}, {self.entry_type}, {self.amount})"


class AdminPlatformAccount(models.Model):
    name = models.CharField(max_length=80, default="Platform Wallet", unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_credited = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_debited = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_platform_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_doctor_subsidies = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AdminPlatformAccount(balance={self.balance})"


class AdminPlatformEntry(models.Model):
    class EntryType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        PLATFORM_FEE = "PLATFORM_FEE", "Platform Fee"
        DOCTOR_SUBSIDY = "DOCTOR_SUBSIDY", "Doctor Subsidy"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"

    account = models.ForeignKey(
        AdminPlatformAccount, on_delete=models.CASCADE, related_name="entries"
    )
    entry_type = models.CharField(max_length=20, choices=EntryType.choices, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_platform_entries",
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"AdminPlatformEntry({self.entry_type}, {self.amount})"


class DoctorEarning(models.Model):
    class Status(models.TextChoices):
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"
        PENDING = "PENDING", "Pending"
        EARNED = "EARNED", "Earned"
        SETTLED = "SETTLED", "Settled"

    consultation = models.OneToOneField(
        Consultation, on_delete=models.CASCADE, related_name="doctor_earning"
    )
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="earnings")
    source_type = models.CharField(max_length=20, choices=ConsultationFinance.SourceType.choices)
    billing_type = models.CharField(max_length=10, choices=ConsultationFinance.BillingType.choices)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    earning_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DoctorEarning({self.consultation_id}, {self.earning_amount}, {self.status})"
