from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from users.models import DoctorProfile, PatientProfile, TMCProfile


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

    class Meta:
        indexes = [
            models.Index(fields=["doctor", "day_of_week", "is_online"]),
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
#---- Prescription model-----
#================================
class Prescription(models.Model):
    consultation = models.OneToOneField(
        Consultation, on_delete=models.CASCADE, related_name="prescription"
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for consultation {self.consultation_id} - {self.status}"


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
        PRESCRIPTION_CREATED = "PRESCRIPTION_CREATED", "Prescription Created"
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
