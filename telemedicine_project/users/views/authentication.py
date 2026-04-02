import logging
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from ..serializers.authentication import UserRegisterSerializer, UserLoginSerializer
from django.db.models import Q  # Import for optimized querying
from django.shortcuts import get_object_or_404

User = get_user_model()  # Custom User Model

# -------------------------------------
# User Registration View
# -------------------------------------
from ..models.profiles import DoctorProfile, PatientProfile, TMCProfile
logger = logging.getLogger(__name__)  # ✅ Logging for debugging

class RegisterAPIView(generics.GenericAPIView):
    """
    🚀 API for user registration with proper role-based profile handling.
    Uses database transactions to ensure atomicity.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer
    throttle_classes = [AnonRateThrottle]

    @transaction.atomic
    def post(self, request):
        # Log only email (not sensitive data)
        logger.info(f"📩 Registration request for: {request.data.get('email', 'N/A')}")

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            logger.error(f"❌ Registration Failed: Validation errors")
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        role = validated_data.pop("role", None)

        # Extract profile-specific fields from User data
        patient_data = {
            "gender": validated_data.pop("gender", None),
            "age": validated_data.pop("age", None),
            "address": validated_data.pop("address", None),
        } if role == "patient" else {}

        try:
            # ✅ Atomic transaction: Create User + Profile together
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

                # ✅ Create Profile Based on Role (atomic with user creation)
                if role == "doctor":
                    DoctorProfile.objects.create(user=user)
                elif role == "patient":
                    PatientProfile.objects.create(
                        user=user, 
                        **{k: v for k, v in patient_data.items() if v is not None}
                    )
                elif role == "tmc":
                    TMCProfile.objects.create(user=user)

                # ✅ Standardized cache key strategy using user.id
                cache.set(f"users:user:{user.id}", user.id, timeout=300)
                cache.delete(f"users:profile:{user.id}")  # Ensure fresh profile fetch

                logger.info(f"✅ Registration Success: {user.email} ({role})")
                return Response(
                    {"detail": "User registered successfully", "user_id": user.id}, 
                    status=status.HTTP_201_CREATED
                )

        except IntegrityError as e:
            logger.error(f"❌ Registration Failed: IntegrityError - {str(e)}")
            # Provide specific error messages
            error_msg = str(e).lower()
            if 'email' in error_msg or 'unique constraint' in error_msg and 'email' in str(request.data):
                return Response(
                    {"error": {"email": ["A user with this email already exists."]}}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif 'phone' in error_msg or 'unique constraint' in error_msg and 'phone' in str(request.data):
                return Response(
                    {"error": {"phone_number": ["A user with this phone number already exists."]}}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {"error": "User already exists. Please check email and phone number."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"❌ Registration Failed Unexpectedly: {str(e)}")
            return Response(
                {"error": "Registration failed. Please try again."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# -------------------------------------
# User Login View
# -------------------------------------
import logging
from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
logger = logging.getLogger(__name__)

class LoginAPIView(generics.GenericAPIView):
    """
    Secure user authentication with optimized caching.
    Returns JWT access & refresh tokens upon successful login.
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer  # ✅ Ensure serializer is set

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # ✅ Generate JWT Tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        logger.info(f"✅ Login Successful: {user.email}")

        return Response(
            {
                "email": user.email,
                "tokens": {
                    "refresh": str(refresh),
                    "access": access_token,
                },
                "user_type": "patient" if user.is_patient else "doctor" if user.is_doctor else "tmc",
            },
            status=status.HTTP_200_OK,
        )

# -------------------------------------
# User Logout View
# -------------------------------------
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Blacklists the provided refresh token to log out the user."""
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": {"code": "MISSING_TOKEN", "message": "Refresh token is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # 🔹 Ensure this works now
            return Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)
        except (InvalidToken, TokenError):
            return Response(
                {"error": {"code": "INVALID_TOKEN", "message": "Invalid or expired refresh token."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

# -------------------------------------
# Refresh Token View
# -------------------------------------
class RefreshTokenAPIView(APIView):
    """Handles token refresh using a valid refresh token."""

    def post(self, request):
        """Expects a valid refresh token and returns a new access token."""
        if "refresh" not in request.data:
            return Response(
                {"error": {"code": "MISSING_REFRESH_TOKEN", "message": "Refresh token is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh_token = request.data.get("refresh")  # ✅ Extract token correctly

        try:
            token = RefreshToken(refresh_token)  # ✅ Generate new access token
            return Response(
                {
                    "refresh": str(token),
                    "access": str(token.access_token),
                },
                status=status.HTTP_200_OK,
            )
        except (InvalidToken, TokenError):
            return Response(
                {"error": {"code": "INVALID_REFRESH_TOKEN", "message": "Invalid or expired refresh token."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
