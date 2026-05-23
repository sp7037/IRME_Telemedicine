import logging
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from ..serializers.authentication import UserRegisterSerializer, UserLoginSerializer
from ..email_verification import (
    create_doctor_email_otp,
    create_patient_email_otp,
    create_tmc_email_otp,
    send_doctor_verification_email,
    send_patient_verification_email,
    send_tmc_verification_email,
    verify_registration_email_otp,
    resend_registration_otp_for_user,
)
from django.conf import settings
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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "registration"

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
                    is_email_verified=False,
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
                otp_handlers = {
                    "doctor": (create_doctor_email_otp, send_doctor_verification_email),
                    "patient": (create_patient_email_otp, send_patient_verification_email),
                    "tmc": (create_tmc_email_otp, send_tmc_verification_email),
                }
                if role in otp_handlers:
                    create_otp_fn, send_email_fn = otp_handlers[role]
                    otp = create_otp_fn(user)
                    send_email_fn(user, otp)
                    detail_msgs = {
                        "doctor": "Doctor registered. Verify email before login.",
                        "patient": "Patient registered. Verify email before login.",
                        "tmc": "Telemedicine center registered. Verify email before login.",
                    }
                    response_data = {
                        "detail": detail_msgs[role],
                        "next_step": "VERIFY_EMAIL",
                        "email": user.email,
                        "user_id": user.id,
                    }
                    if settings.DEBUG:
                        response_data["dev_otp"] = otp
                    return Response(response_data, status=status.HTTP_201_CREATED)

                return Response(
                    {"error": {"role": ["Unsupported registration role."]}},
                    status=status.HTTP_400_BAD_REQUEST,
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

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if not user.is_email_verified:
            return Response(
                {
                    "error": {
                        "code": "EMAIL_NOT_VERIFIED",
                        "message": "Please verify your email before signing in.",
                    },
                    "next_step": "VERIFY_EMAIL",
                    "email": user.email,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ✅ Generate JWT Tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        logger.info(f"✅ Login Successful: {user.email}")

        if user.is_staff or user.is_superuser:
            user_type = "admin"
        elif user.is_patient:
            user_type = "patient"
        elif user.is_doctor:
            user_type = "doctor"
        else:
            user_type = "tmc"

        return Response(
            {
                "email": user.email,
                "tokens": {
                    "refresh": str(refresh),
                    "access": access_token,
                },
                "user_type": user_type,
                "is_email_verified": user.is_email_verified,
                "doctor_onboarding": self._doctor_onboarding_payload(user),
            },
            status=status.HTTP_200_OK,
        )

    def _doctor_onboarding_payload(self, user):
        if not user.is_doctor:
            return None
        profile = getattr(user, "doctor_profile", None)
        if not profile:
            return {
                "profile_completed": False,
                "admin_verified": False,
                "is_approved": False,
                "next_step": "COMPLETE_PROFILE",
            }
        if not profile.profile_completed:
            next_step = "COMPLETE_PROFILE"
        elif not profile.admin_verified:
            next_step = "AWAIT_PROFILE_VERIFICATION"
        elif not profile.is_approved:
            next_step = "AWAIT_CONSULTATION_APPROVAL"
        else:
            next_step = "DASHBOARD"
        return {
            "profile_completed": profile.profile_completed,
            "admin_verified": profile.admin_verified,
            "is_approved": profile.is_approved,
            "next_step": next_step,
        }


class VerifyRegistrationEmailAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email_otp"

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        if not email or not otp:
            return Response({"error": "email and otp are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            verify_registration_email_otp(email, otp)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Email verified. You can now sign in."}, status=status.HTTP_200_OK)


class ResendRegistrationEmailOTPAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email_otp"

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        if not email:
            return Response({"error": "email is required."}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({"error": "Account not found."}, status=status.HTTP_404_NOT_FOUND)
        if user.is_email_verified:
            return Response({"detail": "Email is already verified."}, status=status.HTTP_200_OK)
        try:
            otp = resend_registration_otp_for_user(user)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        data = {"detail": "Verification OTP resent.", "email": user.email}
        if settings.DEBUG:
            data["dev_otp"] = otp
        return Response(data, status=status.HTTP_200_OK)

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

    permission_classes = [AllowAny]

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
