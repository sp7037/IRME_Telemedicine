# serializers/__init__.py

# Authentication serializers
from .authentication import UserRegisterSerializer, UserLoginSerializer

# Profile serializers
from .profiles import (
    UserProfileSerializer,
    DoctorProfileSerializer,
    PatientProfileSerializer,
    TMCProfileSerializer
)
