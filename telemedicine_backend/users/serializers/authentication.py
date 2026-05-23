from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from ..models.users import User  # Corrected import path
from ..models.profiles import DoctorProfile, PatientProfile, TMCProfile  # Corrected import path
from django.contrib.auth import get_user_model
# -------------------------------------
# User Registration Serializer
# -------------------------------------
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models.profiles import DoctorProfile, PatientProfile, TMCProfile

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration, handling role-based profile creation.
    """
    role = serializers.ChoiceField(choices=["doctor", "patient", "tmc"], required=True, write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    
    # Profile fields (only for Patients)
    gender = serializers.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False)
    age = serializers.IntegerField(required=False, min_value=0)
    address = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password', 'role', 'gender', 'age', 'address']

    def validate_email(self, value):
        """
        Ensure the email is unique.
        Note: Final validation happens at database level to handle race conditions.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_phone_number(self, value):
        """
        Ensure the phone number is unique.
        Note: Final validation happens at database level to handle race conditions.
        """
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value
    
    # ✅ Removed create() method - registration logic now handled in view with transactions
    # This removes duplicate code and ensures atomic operations

# -------------------------------------
# User Login Serializer
# -------------------------------------
class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login. Validates credentials and generates JWT tokens.
    """
    email = serializers.EmailField(
        max_length=255, 
        required=True, 
        help_text="Email address of the user."
    )
    password = serializers.CharField(
        write_only=True, 
        max_length=68, 
        required=True, 
        help_text="User's password."
    )
    tokens = serializers.SerializerMethodField(
        help_text="JWT access and refresh tokens upon successful login."
    )

    def get_tokens(self, obj):
        """
        Generates JWT tokens for the authenticated user.
        """
        user = obj['user']
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def validate(self, data):
        """
        Validates the provided email and password.
        """
        email = data.get('email', '')
        password = data.get('password', '')

        # Authenticate user
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError({
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password. Please try again."
                }
            })
        if not user.is_active:
            raise serializers.ValidationError({
                "error": {
                    "code": "INACTIVE_ACCOUNT",
                    "message": "This account is inactive. Contact support."
                }
            })

        data['user'] = user
        return data
