from rest_framework import serializers
from ..models.users import User  # Corrected import path
from ..models.profiles import (
    DoctorProfile,
    PatientProfile,
    TMCProfile,
    TMCProfileChangeRequest,
    TMCQualificationChangeRequest,
    TMCQualificationDocument,
)  # Corrected import path


# -------------------------------------
# User Profile Serializer
# -------------------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the basic user profile data.
    Includes a dynamic `role` field to identify user type (doctor, patient, TMC).
    """
    role = serializers.SerializerMethodField(help_text="Returns the user's role (doctor, patient, or TMC operator).")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'role']

    def get_role(self, obj):
        """
        Determines the user's role based on the flags set in the User model.
        """
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
from rest_framework import serializers
from users.models.profiles import DoctorProfile

class DoctorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Doctor Profile, ensuring all required fields are included.
    """
    first_name = serializers.CharField(source="user.first_name", read_only=True)  
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    specialty = serializers.CharField(allow_blank=True, allow_null=True)
    experience = serializers.CharField(allow_blank=True, allow_null=True)
    qualification = serializers.CharField(allow_blank=True, allow_null=True)
    hospital_or_clinic_name = serializers.CharField(allow_blank=True, allow_null=True)
    photo = serializers.SerializerMethodField()
    city = serializers.CharField(read_only=True)
    state = serializers.CharField(read_only=True)
    consultation_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    consultation_modes = serializers.ListField(read_only=True)
    profile_completed = serializers.BooleanField(read_only=True)
    admin_verified = serializers.BooleanField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "specialty",
            "experience",
            "qualification",
            "hospital_or_clinic_name",
            "city",
            "state",
            "consultation_fee",
            "consultation_modes",
            "photo",
            "profile_completed",
            "admin_verified",
            "is_approved",
        ]
    
    def get_photo(self, obj):
        """Return full URL for photo if it exists."""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


# -------------------------------------
# Patient Profile Serializer
# -------------------------------------
class PatientProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the patient-specific profile fields.
    Includes validation for gender and age.
    """
    gender = serializers.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        help_text="Gender of the patient (M=Male, F=Female, O=Other)."
    )
    age = serializers.IntegerField(
        required=True,
        min_value=0,
        help_text="Age of the patient. Must be a positive integer."
    )

    class Meta:
        model = PatientProfile
        fields = ['gender', 'age', 'address', 'created_by_tmc']
        read_only_fields = ['created_by_tmc']

    def validate_age(self, value):
        """
        Ensures the age is within a reasonable range.
        """
        if value > 120:
            raise serializers.ValidationError("Age must be less than or equal to 120.")
        return value


# -------------------------------------
# TMC Profile Serializer
# -------------------------------------
class TMCQualificationDocumentSerializer(serializers.ModelSerializer):
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = TMCQualificationDocument
        fields = [
            "id",
            "exam_name",
            "board_or_university",
            "percentage",
            "document",
            "document_url",
            "created_at",
        ]
        read_only_fields = ["id", "document_url", "created_at"]

    def validate_document(self, value):
        if not value:
            return value
        name = (getattr(value, "name", "") or "").lower()
        content_type = (getattr(value, "content_type", "") or "").lower()
        if not name.endswith(".pdf") or (content_type and content_type != "application/pdf"):
            raise serializers.ValidationError("Upload a PDF document only.")
        if getattr(value, "size", 0) > 5 * 1024 * 1024:
            raise serializers.ValidationError("PDF must be 5 MB or smaller.")
        return value

    def validate_percentage(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Percentage must be between 0 and 100.")
        return value

    def get_document_url(self, obj):
        if obj.document:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None


class TMCProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the TMC operator-specific profile fields.
    """
    completion_percentage = serializers.SerializerMethodField()
    pending_fields = serializers.SerializerMethodField()
    qualification_documents = TMCQualificationDocumentSerializer(many=True, read_only=True)
    pending_change_requests = serializers.SerializerMethodField()
    aadhaar_document_url = serializers.SerializerMethodField()
    user_photo_url = serializers.SerializerMethodField()
    clinic_front_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = TMCProfile
        fields = [
            "id",
            "tmc_details",
            "clinic_name",
            "clinic_address_street",
            "city",
            "state",
            "pin_code",
            "aadhaar_document",
            "aadhaar_document_url",
            "user_photo",
            "user_photo_url",
            "clinic_front_photo",
            "clinic_front_photo_url",
            "profile_completed",
            "admin_verified",
            "is_approved",
            "has_pending_changes",
            "pending_changes_updated_at",
            "completion_percentage",
            "pending_fields",
            "pending_change_requests",
            "qualification_documents",
            "free_consultation_quota",
            "free_consultations_used",
            "discount_percentage",
            "discounted_consultation_quota",
            "discounted_consultations_used",
        ]
        read_only_fields = [
            "id",
            "profile_completed",
            "admin_verified",
            "is_approved",
            "has_pending_changes",
            "pending_changes_updated_at",
            "completion_percentage",
            "pending_fields",
            "pending_change_requests",
            "qualification_documents",
            "free_consultation_quota",
            "free_consultations_used",
            "discount_percentage",
            "discounted_consultation_quota",
            "discounted_consultations_used",
            "aadhaar_document_url",
            "user_photo_url",
            "clinic_front_photo_url",
        ]

    def validate_tmc_details(self, value):
        """
        Ensures TMC details are provided.
        """
        if value and not value.strip():
            raise serializers.ValidationError("TMC details cannot be empty.")
        return value

    def validate_aadhaar_document(self, value):
        return self._validate_pdf(value)

    def _validate_pdf(self, value):
        if not value:
            return value
        name = (getattr(value, "name", "") or "").lower()
        content_type = (getattr(value, "content_type", "") or "").lower()
        if not name.endswith(".pdf") or (content_type and content_type != "application/pdf"):
            raise serializers.ValidationError("Upload a PDF document only.")
        if getattr(value, "size", 0) > 5 * 1024 * 1024:
            raise serializers.ValidationError("PDF must be 5 MB or smaller.")
        return value

    def get_completion_percentage(self, obj):
        return obj.get_profile_completion_percentage()

    def get_pending_fields(self, obj):
        return obj.get_pending_fields()

    def get_pending_change_requests(self, obj):
        profile_requests = [
            {
                "id": row.id,
                "type": "PROFILE",
                "status": row.status,
                "requested_at": row.requested_at,
            }
            for row in obj.profile_change_requests.filter(
                status=TMCProfileChangeRequest.Status.PENDING
            ).order_by("-requested_at")
        ]
        qualification_requests = [
            {
                "id": row.id,
                "type": f"QUALIFICATION_{row.action}",
                "status": row.status,
                "requested_at": row.requested_at,
            }
            for row in obj.qualification_change_requests.filter(
                status=TMCQualificationChangeRequest.Status.PENDING
            ).order_by("-requested_at")
        ]
        return profile_requests + qualification_requests

    def _absolute_url(self, file_field):
        if file_field:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(file_field.url)
            return file_field.url
        return None

    def get_aadhaar_document_url(self, obj):
        return self._absolute_url(obj.aadhaar_document)

    def get_user_photo_url(self, obj):
        return self._absolute_url(obj.user_photo)

    def get_clinic_front_photo_url(self, obj):
        return self._absolute_url(obj.clinic_front_photo)
