import logging
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.core.cache import cache

from users.models.users import User
from ..models.profiles import DoctorProfile, PatientProfile, TMCProfile
from ..serializers.profiles import (
    UserProfileSerializer,
    DoctorProfileSerializer,
    PatientProfileSerializer,
    TMCProfileSerializer,
)

logger = logging.getLogger(__name__)

# ✅ Standardized cache key helpers
def get_user_cache_key(user_id):
    """Get standardized cache key for user data."""
    return f"users:user:{user_id}"

def get_profile_cache_key(user_id):
    """Get standardized cache key for profile data."""
    return f"users:profile:{user_id}"

class UserProfileAPIView(APIView):
    """🚀 Optimized API for fetching and updating user profiles."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request):
        """Fetches the authenticated user's profile with efficient caching."""
        user = request.user
        cache_key = get_profile_cache_key(user.id)

        # ⏳ Dynamic Cache Expiry based on User Type
        cache_expiry = 300 if user.is_active else 600  # 🚀 Cache active users for 5 mins, inactive for 10 mins

        # ✅ Check Cache First
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        # 🔄 Fetch or Create Profile with optimized query (select_related to avoid N+1)
        profile, profile_serializer = self._get_or_create_profile(user)
        if not profile:
            return Response(
                {"error": {"code": "INVALID_ROLE", "message": "User role is invalid or unsupported."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Serialize Data (profile already has user via select_related, no extra queries)
        user_serializer = UserProfileSerializer(user)
        profile_data = profile_serializer(profile).data
        response_data = {"user": user_serializer.data, "profile": profile_data}

        # 🚀 Cache profile dynamically with standardized key
        cache.set(cache_key, response_data, timeout=cache_expiry)
    
        return Response(response_data, status=status.HTTP_200_OK)

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
                
                User.objects.filter(id=user.id).update(**user_data)  # 🚀 Uses Bulk Update (Faster)
                user.refresh_from_db()  # Refresh user object

            # ✅ Fetch profile with select_related to avoid N+1 queries
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

            # 🚀 Invalidate Cache After Update with standardized keys
            cache.delete(get_profile_cache_key(user.id))
            cache.delete(get_user_cache_key(user.id))

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

    def _get_or_create_profile(self, user):
        """
        🔄 Fetches or Creates the Role-Based Profile Efficiently.
        Uses select_related to prevent N+1 queries when accessing user attributes.
        """
        role_mapping = {
            "is_doctor": (DoctorProfile, DoctorProfileSerializer),
            "is_patient": (PatientProfile, PatientProfileSerializer),
            "is_tmc_operator": (TMCProfile, TMCProfileSerializer),
        }

        for role, (model, serializer) in role_mapping.items():
            if getattr(user, role, False):
                # ✅ Uses select_related to fetch user in same query, preventing N+1
                profile, created = model.objects.select_related("user").get_or_create(user=user)
                return profile, serializer
        return None, None


class TMCPatientsAPIView(APIView):
    """List active patients for TMC consultation initiation."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request):
        if not (getattr(request.user, "tmc_profile", None) or getattr(request.user, "tmcprofile_profile", None)):
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        patients = PatientProfile.objects.select_related("user").filter(is_active=True).order_by("-created_at")[:200]
        data = [
            {
                "id": patient.id,
                "name": patient.user.get_full_name() or patient.user.email,
                "email": patient.user.email,
                "phone_number": patient.user.phone_number,
            }
            for patient in patients
        ]
        return Response(data, status=200)

