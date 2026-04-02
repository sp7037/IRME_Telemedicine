# Code Improvements - Implementation Guide

## Quick Fixes for Critical Issues

### 1. Fix Registration with Transaction (CRITICAL)

**File**: `telemedicine_project/users/views/authentication.py`

Replace the `post` method in `RegisterAPIView`:

```python
from django.db import transaction

@transaction.atomic
def post(self, request):
    logger.info(f"📩 Incoming Registration Request: {request.data.get('email')}")
    
    serializer = self.serializer_class(data=request.data)
    if not serializer.is_valid():
        logger.error(f"❌ Registration Failed: {serializer.errors}")
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    role = validated_data.pop("role", None)
    
    patient_data = {
        "gender": validated_data.pop("gender", None),
        "age": validated_data.pop("age", None),
        "address": validated_data.pop("address", None),
    } if role == "patient" else {}
    
    try:
        with transaction.atomic():
            # Create user with role flags in one operation
            user = User.objects.create_user(
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                email=validated_data["email"],
                phone_number=validated_data["phone_number"],
                password=validated_data["password"],
                is_doctor=(role == "doctor"),
                is_patient=(role == "patient"),
                is_tmc_operator=(role == "tmc"),
            )
            
            # Create Profile Based on Role (atomic with user creation)
            if role == "doctor":
                DoctorProfile.objects.create(user=user)
            elif role == "patient":
                PatientProfile.objects.create(
                    user=user, 
                    **{k: v for k, v in patient_data.items() if v is not None}
                )
            elif role == "tmc":
                TMCProfile.objects.create(user=user)
            
            # Cache with consistent key strategy
            cache.set(f"user_{user.id}", user.id, timeout=300)
            cache.delete(f"profile_{user.id}")  # Ensure fresh profile fetch
            
            logger.info(f"✅ Registration Success: {user.email} ({role})")
            return Response(
                {"detail": "User registered successfully", "user_id": user.id}, 
                status=status.HTTP_201_CREATED
            )
    
    except IntegrityError as e:
        logger.error(f"❌ Registration Failed: Duplicate entry - {str(e)}")
        if 'email' in str(e).lower():
            return Response(
                {"error": {"email": ["A user with this email already exists."]}}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        elif 'phone' in str(e).lower():
            return Response(
                {"error": {"phone_number": ["A user with this phone number already exists."]}}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {"error": "User already exists"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.exception(f"❌ Registration Failed Unexpectedly: {str(e)}")
        return Response(
            {"error": "Registration failed. Please try again."}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

---

### 2. Fix N+1 Query in Profile Serializer

**File**: `telemedicine_project/users/views/profiles.py`

Update `_get_or_create_profile` method:

```python
def _get_or_create_profile(self, user):
    """🔄 Fetches or Creates the Role-Based Profile Efficiently."""
    role_mapping = {
        "is_doctor": (DoctorProfile, DoctorProfileSerializer),
        "is_patient": (PatientProfile, PatientProfileSerializer),
        "is_tmc_operator": (TMCProfile, TMCProfileSerializer),
    }
    
    for role, (model, serializer) in role_mapping.items():
        if getattr(user, role, False):
            # ✅ Use select_related to avoid N+1 queries
            profile, created = model.objects.select_related("user").get_or_create(user=user)
            return profile, serializer
    return None, None
```

---

### 3. Add Database Indexes to Models

**File**: `telemedicine_project/users/models/profiles.py`

Add Meta classes with indexes:

```python
class BaseProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="%(class)s_profile")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['-created_at']),  # For recent-first queries
        ]
    
    def __str__(self):
        return f"Profile of {self.user.get_full_name() or self.user.email}"


class DoctorProfile(BaseProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    qualification = models.CharField(max_length=100, null=True, blank=True)
    specialty = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    experience = models.CharField(max_length=100, null=True, blank=True)
    license_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
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
    
    class Meta(BaseProfile.Meta):
        indexes = BaseProfile.Meta.indexes + [
            models.Index(fields=['specialty']),
            models.Index(fields=['license_number']),
        ]
    
    def save(self, *args, **kwargs):
        if self.license_number:
            self.license_number = self.license_number.upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Doctor Profile: {self.user.get_full_name() or self.user.email}"
```

---

### 4. Fix Settings for Production Readiness

**File**: `telemedicine_project/telemedicine_project/settings.py`

Add at the top:
```python
import os
from pathlib import Path
```

Update security settings:
```python
# Security Settings
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-9e_*31h_zssc!a^6a5ad3ys@8ir#ys)xdjzn@bz7ddyw!bi72u')  # Use env var in production

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'telemedicine25'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'Only1@123'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'client_encoding': 'UTF8',
            'connect_timeout': 10,
            'application_name': 'django'
        },
    }
}

# Session Security
SESSION_COOKIE_SECURE = not DEBUG  # Only secure in production
CSRF_COOKIE_SECURE = not DEBUG
```

---

### 5. Improve Profile Update with Transaction

**File**: `telemedicine_project/users/views/profiles.py`

Update `patch` method:

```python
from django.db import transaction

@transaction.atomic
def patch(self, request):
    """Updates user profile details and invalidates cache."""
    user = request.user
    
    try:
        # ✅ Bulk Update User Fields within transaction
        user_data = {
            key: request.data.get(key) 
            for key in ["first_name", "last_name", "email", "phone_number"] 
            if request.data.get(key) and key in request.data
        }
        
        if user_data:
            # Validate email uniqueness if email is being changed
            if 'email' in user_data and user_data['email'] != user.email:
                if User.objects.filter(email=user_data['email']).exists():
                    return Response(
                        {"error": {"email": ["This email is already registered."]}},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            # Validate phone uniqueness if phone is being changed
            if 'phone_number' in user_data and user_data['phone_number'] != user.phone_number:
                if User.objects.filter(phone_number=user_data['phone_number']).exists():
                    return Response(
                        {"error": {"phone_number": ["This phone number is already registered."]}},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            User.objects.filter(id=user.id).update(**user_data)
            user.refresh_from_db()  # Refresh user object
        
        profile, profile_serializer = self._get_or_create_profile(user)
        if not profile:
            return Response(
                {"error": {"code": "INVALID_ROLE", "message": "User role is invalid or unsupported."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # ✅ Partial Update on Profile
        serializer = profile_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # 🚀 Invalidate Cache After Update
        cache.delete(f"profile_{user.id}")
        cache.delete(f"user_{user.id}")
        
        return Response(
            {"user": UserProfileSerializer(user).data, "profile": serializer.data},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.exception(f"Profile update failed: {str(e)}")
        return Response(
            {"error": "Profile update failed. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

---

### 6. Add Role Validation

**File**: `telemedicine_project/users/models/users.py`

Add validation to User model:

```python
from django.core.exceptions import ValidationError

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, blank=False, null=False, db_index=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True, db_index=True)
    
    is_doctor = models.BooleanField(default=False, db_index=True)
    is_patient = models.BooleanField(default=False, db_index=True)
    is_tmc_operator = models.BooleanField(default=False, db_index=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    def clean(self):
        """Validate that user has exactly one role."""
        roles = [self.is_doctor, self.is_patient, self.is_tmc_operator]
        if sum(roles) != 1:
            raise ValidationError("User must have exactly one role (doctor, patient, or TMC operator).")
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Run validation
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.email
```

---

### 7. Standardize Cache Keys

**File**: `telemedicine_project/users/views/profiles.py` and `authentication.py`

Use consistent cache key namespace:

```python
# Cache key helper
def get_user_cache_key(user_id):
    return f"users:user:{user_id}"

def get_profile_cache_key(user_id):
    return f"users:profile:{user_id}"

# Usage:
cache.set(get_user_cache_key(user.id), user.id, timeout=300)
cache.set(get_profile_cache_key(user.id), response_data, timeout=cache_expiry)
cache.get(get_profile_cache_key(user.id))
```

---

## Migration Steps

1. **Create migration for indexes**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Update settings**:
   - Create `.env` file with secrets
   - Install `python-decouple` or `django-environ`

3. **Test thoroughly**:
   - Registration flow
   - Profile updates
   - Error scenarios
   - Concurrent requests

4. **Monitor**:
   - Database query counts
   - Response times
   - Error rates

---

## Testing Recommendations

```python
# tests/test_registration.py
from django.test import TestCase
from django.db import transaction

class RegistrationTestCase(TestCase):
    def test_registration_atomic(self):
        """Test that registration is atomic."""
        # Test that if profile creation fails, user is not created
        pass
    
    def test_concurrent_registration(self):
        """Test race condition handling."""
        pass
    
    def test_cache_invalidation(self):
        """Test cache is properly invalidated on update."""
        pass
```

---

## Load Testing

Use `locustfile.py` (already in project) or tools like:
- Apache JMeter
- Locust
- wrk

Test scenarios:
- 100 concurrent registrations
- 1000 profile fetches/second
- Mixed workload simulation

