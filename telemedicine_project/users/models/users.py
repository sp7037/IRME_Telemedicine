from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
