from rest_framework import serializers
from ..models.users import User  # Corrected import path
from ..models.profiles import DoctorProfile, PatientProfile, TMCProfile  # Corrected import path


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
    profile_completed = serializers.BooleanField(read_only=True)
    admin_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ["id", "first_name", "last_name", "email", "specialty", "experience", "qualification", "hospital_or_clinic_name", "photo", "profile_completed", "admin_verified"]
    
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
        fields = ['gender', 'age', 'address']

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
class TMCProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the TMC operator-specific profile fields.
    """
    tmc_details = serializers.CharField(
        required=True,
        help_text="Details about the TMC operator."
    )

    class Meta:
        model = TMCProfile
        fields = ['tmc_details']

    def validate_tmc_details(self, value):
        """
        Ensures TMC details are provided.
        """
        if not value.strip():
            raise serializers.ValidationError("TMC details cannot be empty.")
        return value
