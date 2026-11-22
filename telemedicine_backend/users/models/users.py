from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

# -------------------------------------
# Custom User Manager
# -------------------------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

# -------------------------------------
# Custom User Model
# -------------------------------------
class User(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(unique=True, blank=False, null=False, db_index=True)  # ✅ Index email for fast lookups
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True, db_index=True)  # ✅ Index phone

    is_doctor = models.BooleanField(default=False, db_index=True)
    is_patient = models.BooleanField(default=False, db_index=True)
    is_tmc_operator = models.BooleanField(default=False, db_index=True)
    is_email_verified = models.BooleanField(default=True, db_index=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class EmailVerificationOTP(models.Model):
    class Purpose(models.TextChoices):
        DOCTOR_EMAIL_VERIFICATION = "DOCTOR_EMAIL_VERIFICATION", "Doctor email verification"
        PATIENT_EMAIL_VERIFICATION = "PATIENT_EMAIL_VERIFICATION", "Patient email verification"
        TMC_EMAIL_VERIFICATION = "TMC_EMAIL_VERIFICATION", "TMC operator email verification"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_verification_otps")
    purpose = models.CharField(max_length=40, choices=Purpose.choices, db_index=True)
    otp_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField(db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "purpose", "consumed_at", "expires_at"]),
        ]

    @property
    def is_consumed(self):
        return self.consumed_at is not None

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at
