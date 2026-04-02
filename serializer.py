from django.core.validators import RegexValidator
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, DoctorProfile, PatientProfile, TMCProfile

# -------------------------------------
# User Registration Serializer
# -------------------------------------
class UserRegisterSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=["doctor", "patient", "tmc"], write_only=True)  # Role not part of User model
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_no', 'password', 'role']

    def validate_password(self, value):
        # Add password complexity validation
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must include at least one digit.")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError("Password must include at least one letter.")
        return value

    def create(self, validated_data):
        role = validated_data.pop('role')  # Extract role
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)

        # Set role-specific flags and profiles
        if role == "doctor":
            user.is_doctor = True
            DoctorProfile.objects.create(user=user)
        elif role == "patient":
            user.is_patient = True
            PatientProfile.objects.create(user=user)
        elif role == "tmc":
            user.is_tmc_operator = True
            TMCProfile.objects.create(user=user)

        user.save()
        return user

# -------------------------------------
# User Login Serializer
# -------------------------------------
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, required=True)
    password = serializers.CharField(write_only=True, max_length=68, required=True)
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        user = obj['user']
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def validate(self, data):
        email = data.get('email', '')
        password = data.get('password', '')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials. Please try again.")
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive. Contact support.")

        data['user'] = user
        return data

# -------------------------------------
# User Profile Serializer
# -------------------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()  # Dynamically determine role

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_no', 'role']

    def get_role(self, obj):
        if obj.is_doctor:
            return "doctor"
        elif obj.is_patient:
            return "patient"
        elif obj.is_tmc_operator:
            return "tmc"
        return "unknown"

# -------------------------------------
# Doctor Profile Serializer
# -------------------------------------
class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = [
            'qualification', 'specialty', 'experience', 'license_no',
            'practice_type', 'date_of_birth', 'photo', 'signature',
            'hospital_or_clinic_name'
        ]

# -------------------------------------
# Patient Profile Serializer
# -------------------------------------
class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['gender', 'age', 'address']

# -------------------------------------
# TMC Profile Serializer
# -------------------------------------
class TMCProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TMCProfile
        fields = ['tmc_details']
