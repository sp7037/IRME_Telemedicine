from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    DoctorAvailability,
    DoctorSchedule,
    Consultation,
    ConsultationChat,
    Prescription,
    ConsultationEvent,
    Payment,
    ConsultationFinance,
    PatientWallet,
    PatientWalletEntry,
    TMCAccount,
    TMCAccountEntry,
    DoctorEarning,
)
from .serializers import (
    DoctorAvailabilitySerializer,
    DoctorScheduleSerializer,
    ConsultationBookingSerializer,
    ConsultationHistorySerializer,
    ConsultationUpdateSerializer,
    ConsultationChatSerializer,
    SendMessageSerializer,
    PrescriptionSerializer,
    DoctorProfileCompletionSerializer,
    ConsultationEventSerializer,
)
from users.models import DoctorProfile, PatientProfile, TMCProfile
from .utils import generate_prescription_pdf
from .services import transition_consultation, add_to_queue, TransitionError
from .finance import create_consultation_finance, ensure_doctor_earning_for_completion, patient_wallet_topup


def _get_tmc_profile(user):
    return getattr(user, "tmc_profile", None) or getattr(user, "tmcprofile_profile", None)

#==================================
# Set or create Doctor Availability
#==================================
class DoctorAvailabilityCreateView(generics.CreateAPIView):
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Ensure the user is a doctor
        if not hasattr(self.request.user, 'doctor_profile'):
            return Response({"error": "Doctor profile not found for this user."}, status=400)

        doctor = self.request.user.doctor_profile

        # Check if availability already exists (prevent duplicates)
        if DoctorAvailability.objects.filter(doctor=doctor).exists():
            return Response({"error": "Doctor availability already exists. Use PATCH to update."}, status=400)

        # Create new availability record
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(doctor=doctor)  # ✅ Automatically assign the doctor
            return Response(serializer.data, status=201)  # ✅ Success response

        return Response(serializer.errors, status=400)  # ✅ Error response


#=================================
# Get & Update Doctor Availability
#=================================
from rest_framework import serializers as drf_serializers

class DoctorAvailabilityView(generics.RetrieveUpdateAPIView):
    queryset = DoctorAvailability.objects.all()
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Ensure the user is a doctor
        if not hasattr(self.request.user, 'doctor_profile'):
            raise drf_serializers.ValidationError({"error": "Doctor profile not found for this user."})

        availability, _ = DoctorAvailability.objects.get_or_create(
            doctor=self.request.user.doctor_profile,
            defaults={
                "is_available_online": True,
                "is_available_in_clinic": True,
            },
        )
        return availability


#=================================
# Manage Doctor Schedules (Slots)
#=================================
class DoctorScheduleView(generics.ListCreateAPIView):
    serializer_class = DoctorScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DoctorSchedule.objects.filter(doctor=self.request.user.doctor_profile)

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.doctor_profile)
#==============================================
# Get Available Doctors (For Patients)
#==============================================

from users.serializers import DoctorProfileSerializer  # Ensure you have a proper serializer

class AvailableDoctorsView(APIView):
    """
    Fetches all available doctors with necessary details.
    Only returns doctors who:
    - Have completed and verified profiles
    - Are marked as available (online or in-clinic)
    - Have an availability record
    """
    permission_classes = []  # Allow unauthenticated access for patients to browse doctors

    def get(self, request):
        # Show doctors with completed profiles.
        # Keeping this broader prevents empty patient lists in environments
        # where admin verification workflow is not actively used.
        doctors = DoctorProfile.objects.filter(
            profile_completed=True
        ).select_related('user')
        
        # Filter by availability - read-only (no side effects in GET)
        available_doctors = []
        for doctor in doctors:
            try:
                availability = doctor.availability
            except DoctorAvailability.DoesNotExist:
                continue

            # Include if available online OR in-clinic
            if availability.is_available_online or availability.is_available_in_clinic:
                available_doctors.append(doctor)
        
        if not available_doctors:
            return Response([], status=status.HTTP_200_OK)

        # Pass request context to serializer for absolute URLs
        serializer = DoctorProfileSerializer(
            available_doctors, 
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

#==============================================
# Consultation Booking
#==============================================

class ConsultationBookingView(APIView):
    """
    Book a consultation, enforcing:
    - doctor availability
    - per-day limit
    - TMC free quota and payment creation
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConsultationBookingSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        consultation = serializer.save()
        payment = serializer.validated_data.get("payment")
        ConsultationEvent.objects.create(
            consultation=consultation,
            event_type=ConsultationEvent.EventType.REQUESTED,
            actor=request.user,
            to_status=consultation.status,
            metadata={"consultation_type": consultation.consultation_type},
        )

        response_data = {
            "message": "Consultation request sent successfully.",
            "consultation_id": consultation.id,
            "scheduled_time": consultation.scheduled_time,
            "status": consultation.status,
            "is_free": consultation.is_free,
        }
        if payment:
            response_data["payment"] = {
                "amount": payment.amount,
                "status": payment.status,
                "paid_by_tmc": payment.paid_by_tmc,
            }

        return Response(response_data, status=status.HTTP_201_CREATED)


#===================================================
# List Consultations for Logged-in User
#===================================================
class ConsultationHistoryView(APIView):
    """
    Fetches the consultation history for the logged-in user.

    - Patients: consultations where they are the patient
    - Doctors: consultations where they are the doctor
    - TMC: consultations routed via their TMC profile
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        consultations = Consultation.objects.none()

        if hasattr(user, "patient_profile"):
            consultations = Consultation.objects.filter(
                patient=user.patient_profile
            ).select_related("finance", "payment").order_by("-created_at")
        elif hasattr(user, "doctor_profile"):
            consultations = Consultation.objects.filter(
                doctor=user.doctor_profile
            ).select_related("finance", "payment").order_by("-created_at")
        elif _get_tmc_profile(user):
            tmc_profile = _get_tmc_profile(user)
            consultations = Consultation.objects.filter(
                tmc=tmc_profile
            ).select_related("finance", "payment").order_by("-created_at")
        else:
            return Response(
                {"error": "User does not have a patient, doctor, or TMC profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not consultations.exists():
            return Response({"message": "No past consultations found."}, status=status.HTTP_200_OK)

        # 🔹 Serialize the consultations using ConsultationHistorySerializer
        serializer = ConsultationHistorySerializer(consultations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



#========================================================================
# Mark Status of cosnsultation complete by doctor and canceled by patient 
#========================================================================
from .serializers import ConsultationUpdateSerializer

class UpdateConsultationStatusView(generics.UpdateAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationUpdateSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        consultation = self.get_object()

        # If the user is a patient, allow only cancellation
        if hasattr(request.user, 'patient_profile'):
            if consultation.patient != request.user.patient_profile:
                return Response({"error": "You are not authorized to cancel this consultation."}, status=403)
            
            if consultation.is_completed:
                return Response({"error": "Completed consultations cannot be canceled."}, status=400)

            try:
                consultation = transition_consultation(
                    consultation.id,
                    Consultation.StatusChoices.CANCELED,
                    actor=request.user,
                    note="Canceled by patient from update-status endpoint.",
                )
            except TransitionError as exc:
                return Response({"error": str(exc)}, status=400)
            return Response(
                {
                    "message": "Consultation canceled successfully.",
                    "data": ConsultationUpdateSerializer(consultation).data,
                }
            )

        # If the user is a doctor, allow marking as completed
        if hasattr(request.user, 'doctor_profile'):
            if consultation.doctor != request.user.doctor_profile:
                return Response({"error": "You are not authorized to complete this consultation."}, status=403)

            try:
                consultation = transition_consultation(
                    consultation.id,
                    Consultation.StatusChoices.COMPLETED,
                    actor=request.user,
                )
                ensure_doctor_earning_for_completion(consultation)
            except TransitionError as exc:
                return Response({"error": str(exc)}, status=400)
            return Response(
                {
                    "message": "Consultation marked as completed.",
                    "data": ConsultationUpdateSerializer(consultation).data,
                }
            )

        return Response({"error": "Unauthorized access."}, status=403)
#===============================================
# Doctor Response to consultations
#===============================================
class DoctorResponseView(generics.UpdateAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationUpdateSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        consultation = self.get_object()
        if not hasattr(request.user, 'doctor_profile'):
            return Response({"error": "Only doctors can respond to consultations."}, status=403)

        if consultation.doctor != request.user.doctor_profile:
            return Response({"error": "Unauthorized action."}, status=403)

        if consultation.status in [
            Consultation.StatusChoices.CANCELED,
            Consultation.StatusChoices.COMPLETED,
            Consultation.StatusChoices.REJECTED,
        ]:
            return Response({"error": "Consultation can no longer be updated."}, status=400)

        action = request.data.get("status")

        if action not in ["ACCEPTED", "QUEUED", "POSTPONED", "REJECTED"]:
            return Response({"error": "Invalid action. Choose ACCEPTED, QUEUED, POSTPONED, or REJECTED."}, status=400)

        if action == "ACCEPTED":
            try:
                with transaction.atomic():
                    consultation = transition_consultation(
                        consultation.id,
                        Consultation.StatusChoices.ACCEPTED,
                        actor=request.user,
                    )
                    has_active = Consultation.objects.select_for_update().filter(
                        doctor=consultation.doctor,
                        status=Consultation.StatusChoices.IN_PROGRESS,
                    ).exists()
                    has_other_queued = Consultation.objects.select_for_update().filter(
                        doctor=consultation.doctor,
                        status=Consultation.StatusChoices.QUEUED,
                    ).exclude(id=consultation.id).exists()
                    if has_active or has_other_queued:
                        add_to_queue(consultation)
                        ConsultationEvent.objects.create(
                            consultation=consultation,
                            event_type=ConsultationEvent.EventType.QUEUED,
                            actor=request.user,
                            from_status=Consultation.StatusChoices.ACCEPTED,
                            to_status=Consultation.StatusChoices.QUEUED,
                        )
                        message = "Consultation accepted and queued successfully."
                    else:
                        consultation = transition_consultation(
                            consultation.id,
                            Consultation.StatusChoices.IN_PROGRESS,
                            actor=request.user,
                            note="Auto-started after accept because doctor had no active/queued consultations.",
                        )
                        message = "Consultation accepted and started immediately."
            except TransitionError as exc:
                return Response({"error": str(exc)}, status=400)
            return Response(
                {
                    "message": message,
                    "data": ConsultationUpdateSerializer(consultation).data
                }
            )
        elif action == "POSTPONED":
            new_time = request.data.get("new_suggested_time")
            if not new_time:
                return Response({"error": "new_suggested_time is required when postponing."}, status=400)
            try:
                # Parse the datetime string
                from django.utils.dateparse import parse_datetime
                new_time_parsed = parse_datetime(new_time)
                if not new_time_parsed:
                    return Response({"error": "Invalid datetime format for new_suggested_time."}, status=400)
            except Exception as e:
                return Response({"error": f"Invalid datetime format: {str(e)}"}, status=400)
            
            try:
                consultation = transition_consultation(
                    consultation.id,
                    Consultation.StatusChoices.POSTPONED,
                    actor=request.user,
                    note=request.data.get("postpone_note"),
                    suggested_time=new_time_parsed,
                )
            except TransitionError as exc:
                return Response({"error": str(exc)}, status=400)
            return Response(
                {
                    "message": "Consultation postponed. Patient will be notified of the new suggested time.",
                    "data": ConsultationUpdateSerializer(consultation).data
                }
            )
        elif action == "REJECTED":
            try:
                consultation = transition_consultation(
                    consultation.id,
                    Consultation.StatusChoices.REJECTED,
                    actor=request.user,
                    note=request.data.get("reason") or "Doctor unavailable.",
                )
            except TransitionError as exc:
                return Response({"error": str(exc)}, status=400)
            return Response(
                {
                    "message": "Consultation rejected. Patient has been informed that the doctor is extremely busy.",
                    "data": ConsultationUpdateSerializer(consultation).data
                }
            )
        else:
            return Response({"error": "Invalid action."}, status=400)


#================================================
# Patient response to consultation
#================================================
class PatientResponseView(generics.UpdateAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationUpdateSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        consultation = self.get_object()

        # Ensure only the patient can respond
        if not hasattr(request.user, 'patient_profile'):
            return Response({"error": "Only patients can respond to consultations."}, status=403)

        if consultation.patient != request.user.patient_profile:
            return Response({"error": "Unauthorized action."}, status=403)

        action = request.data.get("action")  # Changed from "status" to "action" for clarity
        
        # Handle approve postponed consultation
        if action == "approve_postponed":
            if consultation.status != Consultation.StatusChoices.POSTPONED:
                return Response({"error": "This consultation is not in postponed status."}, status=400)
            
            if not consultation.new_suggested_time:
                return Response({"error": "No new suggested time found."}, status=400)
            
            # Update scheduled time to the new suggested time
            consultation.scheduled_time = consultation.new_suggested_time
            consultation.save(update_fields=["scheduled_time"])
            try:
                consultation = transition_consultation(
                    consultation.id,
                    Consultation.StatusChoices.PENDING,
                    actor=request.user,
                    note="Patient accepted postponed schedule.",
                    suggested_time=None,
                )
                ConsultationEvent.objects.create(
                    consultation=consultation,
                    event_type=ConsultationEvent.EventType.POSTPONE_ACCEPTED,
                    actor=request.user,
                    from_status=Consultation.StatusChoices.POSTPONED,
                    to_status=Consultation.StatusChoices.PENDING,
                    suggested_time=consultation.scheduled_time,
                )
            except TransitionError as exc:
                return Response({"error": str(exc)}, status=400)
            return Response(
                {
                    "message": "Postponed time approved. Consultation is now pending doctor's acceptance.",
                    "data": ConsultationUpdateSerializer(consultation).data
                }
            )
        
        # Handle reject postponed consultation
        elif action == "reject_postponed":
            if consultation.status != Consultation.StatusChoices.POSTPONED:
                return Response({"error": "This consultation is not in postponed status."}, status=400)
            
            # Mark as rejected by patient
            try:
                consultation = transition_consultation(
                    consultation.id,
                    Consultation.StatusChoices.REJECTED_BY_PATIENT,
                    actor=request.user,
                    note="Patient rejected postponed schedule.",
                    suggested_time=None,
                )
            except TransitionError as exc:
                return Response({"error": str(exc)}, status=400)
            return Response(
                {
                    "message": "Postponed time rejected. Doctor has been notified.",
                    "data": ConsultationUpdateSerializer(consultation).data
                }
            )
        
        # Handle cancel consultation (backward compatibility)
        elif action == "cancel" or action == Consultation.StatusChoices.CANCELED:
            allowed_statuses = [
                Consultation.StatusChoices.PENDING,
                Consultation.StatusChoices.ACCEPTED,
                Consultation.StatusChoices.QUEUED,
                Consultation.StatusChoices.POSTPONED,
            ]
            if consultation.status not in allowed_statuses:
                return Response({"error": "Consultation cannot be canceled anymore."}, status=400)
            
            try:
                consultation = transition_consultation(
                    consultation.id,
                    Consultation.StatusChoices.CANCELED,
                    actor=request.user,
                    note="Canceled by patient.",
                )
            except TransitionError as exc:
                return Response({"error": str(exc)}, status=400)
            return Response(
                {"message": "Consultation canceled successfully.", "data": ConsultationUpdateSerializer(consultation).data}
            )

        return Response({"error": "Invalid action. Use 'approve_postponed', 'reject_postponed', or 'cancel'."}, status=400)

#=========================================
# Get Pending Consultation Requests for Doctor
#=========================================
class DoctorPendingRequestsView(APIView):
    """
    Get all pending and postponed consultation requests for the logged-in doctor.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'doctor_profile'):
            return Response({"error": "Only doctors can access this endpoint."}, status=403)
        
        doctor = request.user.doctor_profile
        # Include both PENDING and POSTPONED requests
        pending_consultations = Consultation.objects.filter(
            doctor=doctor,
            status__in=[Consultation.StatusChoices.PENDING, Consultation.StatusChoices.POSTPONED]
        ).select_related('patient__user', 'doctor__user').order_by('scheduled_time', 'created_at')
        
        serializer = ConsultationHistorySerializer(pending_consultations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#=========================================
# Retrieve Chat History
#=========================================
class ConsultationChatHistoryView(generics.ListAPIView):
    serializer_class = ConsultationChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return chat messages for a specific consultation"""
        consultation_id = self.kwargs.get("consultation_id")
        consultation = get_object_or_404(Consultation, id=consultation_id)

        # Ensure the user is part of the consultation (patient or doctor)
        if self.request.user != consultation.patient.user and self.request.user != consultation.doctor.user:
            return ConsultationChat.objects.none()

        return ConsultationChat.objects.filter(consultation=consultation).order_by("timestamp")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response({
            "consultation_id": self.kwargs.get("consultation_id"),
            "chat_history": serializer.data
        })

#=========================================
# Send Message
#=========================================
class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, consultation_id):
        """Send a message in a consultation with optional file attachment"""
        consultation = get_object_or_404(Consultation, id=consultation_id)
        
        # Ensure the user is part of the consultation
        if request.user != consultation.patient.user and request.user != consultation.doctor.user:
            return Response({"error": "Unauthorized access."}, status=403)

        if consultation.status in [
            Consultation.StatusChoices.CANCELED,
            Consultation.StatusChoices.REJECTED,
            Consultation.StatusChoices.REJECTED_BY_PATIENT,
            Consultation.StatusChoices.COMPLETED,
        ]:
            return Response({"error": "Messaging is unavailable for closed consultations."}, status=400)
        
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        message_text = serializer.validated_data.get('message', '')
        attachment = serializer.validated_data.get('attachment', None)
        
        # Validate that either message or attachment is provided
        if not message_text and not attachment:
            return Response({"error": "Either message or attachment is required."}, status=400)
        
        # Validate file type if attachment is provided
        if attachment:
            allowed_types = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf']
            file_name = attachment.name.lower()
            if not any(file_name.endswith(ext) for ext in allowed_types):
                return Response({
                    "error": "Invalid file type. Only images (JPG, PNG, GIF, WEBP) and PDF files are allowed."
                }, status=400)
            
            # Check file size (max 10MB)
            if attachment.size > 10 * 1024 * 1024:
                return Response({"error": "File size too large. Maximum size is 10MB."}, status=400)
        
        # Create chat message - check if attachment field exists
        chat_data = {
            'consultation': consultation,
            'sender': request.user,
            'message': message_text
        }
        
        # Only add attachment if the model has the field (after migration)
        if hasattr(ConsultationChat, 'attachment') and attachment:
            chat_data['attachment'] = attachment
        
        chat = ConsultationChat.objects.create(**chat_data)
        
        response_serializer = ConsultationChatSerializer(chat, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

#=========================================
# Get Queued Consultations for Doctor
#=========================================
class DoctorQueuedConsultationsView(APIView):
    """Get all queued consultations for the logged-in doctor, ordered by queue number."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'doctor_profile'):
            return Response({"error": "Only doctors can access this endpoint."}, status=403)
        
        doctor = request.user.doctor_profile
        queued_consultations = Consultation.objects.filter(
            doctor=doctor,
            status=Consultation.StatusChoices.QUEUED
        ).select_related('patient__user', 'doctor__user').order_by('queue_number', 'scheduled_time')
        
        serializer = ConsultationHistorySerializer(queued_consultations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#=========================================
# Start Consultation (Change to IN_PROGRESS)
#=========================================
class StartConsultationView(APIView):
    """Doctor starts a consultation from the queue, changing status to IN_PROGRESS."""
    permission_classes = [IsAuthenticated]

    def post(self, request, consultation_id):
        consultation = get_object_or_404(Consultation, id=consultation_id)
        
        if not hasattr(request.user, 'doctor_profile'):
            return Response({"error": "Only doctors can start consultations."}, status=403)
        
        if consultation.doctor != request.user.doctor_profile:
            return Response({"error": "Unauthorized action."}, status=403)
        
        if consultation.status not in [Consultation.StatusChoices.QUEUED, Consultation.StatusChoices.ACCEPTED]:
            return Response({"error": "Only queued consultations can be started."}, status=400)
        
        # Check if doctor already has an active consultation
        active_consultation = Consultation.objects.filter(
            doctor=request.user.doctor_profile,
            status=Consultation.StatusChoices.IN_PROGRESS
        ).first()
        
        if active_consultation:
            return Response({
                "error": f"You already have an active consultation (ID: {active_consultation.id}). Please complete it first."
            }, status=400)
        
        try:
            consultation = transition_consultation(
                consultation.id,
                Consultation.StatusChoices.IN_PROGRESS,
                actor=request.user,
                note="Started by doctor.",
            )
        except TransitionError as exc:
            return Response({"error": str(exc)}, status=400)
        
        serializer = ConsultationHistorySerializer(consultation)
        return Response({
            "message": "Consultation started successfully.",
            "consultation": serializer.data
        }, status=status.HTTP_200_OK)

#=========================================
# Complete Consultation
#=========================================
class CompleteConsultationView(APIView):
    """Doctor marks a consultation as completed."""
    permission_classes = [IsAuthenticated]

    def post(self, request, consultation_id):
        consultation = get_object_or_404(Consultation, id=consultation_id)
        
        if not hasattr(request.user, 'doctor_profile'):
            return Response({"error": "Only doctors can complete consultations."}, status=403)
        
        if consultation.doctor != request.user.doctor_profile:
            return Response({"error": "Unauthorized action."}, status=403)
        
        # Check if consultation is in progress
        if consultation.status != Consultation.StatusChoices.IN_PROGRESS:
            return Response({"error": "Only in-progress consultations can be completed."}, status=400)
        
        try:
            consultation = transition_consultation(
                consultation.id,
                Consultation.StatusChoices.COMPLETED,
                actor=request.user,
            )
            ensure_doctor_earning_for_completion(consultation)
        except TransitionError as exc:
            return Response({"error": str(exc)}, status=400)
        
        serializer = ConsultationHistorySerializer(consultation)
        return Response({
            "message": "Consultation completed successfully.",
            "consultation": serializer.data
        }, status=status.HTTP_200_OK)

#=========================================
# Get Active Consultation (for patient and doctor)
#=========================================
class ActiveConsultationView(APIView):
    """Get the currently active consultation for the logged-in user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        consultation = None
        
        if hasattr(user, 'patient_profile'):
            consultation = Consultation.objects.filter(
                patient=user.patient_profile,
                status=Consultation.StatusChoices.IN_PROGRESS
            ).select_related('patient__user', 'doctor__user').first()
        elif hasattr(user, 'doctor_profile'):
            consultation = Consultation.objects.filter(
                doctor=user.doctor_profile,
                status=Consultation.StatusChoices.IN_PROGRESS
            ).select_related('patient__user', 'doctor__user').first()
        
        if not consultation:
            return Response({"message": "No active consultation found."}, status=status.HTTP_200_OK)
        
        serializer = ConsultationHistorySerializer(consultation)
        return Response(serializer.data, status=status.HTTP_200_OK)

#=========================================
# Prescription View
#=========================================
class PrescriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, consultation_id):
        """Get prescription for a consultation"""
        consultation = get_object_or_404(Consultation, id=consultation_id)
        
        # Ensure user is part of the consultation
        if request.user != consultation.doctor.user and request.user != consultation.patient.user:
            return Response({"error": "You don't have permission to view this prescription."}, status=403)
        
        try:
            prescription = Prescription.objects.get(consultation=consultation)
            serializer = PrescriptionSerializer(prescription, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Prescription.DoesNotExist:
            return Response({"message": "No prescription found for this consultation."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, consultation_id):
        """Create a new prescription"""
        consultation = get_object_or_404(Consultation, id=consultation_id)

        # Ensure only the assigned doctor can create prescriptions
        if request.user != consultation.doctor.user:
            return Response({"error": "Only the assigned doctor can create prescriptions."}, status=status.HTTP_403_FORBIDDEN)

        # Check if prescription already exists
        if Prescription.objects.filter(consultation=consultation).exists():
            return Response({"error": "Prescription already exists for this consultation. Use PUT/PATCH to update."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate medicines data
        medicines = request.data.get("medicines", [])
        if not medicines or not isinstance(medicines, list):
            return Response({"error": "medicines must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

        # Create prescription
        prescription_data = {
            "consultation": consultation,
            "doctor": consultation.doctor,
            "patient": consultation.patient,
            "medicines": medicines,
            "instructions": request.data.get("instructions", "Take medicines as prescribed. Follow up if symptoms persist.")
        }

        prescription = Prescription.objects.create(**prescription_data)
        ConsultationEvent.objects.create(
            consultation=consultation,
            event_type=ConsultationEvent.EventType.PRESCRIPTION_CREATED,
            actor=request.user,
            from_status=consultation.status,
            to_status=consultation.status,
        )
        
        # Create a chat message to mark this as a prescription in chat history
        ConsultationChat.objects.create(
            consultation=consultation,
            sender=request.user,
            message=f"PRESCRIPTION: Prescription issued on {prescription.created_at.strftime('%d-%b-%Y %I:%M %p')}"
        )
        
        serializer = PrescriptionSerializer(prescription, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, consultation_id):
        """Update an existing prescription"""
        consultation = get_object_or_404(Consultation, id=consultation_id)

        # Ensure only the assigned doctor can update prescriptions
        if request.user != consultation.doctor.user:
            return Response({"error": "Only the assigned doctor can update prescriptions."}, status=status.HTTP_403_FORBIDDEN)

        try:
            prescription = Prescription.objects.get(consultation=consultation)
        except Prescription.DoesNotExist:
            return Response({"error": "Prescription not found. Use POST to create."}, status=status.HTTP_404_NOT_FOUND)

        # Update medicines if provided
        if "medicines" in request.data:
            medicines = request.data.get("medicines", [])
            if not isinstance(medicines, list):
                return Response({"error": "medicines must be a list."}, status=status.HTTP_400_BAD_REQUEST)
            prescription.medicines = medicines

        # Update instructions if provided
        if "instructions" in request.data:
            prescription.instructions = request.data.get("instructions")

        prescription.save()
        ConsultationEvent.objects.create(
            consultation=consultation,
            event_type=ConsultationEvent.EventType.PRESCRIPTION_UPDATED,
            actor=request.user,
            from_status=consultation.status,
            to_status=consultation.status,
        )
        serializer = PrescriptionSerializer(prescription, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

#=========================================
# Create PDF view
#=========================================
class PrescriptionPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, prescription_id):
        """Allow doctors & patients to download prescription PDF"""
        prescription = get_object_or_404(Prescription, id=prescription_id)

        # Ensure only the patient or doctor can access it
        if request.user != prescription.patient.user and request.user != prescription.doctor.user:
            return Response({"error": "Unauthorized access"}, status=403)

        return generate_prescription_pdf(prescription_id)


class ConsultationEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, consultation_id):
        consultation = get_object_or_404(Consultation, id=consultation_id)
        allowed = request.user in {
            consultation.patient.user,
            consultation.doctor.user,
            consultation.tmc.user if consultation.tmc else None,
        }
        if not allowed:
            return Response({"error": "Unauthorized access."}, status=403)
        events = consultation.events.all()
        return Response(ConsultationEventSerializer(events, many=True).data, status=200)


class TMCDashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "tmc_profile"):
            if not _get_tmc_profile(request.user):
                return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        tmc = _get_tmc_profile(request.user)
        consultations = Consultation.objects.filter(tmc=tmc)
        finance_qs = ConsultationFinance.objects.filter(consultation__tmc=tmc)
        data = {
            "total": consultations.count(),
            "pending": consultations.filter(status=Consultation.StatusChoices.PENDING).count(),
            "queued": consultations.filter(status=Consultation.StatusChoices.QUEUED).count(),
            "in_progress": consultations.filter(status=Consultation.StatusChoices.IN_PROGRESS).count(),
            "completed": consultations.filter(status=Consultation.StatusChoices.COMPLETED).count(),
            "postponed": consultations.filter(status=Consultation.StatusChoices.POSTPONED).count(),
            "rejected": consultations.filter(status__in=[
                Consultation.StatusChoices.REJECTED,
                Consultation.StatusChoices.REJECTED_BY_PATIENT,
            ]).count(),
            "free_used": tmc.free_consultations_used,
            "free_quota": tmc.free_consultation_quota,
            "free_remaining": tmc.free_consultations_remaining,
            "finance_total_charged": str(sum((f.amount_charged for f in finance_qs), start=Decimal("0.00"))),
            "finance_paid_count": finance_qs.filter(
                billing_type=ConsultationFinance.BillingType.PAID
            ).count(),
            "finance_free_count": finance_qs.filter(
                billing_type=ConsultationFinance.BillingType.FREE
            ).count(),
        }
        return Response(data, status=200)


class TMCConsultationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _get_tmc_profile(request.user):
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        consultations = Consultation.objects.filter(tmc=_get_tmc_profile(request.user)).order_by("-created_at")
        return Response(ConsultationHistorySerializer(consultations, many=True).data, status=200)


class TMCBookConsultationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _get_tmc_profile(request.user):
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        tmc = _get_tmc_profile(request.user)
        patient_id = request.data.get("patient_id")
        doctor_id = request.data.get("doctor_id")
        if not patient_id or not doctor_id:
            return Response({"error": "patient_id and doctor_id are required."}, status=400)
        amount = request.data.get("amount", "0")
        patient = get_object_or_404(PatientProfile, id=patient_id)
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        scheduled_time = request.data.get("scheduled_time")
        if scheduled_time:
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(scheduled_time)
            if not dt:
                return Response({"error": "Invalid scheduled_time format."}, status=400)
            scheduled_time = dt
        else:
            scheduled_time = timezone.now() + timezone.timedelta(minutes=10)

        is_free = tmc.free_consultations_remaining > 0
        if is_free:
            tmc.free_consultations_used += 1
            tmc.save(update_fields=["free_consultations_used"])

        consultation = Consultation.objects.create(
            patient=patient,
            doctor=doctor,
            tmc=tmc,
            consultation_type=Consultation.ConsultationType.TMC,
            scheduled_time=scheduled_time,
            status=Consultation.StatusChoices.PENDING,
            is_free=is_free,
            status_changed_by=request.user,
        )

        payment = None
        if not is_free:
            payment = Payment.objects.create(
                consultation=consultation,
                amount=amount,
                status=Payment.Status.PAID,
                paid_by_tmc=True,
            )
        create_consultation_finance(
            consultation=consultation,
            payment=payment,
            amount=amount,
        )

        ConsultationEvent.objects.create(
            consultation=consultation,
            event_type=ConsultationEvent.EventType.REQUESTED,
            actor=request.user,
            to_status=Consultation.StatusChoices.PENDING,
            metadata={"initiated_by": "tmc"},
        )
        return Response(
            {
                "message": "TMC consultation created successfully.",
                "consultation_id": consultation.id,
                "status": consultation.status,
                "is_free": consultation.is_free,
            },
            status=201,
        )


class PatientWalletSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "patient_profile"):
            return Response({"error": "Only patients can access this endpoint."}, status=403)
        wallet, _ = PatientWallet.objects.get_or_create(patient=request.user.patient_profile)
        entries = wallet.entries.all()[:20]
        data = {
            "balance": str(wallet.balance),
            "total_credited": str(wallet.total_credited),
            "total_debited": str(wallet.total_debited),
            "recent_entries": [
                {
                    "id": e.id,
                    "entry_type": e.entry_type,
                    "amount": str(e.amount),
                    "balance_after": str(e.balance_after),
                    "consultation_id": e.consultation_id,
                    "description": e.description,
                    "created_at": e.created_at,
                }
                for e in entries
            ],
        }
        return Response(data, status=200)

    def post(self, request):
        if not hasattr(request.user, "patient_profile"):
            return Response({"error": "Only patients can access this endpoint."}, status=403)
        amount = request.data.get("amount")
        if amount is None:
            return Response({"error": "amount is required."}, status=400)
        entry = patient_wallet_topup(request.user.patient_profile, amount)
        return Response(
            {
                "message": "Wallet top-up recorded.",
                "entry_id": entry.id,
                "balance_after": str(entry.balance_after),
            },
            status=201,
        )


class DoctorEarningsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "doctor_profile"):
            return Response({"error": "Only doctors can access this endpoint."}, status=403)
        earnings = DoctorEarning.objects.filter(doctor=request.user.doctor_profile).order_by("-created_at")
        total = sum((e.earning_amount for e in earnings), start=Decimal("0.00"))
        return Response(
            {
                "total_earnings": str(total),
                "total_records": earnings.count(),
                "paid_count": earnings.filter(billing_type=ConsultationFinance.BillingType.PAID).count(),
                "free_count": earnings.filter(billing_type=ConsultationFinance.BillingType.FREE).count(),
                "recent_earnings": [
                    {
                        "consultation_id": e.consultation_id,
                        "earning_amount": str(e.earning_amount),
                        "status": e.status,
                        "source_type": e.source_type,
                        "billing_type": e.billing_type,
                        "created_at": e.created_at,
                    }
                    for e in earnings[:20]
                ],
            },
            status=200,
        )


class TMCFinanceSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _get_tmc_profile(request.user):
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        account, _ = TMCAccount.objects.get_or_create(tmc=_get_tmc_profile(request.user))
        entries = account.entries.all()[:20]
        return Response(
            {
                "balance": str(account.balance),
                "total_charged": str(account.total_charged),
                "total_credited": str(account.total_credited),
                "total_debited": str(account.total_debited),
                "recent_entries": [
                    {
                        "id": e.id,
                        "entry_type": e.entry_type,
                        "amount": str(e.amount),
                        "balance_after": str(e.balance_after),
                        "consultation_id": e.consultation_id,
                        "description": e.description,
                        "created_at": e.created_at,
                    }
                    for e in entries
                ],
            },
            status=200,
        )

#=========================================
# Doctor Profile Completion View
#=========================================
class DoctorProfileCompletionView(generics.RetrieveUpdateAPIView):
    """
    View for doctors to complete their profile after login.
    GET: Retrieve doctor profile
    PATCH: Update doctor profile and mark as completed
    """
    serializer_class = DoctorProfileCompletionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Get the doctor profile for the authenticated user - create if doesn't exist."""
        from users.models.profiles import DoctorProfile
        
        # Get or create the profile
        profile, created = DoctorProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_serializer_context(self):
        """Add request to serializer context for building absolute URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def patch(self, request, *args, **kwargs):
        """Update doctor profile with completion check."""
        doctor_profile = self.get_object()
        serializer = self.get_serializer(doctor_profile, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response({
                "error": serializer.errors,
                "message": "Validation failed. Please check the errors below."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        # Refresh from DB to get updated completion status
        doctor_profile.refresh_from_db()
        
        return Response({
            "message": "Profile updated successfully.",
            "profile": serializer.data,
            "profile_completed": doctor_profile.profile_completed
        }, status=status.HTTP_200_OK)
