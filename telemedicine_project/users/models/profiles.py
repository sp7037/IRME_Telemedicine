from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()  # Dynamically fetch the user model

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
    city = models.CharField(max_length=100, null=True, blank=True, help_text="City where the doctor practices")
    state = models.CharField(max_length=100, null=True, blank=True, help_text="State where the doctor practices")
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
            'qualification': self.qualification,
            'specialty': self.specialty,
            'experience': self.experience,
            'license_number': self.license_number,
            'registration_number': self.registration_number,
            'major_diseases_specializations': self.major_diseases_specializations,
            'photo': self.photo,
            'registration_certificate': self.registration_certificate,
        }
        
        filled_count = sum(1 for value in required_fields.values() if value)
        total_count = len(required_fields)
        
        return int((filled_count / total_count) * 100) if total_count > 0 else 0

    def get_pending_fields(self):
        """Get list of pending required fields."""
        required_fields = {
            'qualification': self.qualification,
            'specialty': self.specialty,
            'experience': self.experience,
            'license_number': self.license_number,
            'registration_number': self.registration_number,
            'major_diseases_specializations': self.major_diseases_specializations,
            'photo': self.photo,
            'registration_certificate': self.registration_certificate,
        }
        
        return [field for field, value in required_fields.items() if not value]

    def __str__(self):
        return f"Doctor Profile: {self.user.get_full_name() or self.user.email}"
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

    class Meta(BaseProfile.Meta):
        indexes = BaseProfile.Meta.indexes + [
            models.Index(fields=['gender']),  # ✅ Index for gender-based filtering
            models.Index(fields=['is_active', 'gender']),  # ✅ Composite index for active patients by gender
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

    # ✅ Quota configuration for free consultations routed via this TMC
    free_consultation_quota = models.PositiveIntegerField(
        default=0,
        help_text="Total number of free consultations allowed for this TMC.",
    )
    free_consultations_used = models.PositiveIntegerField(
        default=0,
        help_text="Number of free consultations already used.",
    )

    class Meta(BaseProfile.Meta):
        indexes = BaseProfile.Meta.indexes + [
            models.Index(fields=["is_active", "free_consultation_quota"]),
        ]

    @property
    def free_consultations_remaining(self) -> int:
        """Number of free consultations still available."""
        return max(self.free_consultation_quota - self.free_consultations_used, 0)

    def increment_free_usage(self, count: int = 1) -> None:
        """Increment used free consultations safely."""
        self.free_consultations_used = models.F("free_consultations_used") + count
        self.save(update_fields=["free_consultations_used"])

    def __str__(self):
        return f"TMC Operator Profile: {self.user.get_full_name() or self.user.email}"
