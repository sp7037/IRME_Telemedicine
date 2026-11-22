import logging
import uuid
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.core.cache import cache

from users.models.users import User
from ..models.profiles import (
    DoctorProfile,
    PatientProfile,
    TMCProfile,
    TMCProfileChangeRequest,
    TMCQualificationChangeRequest,
    TMCQualificationDocument,
)
from ..serializers.profiles import (
    UserProfileSerializer,
    DoctorProfileSerializer,
    PatientProfileSerializer,
    TMCProfileSerializer,
    TMCQualificationDocumentSerializer,
)

DOCTOR_PROFESSIONAL_PROFILE_FIELDS = {
    "qualification",
    "degree",
    "college_university_name",
    "passing_year",
    "specialty",
    "experience",
    "license_number",
    "registration_number",
    "state_medical_council",
    "major_diseases_specializations",
    "previous_hospitals_served",
    "hospital_or_clinic_name",
    "clinic_address_street",
    "city",
    "state",
    "pin_code",
    "consultation_modes",
    "consultation_fee",
    "max_daily_consultations",
    "photo",
    "identity_proof",
    "registration_certificate",
}

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

        if "email" in request.data and request.data.get("email") != user.email:
            return Response(
                {
                    "error": {
                        "email": [
                            "Email cannot be changed from this screen. Register a new verified email or contact admin support."
                        ]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_doctor:
            blocked = sorted(DOCTOR_PROFESSIONAL_PROFILE_FIELDS.intersection(request.data.keys()))
            if blocked:
                return Response(
                    {
                        "error": {
                            "doctor_profile": [
                                "Doctor professional details must be updated from the doctor profile workflow and require admin review."
                            ],
                            "fields": blocked,
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            # ✅ Bulk Update User Fields within transaction
            user_data = {
                key: request.data.get(key) 
                for key in ["first_name", "last_name", "phone_number"] 
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
        tmc = getattr(request.user, "tmc_profile", None) or getattr(request.user, "tmcprofile_profile", None)
        if not tmc:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        patients = PatientProfile.objects.select_related("user").filter(
            is_active=True,
            created_by_tmc=tmc,
        ).order_by("-created_at")[:200]
        data = [
            {
                "id": patient.id,
                "name": patient.user.get_full_name() or patient.user.email,
                "email": patient.user.email,
                "phone_number": patient.user.phone_number,
                "age": patient.age,
                "gender": patient.gender,
            }
            for patient in patients
        ]
        return Response(data, status=200)

    @transaction.atomic
    def post(self, request):
        tmc = getattr(request.user, "tmc_profile", None) or getattr(request.user, "tmcprofile_profile", None)
        if not tmc:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        name = (request.data.get("name") or "").strip()
        age = request.data.get("age")
        gender = request.data.get("gender")
        if not name or age in (None, "") or gender not in {"M", "F", "O"}:
            return Response({"error": "Patient name, age, and sex are required."}, status=400)
        try:
            age_value = int(age)
        except (TypeError, ValueError):
            return Response({"error": "Age must be a number."}, status=400)
        if age_value < 0 or age_value > 120:
            return Response({"error": "Age must be between 0 and 120."}, status=400)
        parts = name.split()
        first_name = parts[0]
        last_name = " ".join(parts[1:])
        email = f"tmc{tmc.id}.patient.{uuid.uuid4().hex[:12]}@local.irme.in"
        user = User.objects.create_user(
            email=email,
            password=None,
            is_patient=True,
            is_email_verified=True,
            first_name=first_name,
            last_name=last_name,
        )
        profile = PatientProfile.objects.create(
            user=user,
            age=age_value,
            gender=gender,
            created_by_tmc=tmc,
        )
        return Response(
            {
                "id": profile.id,
                "name": profile.user.get_full_name() or profile.user.email,
                "email": profile.user.email,
                "age": profile.age,
                "gender": profile.gender,
            },
            status=201,
        )


class TMCProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _get_profile(self, user):
        return getattr(user, "tmc_profile", None) or getattr(user, "tmcprofile_profile", None)

    def get(self, request):
        profile = self._get_profile(request.user)
        if not profile:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        serializer = TMCProfileSerializer(profile, context={"request": request})
        return Response(serializer.data, status=200)

    @transaction.atomic
    def patch(self, request):
        profile = self._get_profile(request.user)
        if not profile:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        serializer = TMCProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        if profile.admin_verified or profile.is_approved:
            from django.utils import timezone

            file_fields = {
                "aadhaar_document": "proposed_aadhaar_document",
                "user_photo": "proposed_user_photo",
                "clinic_front_photo": "proposed_clinic_front_photo",
            }
            proposed_data = {}
            proposed_files = {}
            for field, value in serializer.validated_data.items():
                if field in file_fields:
                    proposed_files[file_fields[field]] = value
                elif str(getattr(profile, field, "") or "").strip() != str(value or "").strip():
                    proposed_data[field] = value
            if not proposed_data and not proposed_files:
                return Response({"error": "No profile changes were submitted."}, status=400)
            change = TMCProfileChangeRequest.objects.create(
                tmc=profile,
                requested_by=request.user,
                proposed_data=proposed_data,
                **proposed_files,
            )
            profile.has_pending_changes = True
            profile.pending_changes_updated_at = timezone.now()
            profile.save(update_fields=["has_pending_changes", "pending_changes_updated_at", "updated_at"])
            return Response(
                {
                    "message": "TMC profile change request submitted for admin approval. Current verified details remain active until approval.",
                    "change_request_created": True,
                    "change_request_id": change.id,
                    "profile": TMCProfileSerializer(profile, context={"request": request}).data,
                },
                status=202,
            )
        serializer.save()
        profile.refresh_from_db()
        profile.profile_completed = len(profile.get_pending_fields()) == 0
        profile.save(update_fields=["profile_completed", "updated_at"])
        cache.delete(get_profile_cache_key(request.user.id))
        return Response(
            {
                "message": "TMC profile saved.",
                "profile": TMCProfileSerializer(profile, context={"request": request}).data,
            },
            status=200,
        )


class TMCQualificationDocumentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _get_profile(self, user):
        return getattr(user, "tmc_profile", None) or getattr(user, "tmcprofile_profile", None)

    def get(self, request):
        profile = self._get_profile(request.user)
        if not profile:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        rows = profile.qualification_documents.all()
        serializer = TMCQualificationDocumentSerializer(rows, many=True, context={"request": request})
        return Response(serializer.data, status=200)

    @transaction.atomic
    def post(self, request):
        profile = self._get_profile(request.user)
        if not profile:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        serializer = TMCQualificationDocumentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        if profile.admin_verified or profile.is_approved:
            from django.utils import timezone

            change = TMCQualificationChangeRequest.objects.create(
                tmc=profile,
                requested_by=request.user,
                action=TMCQualificationChangeRequest.Action.ADD,
                **serializer.validated_data,
            )
            profile.has_pending_changes = True
            profile.pending_changes_updated_at = timezone.now()
            profile.save(update_fields=["has_pending_changes", "pending_changes_updated_at", "updated_at"])
            return Response(
                {
                    "message": "Qualification document add request submitted for admin approval.",
                    "change_request_created": True,
                    "change_request_id": change.id,
                },
                status=202,
            )
        doc = serializer.save(tmc=profile)
        profile.profile_completed = len(profile.get_pending_fields()) == 0
        profile.save(update_fields=["profile_completed", "updated_at"])
        cache.delete(get_profile_cache_key(request.user.id))
        return Response(
            TMCQualificationDocumentSerializer(doc, context={"request": request}).data,
            status=201,
        )


class TMCQualificationDocumentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _get_profile(self, user):
        return getattr(user, "tmc_profile", None) or getattr(user, "tmcprofile_profile", None)

    def delete(self, request, pk):
        profile = self._get_profile(request.user)
        if not profile:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        doc = get_object_or_404(TMCQualificationDocument, pk=pk, tmc=profile)
        if profile.admin_verified or profile.is_approved:
            from django.utils import timezone

            change = TMCQualificationChangeRequest.objects.create(
                tmc=profile,
                requested_by=request.user,
                action=TMCQualificationChangeRequest.Action.REMOVE,
                target_document=doc,
            )
            profile.has_pending_changes = True
            profile.pending_changes_updated_at = timezone.now()
            profile.save(update_fields=["has_pending_changes", "pending_changes_updated_at", "updated_at"])
            return Response(
                {
                    "message": "Qualification document removal request submitted for admin approval.",
                    "change_request_created": True,
                    "change_request_id": change.id,
                },
                status=202,
            )
        doc.delete()
        profile.profile_completed = len(profile.get_pending_fields()) == 0
        profile.save(update_fields=["profile_completed", "updated_at"])
        cache.delete(get_profile_cache_key(request.user.id))
        return Response(status=204)

