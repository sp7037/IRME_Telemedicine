from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializer import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
)
from .models import DoctorProfile, PatientProfile, TMCProfile

# Get the User model
User = get_user_model()

# -------------------------------------
# User Registration View
# Handles registration for all roles (doctor, patient, tmc)
# -------------------------------------
class RegisterAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer

    def post(self, request):
        # Get user data from the request
        user_data = request.data
        # Pass data to the serializer for validation
        serializer = self.serializer_class(data=user_data)
        serializer.is_valid(raise_exception=True)
        # Save the user (and role-specific profiles, if applicable)
        user = serializer.save()
        # Return the serialized user data
        return Response({"detail": "User registered successfully", "user": serializer.data}, status=status.HTTP_201_CREATED)

# -------------------------------------
# User Login View
# Handles login for all roles
# -------------------------------------
class LoginAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        # Get login data from the request
        login_data = request.data
        # Pass data to the serializer for validation
        serializer = self.serializer_class(data=login_data)
        serializer.is_valid(raise_exception=True)
        # Return tokens and user information
        return Response(serializer.data, status=status.HTTP_200_OK)

# -------------------------------------
# User Logout View
# Handles token blacklisting to log out users
# -------------------------------------
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Blacklist the provided refresh token
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# -------------------------------------
# User Profile View
# Handles fetching and updating profile information for all roles
# -------------------------------------
from .serializer import (
    UserProfileSerializer,
    DoctorProfileSerializer,
    PatientProfileSerializer,
    TMCProfileSerializer,
)
from .models import DoctorProfile, PatientProfile, TMCProfile

class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Fetch role-specific profile and serializer
        profile, profile_serializer = self._get_profile_and_serializer(user)

        if not profile:
            return Response({"detail": "Invalid user role"}, status=status.HTTP_400_BAD_REQUEST)

        # Serialize user and profile data
        user_serializer = UserProfileSerializer(user)
        profile_data = profile_serializer(profile).data

        return Response({
            "user": user_serializer.data,
            "profile": profile_data
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user

        # Update basic user fields
        user_data = {
            'first_name': request.data.get('first_name'),
            'last_name': request.data.get('last_name'),
            'email': request.data.get('email'),
            'phone_no': request.data.get('phone_no'),
        }
        for field, value in user_data.items():
            if value is not None:
                setattr(user, field, value)
        user.save()

        # Fetch role-specific profile and serializer
        profile, profile_serializer = self._get_profile_and_serializer(user)

        if not profile:
            return Response({"detail": "Invalid user role"}, status=status.HTTP_400_BAD_REQUEST)

        # Update profile fields
        profile_data = {key: value for key, value in request.data.items() if key not in user_data}
        serializer = profile_serializer(profile, data=profile_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_profile_and_serializer(self, user):
        """
        Utility method to get the profile instance and corresponding serializer
        based on the user's role.
        """
        if user.is_doctor:
            return DoctorProfile.objects.get(user=user), DoctorProfileSerializer
        elif user.is_patient:
            return PatientProfile.objects.get(user=user), PatientProfileSerializer
        elif user.is_tmc_operator:
            return TMCProfile.objects.get(user=user), TMCProfileSerializer
        return None, None


# -------------------------------------
# Refresh Token View
# Handles refreshing the access token using a valid refresh token
# -------------------------------------
class RefreshTokenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return Response({"detail": "Authorization header is missing"}, status=400)
        if not auth_header.startswith('Bearer '):
            return Response({"detail": "Invalid Authorization header format"}, status=400)

        access_token = auth_header.split(' ')[1]
        try:
            # Decode the access token and fetch the user
            decoded_access_token = AccessToken(access_token)
            user_id = decoded_access_token.payload.get('user_id')
            user = User.objects.get(id=user_id)
            # Generate a new refresh token
            refresh_token = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh_token),
                "access": str(decoded_access_token)
            }, status=200)
        except TokenError as e:
            return Response({"detail": str(e)}, status=400)
