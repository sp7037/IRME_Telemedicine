import logging

from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()  # Dynamically fetch the user model

logger = logging.getLogger(__name__)

_DOCTOR_PROFILE_CHANGE_FIELD_LABELS = {
    "qualification": "Qualification",
    "degree": "Degree",
    "college_university_name": "College / university",
    "passing_year": "Passing year",
    "specialty": "Specialty",
    "experience": "Experience",
    "license_number": "License number",
    "registration_number": "Registration number",
    "state_medical_council": "State medical council",
    "major_diseases_specializations": "Major diseases / specializations",
    "previous_hospitals_served": "Previous hospitals",
    "hospital_or_clinic_name": "Hospital or clinic name",
    "clinic_address_street": "Clinic street address",
    "city": "City / district",
    "state": "State",
    "pin_code": "PIN code",
    "consultation_modes": "Consultation modes",
    "consultation_fee": "Consultation fee",
    "max_daily_consultations": "Max daily consultations",
}
_DOCTOR_PROFILE_CHANGE_ADDRESS_KEYS = frozenset(
    {"clinic_address_street", "city", "state", "pin_code"}
)

# -------------------------------------
# Abstract Base Model for Role Profiles
# -------------------------------------
class BaseProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="%(class)s_profile")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # ✅ Indexed for date-based queries
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)  # ✅ Indexed for active/inactive filtering

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_active', 'created_at']),  # ✅ Composite index for common query patterns
            models.Index(fields=['-created_at']),  # ✅ Index for recent-first queries
        ]

    def __str__(self):
        return f"Profile of {self.user.get_full_name() or self.user.email}"

# -------------------------------------
# Doctor Profile Model
# -------------------------------------
class DoctorProfile(BaseProfile):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    qualification = models.CharField(max_length=100, null=True, blank=True)
    degree = models.CharField(max_length=100, null=True, blank=True)
    college_university_name = models.CharField(max_length=255, null=True, blank=True)
    passing_year = models.PositiveIntegerField(null=True, blank=True)
    specialty = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # ✅ Indexed for specialty filtering
    experience = models.CharField(max_length=100, null=True, blank=True)
    license_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        unique=True,
        db_index=True,  # ✅ Optimized for performance
        validators=[
            RegexValidator(
                regex='^[A-Z0-9-]+$',
                message='License number must contain only uppercase letters, numbers, and hyphens.'
            )
        ],
    )
    practice_type = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to="doctors/%Y/%m/%d/photos/", null=True, blank=True)
    signature = models.ImageField(upload_to="doctors/%Y/%m/%d/signatures/", null=True, blank=True)
    hospital_or_clinic_name = models.CharField(max_length=100, null=True, blank=True)
    clinic_address_street = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True, help_text="City where the doctor practices")
    state = models.CharField(max_length=100, null=True, blank=True, help_text="State where the doctor practices")
    pin_code = models.CharField(max_length=12, null=True, blank=True)
    consultation_modes = models.JSONField(default=list, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_daily_consultations = models.PositiveIntegerField(
        default=50,
        help_text="Maximum number of consultations this doctor can take per day.",
    )
    # Additional profile fields for profile completion
    registration_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Medical registration number",
    )
    state_medical_council = models.CharField(max_length=160, null=True, blank=True)
    identity_proof = models.FileField(
        upload_to="doctors/%Y/%m/%d/identity/",
        null=True,
        blank=True,
        help_text="Upload government identity proof",
    )
    registration_certificate = models.FileField(
        upload_to="doctors/%Y/%m/%d/certificates/",
        null=True,
        blank=True,
        help_text="Upload registration certificate",
    )
    major_diseases_specializations = models.TextField(
        null=True,
        blank=True,
        help_text="Major diseases and specializations",
    )
    previous_hospitals_served = models.TextField(
        null=True,
        blank=True,
        help_text="Previous hospitals served (include in experience)",
    )
    profile_completed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the doctor has completed their profile",
    )
    admin_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the admin has verified the doctor's profile",
    )
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the doctor is approved to take consultations",
    )
    admin_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when admin verified the profile",
    )
    admin_verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_doctor_profiles",
        help_text="Admin user who verified this profile",
    )
    has_pending_changes = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the doctor has made changes pending admin approval",
    )
    pending_changes_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when pending changes were made",
    )

    class Meta(BaseProfile.Meta):
        indexes = BaseProfile.Meta.indexes + [
            models.Index(fields=['specialty']),  # ✅ Index for specialty-based queries
            models.Index(fields=['is_active', 'specialty']),  # ✅ Composite index for active doctors by specialty
            models.Index(fields=['is_active', 'max_daily_consultations']),
        ]

    def save(self, *args, **kwargs):
        if self.license_number:
            self.license_number = self.license_number.upper()  # ✅ Auto-converts to uppercase
        super().save(*args, **kwargs)

    def get_profile_completion_percentage(self):
        """Calculate profile completion percentage based on required fields."""
        required_fields = {
            'degree': self.degree or self.qualification,
            'college_university_name': self.college_university_name,
            'passing_year': self.passing_year,
            'specialty': self.specialty,
            'experience': self.experience,
            'license_number': self.license_number,
            'registration_number': self.registration_number,
            'state_medical_council': self.state_medical_council,
            'identity_proof': self.identity_proof,
            'registration_certificate': self.registration_certificate,
            'hospital_or_clinic_name': self.hospital_or_clinic_name,
            'clinic_address_street': self.clinic_address_street,
            'city': self.city,
            'state': self.state,
            'pin_code': self.pin_code,
            'consultation_modes': self.consultation_modes,
            'consultation_fee': self.consultation_fee,
        }
        
        filled_count = sum(1 for value in required_fields.values() if value)
        total_count = len(required_fields)
        
        return int((filled_count / total_count) * 100) if total_count > 0 else 0

    def get_pending_fields(self):
        """Get list of pending required fields."""
        required_fields = {
            'degree': self.degree or self.qualification,
            'college_university_name': self.college_university_name,
            'passing_year': self.passing_year,
            'specialty': self.specialty,
            'experience': self.experience,
            'license_number': self.license_number,
            'registration_number': self.registration_number,
            'state_medical_council': self.state_medical_council,
            'identity_proof': self.identity_proof,
            'registration_certificate': self.registration_certificate,
            'hospital_or_clinic_name': self.hospital_or_clinic_name,
            'clinic_address_street': self.clinic_address_street,
            'city': self.city,
            'state': self.state,
            'pin_code': self.pin_code,
            'consultation_modes': self.consultation_modes,
            'consultation_fee': self.consultation_fee,
        }
        
        return [field for field, value in required_fields.items() if not value]

    def __str__(self):
        return f"Doctor Profile: {self.user.get_full_name() or self.user.email}"


def doctor_profile_field_changed(profile, field: str, new_value) -> bool:
    """True when new_value differs from the live doctor profile (handles Decimal/list/int quirks)."""
    from decimal import Decimal

    current = getattr(profile, field, None)

    if field == "consultation_modes":
        cur = list(current or [])
        new = list(new_value or []) if new_value is not None else []
        return sorted(cur) != sorted(new)

    if field == "consultation_fee":
        try:
            cur_d = Decimal(str(current)) if current is not None else None
            new_d = Decimal(str(new_value)) if new_value not in (None, "") else None
        except Exception:
            return True
        if cur_d is None and new_d is None:
            return False
        if cur_d is None or new_d is None:
            return True
        return cur_d != new_d

    if field in ("passing_year", "max_daily_consultations"):
        try:
            if current is None and new_value in (None, ""):
                return False
            return int(current) != int(new_value)
        except (TypeError, ValueError):
            return str(current).strip() != str(new_value).strip()

    if field == "license_number":
        return (current or "").strip().upper() != (str(new_value or "")).strip().upper()

    def norm(v):
        if v is None:
            return ""
        return str(v).strip()

    return norm(current) != norm(new_value)


def filter_proposed_data_to_actual_changes(profile, proposed_data: dict) -> dict:
    """Remove proposed keys that match the current profile (full-form PATCH payloads)."""
    if not proposed_data:
        return {}
    return {k: v for k, v in proposed_data.items() if doctor_profile_field_changed(profile, k, v)}


class DoctorProfileChangeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="change_requests")
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctor_profile_change_requests",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    proposed_data = models.JSONField(default=dict, blank=True)
    proposed_photo = models.ImageField(upload_to="doctors/%Y/%m/%d/pending/photos/", null=True, blank=True)
    proposed_identity_proof = models.FileField(upload_to="doctors/%Y/%m/%d/pending/identity/", null=True, blank=True)
    proposed_registration_certificate = models.FileField(upload_to="doctors/%Y/%m/%d/pending/certificates/", null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_doctor_profile_change_requests",
    )
    admin_note = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["doctor", "status", "-requested_at"]),
        ]

    def get_summary_parts(self):
        """Human-readable labels for what this request changes (for UI and emails)."""
        parts = []
        doctor = self.doctor
        if self.proposed_photo:
            parts.append("Profile photo")
        if self.proposed_identity_proof:
            parts.append("Identity proof")
        if self.proposed_registration_certificate:
            parts.append("Registration certificate")
        pd = self.proposed_data or {}
        addr_keys = _DOCTOR_PROFILE_CHANGE_ADDRESS_KEYS.intersection(pd.keys())
        if addr_keys and any(doctor_profile_field_changed(doctor, k, pd[k]) for k in addr_keys):
            parts.append("Clinic address (street, city, state, or PIN)")
        for key in sorted(k for k in pd if k not in _DOCTOR_PROFILE_CHANGE_ADDRESS_KEYS):
            if doctor_profile_field_changed(doctor, key, pd[key]):
                parts.append(
                    _DOCTOR_PROFILE_CHANGE_FIELD_LABELS.get(
                        key, key.replace("_", " ").title()
                    )
                )
        return parts

    def apply_to_profile(self, reviewed_by=None, admin_note=None, *, notify_doctor=True):
        from django.utils import timezone

        proposed = self.proposed_data or {}
        for field, value in proposed.items():
            if doctor_profile_field_changed(self.doctor, field, value):
                setattr(self.doctor, field, value)
        if self.proposed_photo:
            self.doctor.photo = self.proposed_photo
        if self.proposed_identity_proof:
            self.doctor.identity_proof = self.proposed_identity_proof
        if self.proposed_registration_certificate:
            self.doctor.registration_certificate = self.proposed_registration_certificate
        self.doctor.has_pending_changes = False
        self.doctor.pending_changes_updated_at = None
        self.doctor.admin_verified = True
        self.doctor.is_approved = False
        self.doctor.profile_completed = len(self.doctor.get_pending_fields()) == 0
        self.doctor.admin_verified_at = timezone.now()
        self.doctor.admin_verified_by = reviewed_by
        self.doctor.save()

        self.status = self.Status.APPROVED
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.admin_note = admin_note
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "admin_note"])
        self.doctor.change_requests.filter(status=self.Status.PENDING).exclude(pk=self.pk).update(
            status=self.Status.REJECTED,
            reviewed_by=reviewed_by,
            reviewed_at=timezone.now(),
            admin_note="Superseded by a newer approved change request.",
        )
        if notify_doctor:
            try:
                from users.email_verification import send_doctor_profile_changes_approved_email

                send_doctor_profile_changes_approved_email(
                    self.doctor.user, self.get_summary_parts()
                )
            except Exception:
                logger.exception(
                    "Failed to send profile-change-approved email for doctor_profile_id=%s",
                    self.doctor_id,
                )
        return self.doctor
#====================================
#Doctor Availaibility
#====================================
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps  # ✅ Dynamically fetch models

@receiver(post_save, sender=DoctorProfile)
def create_doctor_availability(sender, instance, created, **kwargs):
    if created:
        DoctorAvailability = apps.get_model('consultations', 'DoctorAvailability')  # ✅ Fix Circular Import
        DoctorAvailability.objects.create(doctor=instance)


# -------------------------------------
# Patient Profile Model
# -------------------------------------
class PatientProfile(BaseProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")  # ✅ Ensure correct related_name

    class GenderChoices(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')
        OTHER = 'O', _('Other')

    gender = models.CharField(max_length=1, choices=GenderChoices.choices, null=True, blank=True, db_index=True)  # ✅ Indexed for gender-based queries
    age = models.PositiveIntegerField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    created_by_tmc = models.ForeignKey(
        "TMCProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assisted_patients",
        help_text="TMC operator that created this assisted patient record.",
    )

    class Meta(BaseProfile.Meta):
        indexes = BaseProfile.Meta.indexes + [
            models.Index(fields=['gender']),  # ✅ Index for gender-based filtering
            models.Index(fields=['is_active', 'gender']),  # ✅ Composite index for active patients by gender
            models.Index(fields=['created_by_tmc', 'created_at']),
        ]

    def __str__(self):
        return f"Patient Profile: {self.user.get_full_name() or self.user.email}"


# -------------------------------------
# TMC Operator Profile Model
# -------------------------------------
class TMCProfile(BaseProfile):
    """
    Profile for Telemedicine Center (TMC) operators.

    Includes basic details plus configuration for free consultation quotas
    that are enforced by the consultations app when booking via a TMC.
    """

    tmc_details = models.TextField(null=True, blank=True)
    clinic_name = models.CharField(max_length=160, null=True, blank=True)
    clinic_address_street = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pin_code = models.CharField(max_length=12, null=True, blank=True)
    aadhaar_document = models.FileField(upload_to="tmc/%Y/%m/%d/aadhaar/", null=True, blank=True)
    user_photo = models.ImageField(upload_to="tmc/%Y/%m/%d/user_photos/", null=True, blank=True)
    clinic_front_photo = models.ImageField(upload_to="tmc/%Y/%m/%d/clinic_front/", null=True, blank=True)
    profile_completed = models.BooleanField(default=False, db_index=True)
    admin_verified = models.BooleanField(default=False, db_index=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    has_pending_changes = models.BooleanField(default=False, db_index=True)
    pending_changes_updated_at = models.DateTimeField(null=True, blank=True)

    # ✅ Quota configuration for free consultations routed via this TMC
    free_consultation_quota = models.PositiveIntegerField(
        default=0,
        help_text="Total number of free consultations allowed for this TMC.",
    )
    free_consultations_used = models.PositiveIntegerField(
        default=0,
        help_text="Number of free consultations already used.",
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Discount percentage applied after free consultations are exhausted.",
    )
    discounted_consultation_quota = models.PositiveIntegerField(
        default=0,
        help_text="Number of discounted consultations allowed after free quota.",
    )
    discounted_consultations_used = models.PositiveIntegerField(
        default=0,
        help_text="Number of discounted consultations already used.",
    )

    class Meta(BaseProfile.Meta):
        indexes = BaseProfile.Meta.indexes + [
            models.Index(fields=["is_active", "free_consultation_quota"]),
            models.Index(fields=["city", "state"]),
            models.Index(fields=["profile_completed", "admin_verified", "is_approved"]),
        ]

    def get_profile_completion_percentage(self):
        required_fields = {
            "clinic_name": self.clinic_name,
            "clinic_address_street": self.clinic_address_street,
            "city": self.city,
            "state": self.state,
            "pin_code": self.pin_code,
            "aadhaar_document": self.aadhaar_document,
            "user_photo": self.user_photo,
            "clinic_front_photo": self.clinic_front_photo,
            "qualification_documents": self.qualification_documents.exists() if self.pk else False,
        }
        filled_count = sum(1 for value in required_fields.values() if value)
        total_count = len(required_fields)
        return int((filled_count / total_count) * 100) if total_count else 0

    def get_pending_fields(self):
        required_fields = {
            "clinic_name": self.clinic_name,
            "clinic_address_street": self.clinic_address_street,
            "city": self.city,
            "state": self.state,
            "pin_code": self.pin_code,
            "aadhaar_document": self.aadhaar_document,
            "user_photo": self.user_photo,
            "clinic_front_photo": self.clinic_front_photo,
            "qualification_documents": self.qualification_documents.exists() if self.pk else False,
        }
        return [field for field, value in required_fields.items() if not value]

    @property
    def free_consultations_remaining(self) -> int:
        """Number of free consultations still available."""
        return max(self.free_consultation_quota - self.free_consultations_used, 0)

    def increment_free_usage(self, count: int = 1) -> None:
        """Increment used free consultations safely."""
        self.free_consultations_used = models.F("free_consultations_used") + count
        self.save(update_fields=["free_consultations_used"])

    @property
    def discounted_consultations_remaining(self) -> int:
        """Number of discounted consultations still available."""
        return max(self.discounted_consultation_quota - self.discounted_consultations_used, 0)

    def increment_discount_usage(self, count: int = 1) -> None:
        """Increment used discounted consultations safely."""
        self.discounted_consultations_used = models.F("discounted_consultations_used") + count
        self.save(update_fields=["discounted_consultations_used"])

    def __str__(self):
        return f"TMC Operator Profile: {self.user.get_full_name() or self.user.email}"


class TMCQualificationDocument(models.Model):
    class ExamName(models.TextChoices):
        SECONDARY = "SECONDARY", "Secondary"
        SENIOR_SECONDARY = "SENIOR_SECONDARY", "Senior Secondary"
        UG = "UG", "UG"
        CERTIFICATE = "CERTIFICATE", "Certificate"
        OTHER = "OTHER", "Other"

    tmc = models.ForeignKey(TMCProfile, on_delete=models.CASCADE, related_name="qualification_documents")
    exam_name = models.CharField(max_length=32, choices=ExamName.choices)
    board_or_university = models.CharField(max_length=180)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    document = models.FileField(upload_to="tmc/%Y/%m/%d/qualification_documents/")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["exam_name", "-created_at"]
        indexes = [
            models.Index(fields=["tmc", "exam_name"]),
        ]

    def __str__(self):
        return f"{self.tmc.user.email} - {self.get_exam_name_display()}"


class TMCProfileChangeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    tmc = models.ForeignKey(TMCProfile, on_delete=models.CASCADE, related_name="profile_change_requests")
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tmc_profile_change_requests",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    proposed_data = models.JSONField(default=dict, blank=True)
    proposed_aadhaar_document = models.FileField(upload_to="tmc/%Y/%m/%d/pending/aadhaar/", null=True, blank=True)
    proposed_user_photo = models.ImageField(upload_to="tmc/%Y/%m/%d/pending/user_photos/", null=True, blank=True)
    proposed_clinic_front_photo = models.ImageField(upload_to="tmc/%Y/%m/%d/pending/clinic_front/", null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_tmc_profile_change_requests",
    )
    admin_note = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at"]
        indexes = [models.Index(fields=["tmc", "status", "-requested_at"])]

    def apply_to_profile(self, reviewed_by=None, admin_note=None):
        from django.utils import timezone

        for field, value in (self.proposed_data or {}).items():
            setattr(self.tmc, field, value)
        if self.proposed_aadhaar_document:
            self.tmc.aadhaar_document = self.proposed_aadhaar_document
        if self.proposed_user_photo:
            self.tmc.user_photo = self.proposed_user_photo
        if self.proposed_clinic_front_photo:
            self.tmc.clinic_front_photo = self.proposed_clinic_front_photo
        self.tmc.profile_completed = len(self.tmc.get_pending_fields()) == 0
        self.tmc.has_pending_changes = False
        self.tmc.pending_changes_updated_at = None
        self.tmc.save()
        self.status = self.Status.APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.admin_note = admin_note
        self.save(update_fields=["status", "reviewed_at", "reviewed_by", "admin_note"])
        return self.tmc

    def __str__(self):
        return f"TMCProfileChangeRequest({self.tmc.user.email}, {self.status})"


class TMCQualificationChangeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class Action(models.TextChoices):
        ADD = "ADD", "Add document"
        REMOVE = "REMOVE", "Remove document"

    tmc = models.ForeignKey(TMCProfile, on_delete=models.CASCADE, related_name="qualification_change_requests")
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tmc_qualification_change_requests",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    action = models.CharField(max_length=10, choices=Action.choices)
    target_document = models.ForeignKey(
        TMCQualificationDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="change_requests",
    )
    exam_name = models.CharField(max_length=32, choices=TMCQualificationDocument.ExamName.choices, null=True, blank=True)
    board_or_university = models.CharField(max_length=180, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    document = models.FileField(upload_to="tmc/%Y/%m/%d/pending/qualification_documents/", null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_tmc_qualification_change_requests",
    )
    admin_note = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at"]
        indexes = [models.Index(fields=["tmc", "status", "-requested_at"])]

    def apply(self, reviewed_by=None, admin_note=None):
        from django.utils import timezone

        if self.action == self.Action.ADD:
            TMCQualificationDocument.objects.create(
                tmc=self.tmc,
                exam_name=self.exam_name,
                board_or_university=self.board_or_university or "",
                percentage=self.percentage,
                document=self.document,
            )
        elif self.target_document_id:
            self.target_document.delete()
        self.status = self.Status.APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.admin_note = admin_note
        self.save(update_fields=["status", "reviewed_at", "reviewed_by", "admin_note"])
        self.tmc.profile_completed = len(self.tmc.get_pending_fields()) == 0
        self.tmc.has_pending_changes = False
        self.tmc.pending_changes_updated_at = None
        self.tmc.save(update_fields=["profile_completed", "has_pending_changes", "pending_changes_updated_at", "updated_at"])
        return self

    def __str__(self):
        return f"TMCQualificationChangeRequest({self.tmc.user.email}, {self.action}, {self.status})"
