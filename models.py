from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

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
    email = models.EmailField(unique=True, blank=False, null=False)
    phone_no = models.CharField(max_length=15, unique=True, null=True, blank=True)

    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)
    is_tmc_operator = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# -------------------------------------
# Abstract Base Model for Role Profiles
# -------------------------------------
class BaseProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# -------------------------------------
# Doctor Profile Model
# -------------------------------------
class DoctorProfile(BaseProfile):
    qualification = models.CharField(max_length=100, null=True, blank=True)
    specialty = models.CharField(max_length=100, null=True, blank=True)
    experience = models.CharField(max_length=100, null=True, blank=True)
    license_no = models.CharField(max_length=100, null=True, blank=True, unique=True)
    practice_type = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to="doctor_photos/", null=True, blank=True)
    signature = models.ImageField(upload_to="doctor_signatures/", null=True, blank=True)
    hospital_or_clinic_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Doctor Profile: {self.user.email}"

# -------------------------------------
# Patient Profile Model
# -------------------------------------
class PatientProfile(BaseProfile):
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Patient Profile: {self.user.email}"

# -------------------------------------
# TMC Operator Profile Model
# -------------------------------------
class TMCProfile(BaseProfile):
    tmc_details = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"TMC Operator Profile: {self.user.email}"
