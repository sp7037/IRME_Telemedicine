import logging
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from decimal import Decimal

logger = logging.getLogger(__name__)

MAX_PENDING_DOCTOR_PROFILE_CHANGE_REQUESTS = 3
IN_PROGRESS_COMPLETION_LOCK_HOURS = 24

from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    DoctorAvailability,
    DoctorSchedule,
    Consultation,
    ConsultationFollowUpSession,
    ConsultationChat,
    Prescription,
    ConsultationEvent,
    Payment,
    ConsultationFinance,
    ConsultationFeeSetting,
    PatientWallet,
    PatientWalletEntry,
    PatientWalletRechargeRequest,
    TMCAccount,
    TMCAccountEntry,
    TMCRechargeRequest,
    DoctorEarning,
)
from .prescription_versions import (
    archive_current_before_update,
    prescription_content_changed,
    record_initial_version,
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
    PrescriptionVersionSerializer,
    DoctorProfileCompletionSerializer,
    ConsultationEventSerializer,
)
from users.models import DoctorProfile, PatientProfile, TMCProfile
from .utils import generate_prescription_pdf
from .services import transition_consultation, add_to_queue, TransitionError
from .permissions import get_owned_tmc_profile
from .video import VideoProviderError, get_or_create_video_join, video_config_status
from .video import request_video_session, respond_to_video_session
from .finance import (
    InsufficientBalanceError,
    cancel_patient_recharge_request,
    create_consultation_finance,
    cancel_tmc_recharge_request,
    create_patient_recharge_order_reference,
    create_patient_recharge_request,
    create_tmc_recharge_order_reference,
    create_tmc_recharge_request,
    create_razorpay_order_reference,
    estimate_tmc_consultation_pricing,
    ensure_doctor_earning_for_completion,
    mark_razorpay_payment_success,
    mark_patient_recharge_success,
    mark_tmc_recharge_success,
    reconcile_approved_patient_recharges,
    reconcile_approved_tmc_recharges,
    resolve_consultation_amount,
    resolve_doctor_consultation_amount,
)
from .serializers import OPEN_CONSULTATION_STATUSES, SAME_DOCTOR_REBOOKING_GAP_MINUTES


def _get_tmc_profile(user):
    return get_owned_tmc_profile(user)


def _can_manage_consultation_payment(user, consultation):
    if ConsultationFinance.objects.filter(consultation=consultation, payment_status=ConsultationFinance.PaymentStatus.REFUNDED).exists():
        return False
    if user.is_staff:
        return True
    if consultation.consultation_type == Consultation.ConsultationType.TMC:
        tmc = _get_tmc_profile(user)
        return bool(tmc and tmc.pk == consultation.tmc_id)
    return consultation.patient.user_id == user.pk


def _is_consultation_participant(user, consultation, *, include_tmc=True):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    allowed = {
        consultation.patient.user_id,
        consultation.doctor.user_id,
    }
    if include_tmc and consultation.tmc_id:
        allowed.add(consultation.tmc.user_id)
    return user.id in allowed


def _completion_required(consultation):
    if consultation.status != Consultation.StatusChoices.IN_PROGRESS:
        return False
    started_at = consultation.last_status_changed_at or consultation.updated_at or consultation.created_at
    if not started_at:
        return False
    return timezone.now() - started_at >= timezone.timedelta(hours=IN_PROGRESS_COMPLETION_LOCK_HOURS)


PRESCRIPTION_EDIT_WINDOW_MINUTES = 30
FREE_FOLLOWUP_DAYS = 5
FREE_FOLLOWUP_LIMIT = 3


def _prescription_edit_deadline(prescription):
    return prescription.updated_at + timezone.timedelta(minutes=PRESCRIPTION_EDIT_WINDOW_MINUTES)


def _can_edit_prescription(prescription):
    return timezone.now() <= _prescription_edit_deadline(prescription)


def _extract_prescription_payload(request):
    medicines = request.data.get("medicines", [])
    instructions = request.data.get(
        "instructions",
        "Take medicines as prescribed. Follow up if symptoms persist.",
    )
    if not medicines or not isinstance(medicines, list):
        return None, None, Response(
            {"error": "medicines must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return medicines, instructions, None


def _first_consultation_completion_at(consultation):
    event = consultation.events.filter(
        event_type=ConsultationEvent.EventType.COMPLETED
    ).order_by("created_at").first()
    return event.created_at if event else consultation.updated_at


def _followup_window_status(consultation):
    completed_at = _first_consultation_completion_at(consultation)
    deadline = completed_at + timezone.timedelta(days=FREE_FOLLOWUP_DAYS) if completed_at else timezone.now()
    free_used = consultation.follow_up_sessions.filter(
        status=ConsultationFollowUpSession.Status.COMPLETED,
        is_billable=False,
        requested_at__lte=deadline,
    ).count()
    free_remaining = max(0, FREE_FOLLOWUP_LIMIT - free_used)
    is_free = timezone.now() <= deadline and free_remaining > 0
    return {
        "deadline": deadline,
        "free_used": free_used,
        "free_remaining": free_remaining,
        "is_free": is_free,
    }


def _active_followup_session(consultation):
    return consultation.follow_up_sessions.filter(
        status__in=[
            ConsultationFollowUpSession.Status.PENDING,
            ConsultationFollowUpSession.Status.IN_PROGRESS,
        ]
    ).order_by("-requested_at").first()


def _current_prescription_scope(consultation):
    followup = consultation.follow_up_sessions.filter(
        status=ConsultationFollowUpSession.Status.IN_PROGRESS
    ).order_by("-started_at", "-id").first()
    return followup


def _charge_followup_if_needed(consultation, session, amount, requested_by):
    if not session.is_billable or amount <= 0:
        return
    if consultation.consultation_type == Consultation.ConsultationType.TMC and consultation.tmc_id:
        owner = _get_tmc_profile(requested_by)
        if not owner or owner.pk != consultation.tmc_id:
            raise PermissionDenied("Only the owning TMC operator can authorise its wallet charge.")
        account = TMCAccount.objects.select_for_update().get_or_create(tmc=consultation.tmc)[0]
        if Decimal(account.balance) < amount:
            raise InsufficientBalanceError(
                f"Insufficient TMC wallet balance. Required {amount}, available {account.balance}."
            )
        account.balance = Decimal(account.balance) - amount
        account.total_charged = Decimal(account.total_charged) + amount
        account.total_debited = Decimal(account.total_debited) + amount
        account.save(update_fields=["balance", "total_charged", "total_debited", "updated_at"])
        TMCAccountEntry.objects.create(
            account=account,
            entry_type=TMCAccountEntry.EntryType.CHARGE,
            amount=amount,
            balance_after=account.balance,
            consultation=consultation,
            description=f"Billable follow-up #{session.sequence_number}",
        )
        return

    wallet = PatientWallet.objects.select_for_update().get_or_create(patient=consultation.patient)[0]
    if Decimal(wallet.balance) < amount:
        raise InsufficientBalanceError(
            f"Insufficient patient wallet balance. Required {amount}, available {wallet.balance}."
        )
    wallet.balance = Decimal(wallet.balance) - amount
    wallet.total_debited = Decimal(wallet.total_debited) + amount
    wallet.save(update_fields=["balance", "total_debited", "updated_at"])
    PatientWalletEntry.objects.create(
        wallet=wallet,
        entry_type=PatientWalletEntry.EntryType.DEBIT,
        amount=amount,
        balance_after=wallet.balance,
        consultation=consultation,
        description=f"Billable follow-up #{session.sequence_number}",
    )

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
        if not hasattr(self.request.user, "doctor_profile"):
            return DoctorSchedule.objects.none()
        return DoctorSchedule.objects.filter(doctor=self.request.user.doctor_profile).order_by(
            "day_of_week", "start_time"
        )

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.doctor_profile)


class DoctorScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DoctorScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not hasattr(self.request.user, "doctor_profile"):
            return DoctorSchedule.objects.none()
        return DoctorSchedule.objects.filter(doctor=self.request.user.doctor_profile)
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
        doctors = DoctorProfile.objects.filter(
            profile_completed=True,
            admin_verified=True,
            is_approved=True,
            user__is_email_verified=True,
        ).select_related('user')

        search = (request.query_params.get("search") or "").strip()
        specialty = (request.query_params.get("specialty") or "").strip()
        location = (request.query_params.get("location") or "").strip()

        if search:
            doctors = doctors.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(specialty__icontains=search)
                | Q(qualification__icontains=search)
                | Q(hospital_or_clinic_name__icontains=search)
                | Q(city__icontains=search)
                | Q(state__icontains=search)
            )
        if specialty:
            doctors = doctors.filter(specialty__icontains=specialty)
        if location:
            doctors = doctors.filter(Q(city__icontains=location) | Q(state__icontains=location))
        
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

        probe_time = timezone.now() + timedelta(minutes=10)
        available_doctors = [
            d for d in available_doctors
            if ConsultationBookingSerializer._doctor_is_available(d, probe_time)
        ]

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

class DirectBookingPreviewView(APIView):
    """Read-only current legacy charge preview, not a price or slot reservation."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_patient or not hasattr(request.user, "patient_profile"):
            raise PermissionDenied("Only patients can preview their own direct booking.")
        from rest_framework import serializers
        from .finance import calculate_percentage_amount, normalize_money

        doctor_id = serializers.IntegerField(min_value=1).run_validation(request.query_params.get("doctor_id"))
        doctor = get_object_or_404(DoctorProfile, pk=doctor_id, profile_completed=True,
            admin_verified=True, is_approved=True, user__is_email_verified=True)
        setting = ConsultationFeeSetting.objects.filter(is_active=True).order_by("-created_at").first()
        if not setting or setting.currency != "INR":
            return Response({"error": "INR consultation pricing must be configured before booking."}, status=409)
        base = normalize_money(doctor.consultation_fee or 0)
        if base <= 0:
            base = normalize_money(setting.direct_patient_fee)
        platform = calculate_percentage_amount(base, setting.platform_fee_percentage)
        total = normalize_money(base + platform)
        wallet = PatientWallet.objects.filter(patient=request.user.patient_profile).first()
        balance = normalize_money(wallet.balance if wallet else 0)
        shortfall = max(Decimal("0.00"), total - balance)
        return Response({"doctor_id": doctor.pk, "currency": "INR", "base_fee": str(base),
            "platform_fee": str(platform), "total": str(total), "balance": str(balance),
            "shortfall": str(shortfall), "can_request": shortfall == 0,
            "price_reserved": False})


class ConsultationBookingView(APIView):
    """
    Book a consultation, enforcing:
    - doctor availability
    - per-day limit
    - direct patient wallet charging (TMC spending uses the owner-only endpoint)
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
            except InsufficientBalanceError as exc:
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
    queryset = Consultation.objects.select_for_update()
    serializer_class = ConsultationUpdateSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
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
            if consultation.status == Consultation.StatusChoices.REJECTED_BY_PATIENT:
                return Response({"message": "This postponed time was already rejected.",
                    "data": ConsultationHistorySerializer(consultation).data})
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
                    "message": "You rejected the proposed time. You can choose another doctor or request this doctor again when available.",
                    "data": ConsultationHistorySerializer(consultation).data
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


class PatientFollowUpRequestView(APIView):
    """Patient or assigned TMC requests to reopen a completed consultation thread."""
    permission_classes = [IsAuthenticated]

    def post(self, request, consultation_id):
        consultation = get_object_or_404(
            Consultation.objects.select_related("patient__user", "doctor__user", "tmc__user"),
            id=consultation_id,
        )
        is_direct_patient = (
            hasattr(request.user, "patient_profile")
            and consultation.patient_id == request.user.patient_profile.id
        )
        operator_tmc = _get_tmc_profile(request.user)
        is_assigned_tmc = (
            consultation.consultation_type == Consultation.ConsultationType.TMC
            and operator_tmc is not None
            and consultation.tmc_id == operator_tmc.pk
        )
        if not (is_direct_patient or is_assigned_tmc):
            return Response(
                {"error": "Only this patient or the assigned TMC can request a follow-up."},
                status=403,
            )
        if consultation.status != Consultation.StatusChoices.COMPLETED or not consultation.is_completed:
            return Response({"error": "Follow-up can be requested only after the consultation is completed."}, status=400)
        if _active_followup_session(consultation):
            return Response({"error": "A follow-up request is already open for this consultation."}, status=400)

        window = _followup_window_status(consultation)
        is_billable = not window["is_free"]
        amount = resolve_consultation_amount(consultation.consultation_type) if is_billable else Decimal("0.00")
        if amount > 0 and consultation.consultation_type == Consultation.ConsultationType.TMC and not is_assigned_tmc:
            return Response({"error": "Paid TMC follow-ups require authorisation by the owning TMC operator."}, status=403)

        try:
            with transaction.atomic():
                consultation = Consultation.objects.select_for_update().get(id=consultation.id)
                if _active_followup_session(consultation):
                    return Response({"error": "A follow-up request is already open for this consultation."}, status=400)
                next_sequence = consultation.follow_up_sessions.count() + 1
                session = ConsultationFollowUpSession.objects.create(
                    consultation=consultation,
                    sequence_number=next_sequence,
                    requested_by=request.user,
                    is_billable=is_billable,
                    amount_charged=amount,
                    charge_note=(
                        "Charged because the free 5-day/3-message follow-up allowance is exhausted."
                        if is_billable else
                        "Free follow-up inside 5-day allowance."
                    ),
                )
                _charge_followup_if_needed(consultation, session, amount, requested_by=request.user)
                ConsultationEvent.objects.create(
                    consultation=consultation,
                    event_type=ConsultationEvent.EventType.FOLLOWUP_REQUESTED,
                    actor=request.user,
                    from_status=consultation.status,
                    to_status=consultation.status,
                    metadata={
                        "follow_up_session_id": session.id,
                        "sequence_number": session.sequence_number,
                        "is_billable": session.is_billable,
                        "amount_charged": str(session.amount_charged),
                        "free_remaining_before_request": window["free_remaining"],
                    },
                )
        except InsufficientBalanceError as exc:
            return Response({"wallet": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "Follow-up request sent to the doctor.",
                "follow_up_session_id": session.id,
                "status": session.status,
                "is_billable": session.is_billable,
                "amount_charged": str(session.amount_charged),
                "free_remaining": max(0, window["free_remaining"] - (0 if is_billable else 1)),
            },
            status=status.HTTP_201_CREATED,
        )


class DoctorFollowUpResponseView(APIView):
    """Doctor accepts/rejects a follow-up request from an existing patient."""
    permission_classes = [IsAuthenticated]

    def post(self, request, followup_id):
        session = get_object_or_404(
            ConsultationFollowUpSession.objects.select_related(
                "consultation__doctor__user", "consultation__patient__user"
            ),
            id=followup_id,
        )
        consultation = session.consultation
        if not hasattr(request.user, "doctor_profile") or consultation.doctor != request.user.doctor_profile:
            return Response({"error": "Only the assigned doctor can respond to this follow-up."}, status=403)
        if session.status != ConsultationFollowUpSession.Status.PENDING:
            return Response({"error": "This follow-up request is no longer pending."}, status=400)

        action = (request.data.get("action") or request.data.get("status") or "ACCEPTED").upper()
        if action not in ["ACCEPTED", "REJECTED"]:
            return Response({"error": "Use ACCEPTED or REJECTED."}, status=400)

        if action == "REJECTED":
            session.status = ConsultationFollowUpSession.Status.REJECTED
            session.save(update_fields=["status", "updated_at"])
            ConsultationEvent.objects.create(
                consultation=consultation,
                event_type=ConsultationEvent.EventType.REJECTED,
                actor=request.user,
                from_status=consultation.status,
                to_status=consultation.status,
                note="Doctor rejected the follow-up request.",
                metadata={"follow_up_session_id": session.id},
            )
            return Response({"message": "Follow-up rejected.", "follow_up_session_id": session.id})

        active = Consultation.objects.filter(
            doctor=consultation.doctor,
            status=Consultation.StatusChoices.IN_PROGRESS,
        ).exclude(id=consultation.id).first()
        if active:
            return Response(
                {"error": f"Complete active consultation #{active.id} before accepting this follow-up."},
                status=400,
            )

        with transaction.atomic():
            consultation = Consultation.objects.select_for_update().get(id=consultation.id)
            session = ConsultationFollowUpSession.objects.select_for_update().get(id=session.id)
            session.status = ConsultationFollowUpSession.Status.IN_PROGRESS
            session.started_by = request.user
            session.started_at = timezone.now()
            session.save(update_fields=["status", "started_by", "started_at", "updated_at"])
            consultation.status = Consultation.StatusChoices.IN_PROGRESS
            consultation.is_completed = False
            consultation.status_changed_by = request.user
            consultation.last_status_changed_at = timezone.now()
            consultation.save(update_fields=["status", "is_completed", "status_changed_by", "last_status_changed_at", "updated_at"])
            ConsultationEvent.objects.create(
                consultation=consultation,
                event_type=ConsultationEvent.EventType.FOLLOWUP_STARTED,
                actor=request.user,
                from_status=Consultation.StatusChoices.COMPLETED,
                to_status=Consultation.StatusChoices.IN_PROGRESS,
                metadata={
                    "follow_up_session_id": session.id,
                    "sequence_number": session.sequence_number,
                    "is_billable": session.is_billable,
                    "amount_charged": str(session.amount_charged),
                },
            )
            ConsultationChat.objects.create(
                consultation=consultation,
                sender=request.user,
                message=f"FOLLOW-UP: Follow-up #{session.sequence_number} started."
            )

        serializer = ConsultationHistorySerializer(consultation)
        return Response(
            {
                "message": "Follow-up started.",
                "follow_up_session_id": session.id,
                "consultation": serializer.data,
            }
        )

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
        data = list(serializer.data)

        followups = ConsultationFollowUpSession.objects.filter(
            consultation__doctor=doctor,
            status=ConsultationFollowUpSession.Status.PENDING,
        ).select_related("consultation__patient__user", "consultation__doctor__user").order_by("requested_at")
        for session in followups:
            c = session.consultation
            data.append({
                "id": c.id,
                "follow_up_session_id": session.id,
                "is_follow_up_request": True,
                "doctor": c.doctor_id,
                "doctor_name": c.doctor.user.get_full_name() or c.doctor.user.email,
                "patient_name": c.patient.user.get_full_name() or c.patient.user.email,
                "patient_email": c.patient.user.email,
                "patient_phone": c.patient.user.phone_number,
                "consultation_type": c.consultation_type,
                "formatted_time": session.requested_at.strftime("%d-%b-%Y %I:%M %p"),
                "status": "PENDING",
                "is_completed": False,
                "scheduled_time": session.requested_at,
                "created_at": session.requested_at,
                "created_at_formatted": session.requested_at.strftime("%d-%b-%Y %I:%M %p"),
                "tmc_name": c.tmc.user.get_full_name() if c.tmc_id else None,
                "consultation_label": f"Existing patient follow-up #{session.sequence_number}",
                "billing_type": "PAID" if session.is_billable else "FREE",
                "amount_charged": str(session.amount_charged),
                "follow_up": {
                    "active_session_id": session.id,
                    "active_status": session.status,
                    "active_sequence_number": session.sequence_number,
                    "free_remaining": None,
                    "next_is_billable": session.is_billable,
                    "can_request": False,
                },
            })
        return Response(data, status=status.HTTP_200_OK)

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

        # Ensure the user is part of the consultation (patient, doctor, or assigned TMC)
        if not _is_consultation_participant(self.request.user, consultation):
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
        if not _is_consultation_participant(request.user, consultation):
            return Response({"error": "Unauthorized access."}, status=403)

        if consultation.status in [
            Consultation.StatusChoices.CANCELED,
            Consultation.StatusChoices.REJECTED,
            Consultation.StatusChoices.REJECTED_BY_PATIENT,
            Consultation.StatusChoices.COMPLETED,
        ]:
            return Response({"error": "Messaging is unavailable for closed consultations."}, status=400)
        if _completion_required(consultation):
            return Response(
                {"error": "This consultation has been in progress for more than 24 hours. The doctor must mark it complete before chat or video can continue."},
                status=400,
            )
        
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
        ConsultationEvent.objects.create(
            consultation=consultation,
            event_type=ConsultationEvent.EventType.MESSAGE_SENT,
            actor=request.user,
            from_status=consultation.status,
            to_status=consultation.status,
            metadata={
                "has_attachment": bool(attachment),
                "message_length": len(message_text or ""),
            },
        )
        
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
        except (TransitionError, InsufficientBalanceError) as exc:
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

        active_followup = consultation.follow_up_sessions.filter(
            status=ConsultationFollowUpSession.Status.IN_PROGRESS
        ).order_by("-started_at", "-id").first()
        
        try:
            consultation = transition_consultation(
                consultation.id,
                Consultation.StatusChoices.COMPLETED,
                actor=request.user,
            )
            if active_followup:
                active_followup.status = ConsultationFollowUpSession.Status.COMPLETED
                active_followup.completed_by = request.user
                active_followup.completed_at = timezone.now()
                active_followup.save(update_fields=["status", "completed_by", "completed_at", "updated_at"])
                ConsultationEvent.objects.create(
                    consultation=consultation,
                    event_type=ConsultationEvent.EventType.FOLLOWUP_COMPLETED,
                    actor=request.user,
                    from_status=Consultation.StatusChoices.IN_PROGRESS,
                    to_status=Consultation.StatusChoices.COMPLETED,
                    metadata={
                        "follow_up_session_id": active_followup.id,
                        "sequence_number": active_followup.sequence_number,
                        "is_billable": active_followup.is_billable,
                        "amount_charged": str(active_followup.amount_charged),
                    },
                )
            else:
                ensure_doctor_earning_for_completion(consultation)
        except (TransitionError, InsufficientBalanceError) as exc:
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
        if not _is_consultation_participant(request.user, consultation):
            return Response({"error": "You don't have permission to view this prescription."}, status=403)
        
        followup_id = request.query_params.get("follow_up_session_id")
        qs = Prescription.objects.prefetch_related("versions").filter(consultation=consultation)
        if followup_id:
            qs = qs.filter(follow_up_session_id=followup_id)
        else:
            active_scope = _current_prescription_scope(consultation)
            if active_scope:
                qs = qs.filter(follow_up_session=active_scope)
            else:
                qs = qs.order_by("-updated_at", "-id")
        try:
            prescription = qs.order_by("-updated_at", "-id").first()
            if not prescription:
                raise Prescription.DoesNotExist
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

        if consultation.status not in [Consultation.StatusChoices.IN_PROGRESS, Consultation.StatusChoices.COMPLETED]:
            return Response(
                {"error": "Prescriptions can be created only after the consultation has started."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        medicines, instructions, error_response = _extract_prescription_payload(request)
        if error_response:
            return error_response

        followup_scope = _current_prescription_scope(consultation)
        existing = Prescription.objects.filter(
            consultation=consultation,
            follow_up_session=followup_scope,
        ).order_by("-updated_at", "-id").first()
        if existing:
            if _can_edit_prescription(existing):
                return Response(
                    {
                        "error": (
                            "A prescription already exists and is still inside the 30-minute edit window. "
                            "Use Edit Prescription instead of issuing a new one."
                        ),
                        "code": "EDIT_WINDOW_OPEN",
                        "edit_deadline": _prescription_edit_deadline(existing),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                archive_current_before_update(existing, request.user)
                existing.medicines = medicines
                existing.instructions = instructions
                existing.save()
                ConsultationEvent.objects.create(
                    consultation=consultation,
                    event_type=ConsultationEvent.EventType.PRESCRIPTION_REISSUED,
                    actor=request.user,
                    from_status=consultation.status,
                    to_status=consultation.status,
                )
                ConsultationChat.objects.create(
                    consultation=consultation,
                    sender=request.user,
                    message=(
                        f"PRESCRIPTION_RX:{existing.id}: "
                        f"New prescription issued on {existing.updated_at.strftime('%d-%b-%Y %I:%M %p')}"
                    )
                )

            serializer = PrescriptionSerializer(existing, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Create prescription
        prescription_data = {
            "consultation": consultation,
            "follow_up_session": followup_scope,
            "doctor": consultation.doctor,
            "patient": consultation.patient,
            "medicines": medicines,
            "instructions": instructions,
        }

        with transaction.atomic():
            prescription = Prescription.objects.create(**prescription_data)
            record_initial_version(prescription, request.user)
            ConsultationEvent.objects.create(
                consultation=consultation,
                event_type=ConsultationEvent.EventType.PRESCRIPTION_CREATED,
                actor=request.user,
                from_status=consultation.status,
                to_status=consultation.status,
            )
            ConsultationChat.objects.create(
                consultation=consultation,
                sender=request.user,
                message=(
                    f"PRESCRIPTION_RX:{prescription.id}: "
                    f"Prescription issued on {prescription.created_at.strftime('%d-%b-%Y %I:%M %p')}"
                )
            )

        serializer = PrescriptionSerializer(prescription, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, consultation_id):
        """Update an existing prescription"""
        consultation = get_object_or_404(Consultation, id=consultation_id)

        # Ensure only the assigned doctor can update prescriptions
        if request.user != consultation.doctor.user:
            return Response({"error": "Only the assigned doctor can update prescriptions."}, status=status.HTTP_403_FORBIDDEN)

        if consultation.status not in [Consultation.StatusChoices.IN_PROGRESS, Consultation.StatusChoices.COMPLETED]:
            return Response(
                {"error": "Prescriptions can be updated only after the consultation has started."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        followup_scope = _current_prescription_scope(consultation)
        prescription = Prescription.objects.filter(
            consultation=consultation,
            follow_up_session=followup_scope,
        ).order_by("-updated_at", "-id").first()
        if not prescription:
            return Response({"error": "Prescription not found. Use POST to create."}, status=status.HTTP_404_NOT_FOUND)

        if not _can_edit_prescription(prescription):
            return Response(
                {
                    "error": "The 30-minute edit window has closed. Please issue a new prescription.",
                    "code": "REISSUE_REQUIRED",
                    "edit_deadline": _prescription_edit_deadline(prescription),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        touch_medicines = "medicines" in request.data
        touch_instructions = "instructions" in request.data
        new_medicines = request.data.get("medicines") if touch_medicines else None
        new_instructions = request.data.get("instructions") if touch_instructions else None

        if touch_medicines:
            if not isinstance(new_medicines, list):
                return Response({"error": "medicines must be a list."}, status=status.HTTP_400_BAD_REQUEST)

        if not touch_medicines and not touch_instructions:
            serializer = PrescriptionSerializer(prescription, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        if not prescription_content_changed(
            prescription,
            medicines=new_medicines,
            instructions=new_instructions,
            touch_medicines=touch_medicines,
            touch_instructions=touch_instructions,
        ):
            serializer = PrescriptionSerializer(prescription, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        with transaction.atomic():
            archive_current_before_update(prescription, request.user)
            if touch_medicines:
                prescription.medicines = new_medicines
            if touch_instructions:
                prescription.instructions = new_instructions
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

        # Ensure only the patient, doctor, assigned TMC, or staff can access it
        if not _is_consultation_participant(request.user, prescription.consultation):
            return Response({"error": "Unauthorized access"}, status=403)

        return generate_prescription_pdf(prescription_id)


class ConsultationEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, consultation_id):
        consultation = get_object_or_404(Consultation, id=consultation_id)
        if not _is_consultation_participant(request.user, consultation):
            return Response({"error": "Unauthorized access."}, status=403)
        order = (request.query_params.get("order") or "asc").lower()
        if order == "desc":
            events = consultation.events.order_by("-created_at", "-id")
        else:
            events = consultation.events.order_by("created_at", "id")
        return Response(ConsultationEventSerializer(events, many=True).data, status=200)


class PrescriptionVersionsView(APIView):
    """Archived prescription snapshots (assigned doctor or staff)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, consultation_id):
        consultation = get_object_or_404(Consultation, id=consultation_id)
        is_doctor = request.user == consultation.doctor.user
        if not is_doctor and not request.user.is_staff:
            return Response({"error": "Unauthorized access."}, status=403)
        followup_scope = _current_prescription_scope(consultation)
        prescription = Prescription.objects.prefetch_related("versions").filter(
            consultation=consultation,
            follow_up_session=followup_scope,
        ).order_by("-updated_at", "-id").first()
        if not prescription:
            return Response({"versions": [], "message": "No prescription for this consultation."}, status=200)
        versions = prescription.versions.order_by("version_number")
        return Response(
            {
                "prescription_id": prescription.id,
                "last_updated_at": prescription.updated_at,
                "version_rows": PrescriptionVersionSerializer(versions, many=True).data,
            },
            status=200,
        )


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
            "discount_percentage": str(tmc.discount_percentage),
            "discounted_used": tmc.discounted_consultations_used,
            "discounted_quota": tmc.discounted_consultation_quota,
            "discounted_remaining": tmc.discounted_consultations_remaining,
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
        supplied_tmc = request.data.get("tmc_id")
        if supplied_tmc is not None and str(supplied_tmc).strip() != str(tmc.pk):
            return Response({"error": "You cannot select another TMC's wallet."}, status=403)
        doctor_id = request.data.get("doctor_id")
        if not patient_id or not doctor_id:
            return Response({"error": "patient_id and doctor_id are required."}, status=400)
        patient = get_object_or_404(PatientProfile, id=patient_id, created_by_tmc=tmc)
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        amount = resolve_doctor_consultation_amount(
            Consultation.ConsultationType.TMC,
            doctor=doctor,
        )
        if not (
            doctor.profile_completed
            and doctor.admin_verified
            and doctor.is_approved
            and doctor.user.is_email_verified
        ):
            return Response({"error": "Doctor is not approved for consultations yet."}, status=400)
        open_consultation = Consultation.objects.filter(
            patient=patient,
            status__in=OPEN_CONSULTATION_STATUSES,
        ).select_related("doctor__user").order_by("-created_at").first()
        if open_consultation:
            doctor_name = open_consultation.doctor.user.get_full_name() or open_consultation.doctor.user.email
            return Response(
                {
                    "error": (
                        f"This patient already has an uncompleted consultation with Dr. {doctor_name}. "
                        "Complete or cancel it before booking another consultation."
                    )
                },
                status=400,
            )
        recent_same_doctor = Consultation.objects.filter(
            patient=patient,
            doctor=doctor,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=SAME_DOCTOR_REBOOKING_GAP_MINUTES),
            status__in=[
                Consultation.StatusChoices.COMPLETED,
                Consultation.StatusChoices.CANCELED,
                Consultation.StatusChoices.REJECTED,
                Consultation.StatusChoices.REJECTED_BY_PATIENT,
            ],
        ).order_by("-created_at").first()
        if recent_same_doctor:
            wait_until = recent_same_doctor.created_at + timezone.timedelta(minutes=SAME_DOCTOR_REBOOKING_GAP_MINUTES)
            remaining = max(1, int((wait_until - timezone.now()).total_seconds() // 60) + 1)
            return Response(
                {
                    "error": (
                        f"Please wait about {remaining} minute(s) before booking this patient "
                        "with the same doctor again."
                    )
                },
                status=400,
            )
        scheduled_time = request.data.get("scheduled_time")
        if scheduled_time:
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(scheduled_time)
            if not dt:
                return Response({"error": "Invalid scheduled_time format."}, status=400)
            scheduled_time = dt
        else:
            scheduled_time = timezone.now() + timezone.timedelta(minutes=10)

        try:
            with transaction.atomic():
                patient = get_object_or_404(
                    PatientProfile.objects.select_for_update(), pk=patient.pk, created_by_tmc=tmc
                )
                is_free = tmc.free_consultations_remaining > 0
                pricing = estimate_tmc_consultation_pricing(tmc, amount, is_free=is_free)
                if pricing["amount_charged"] > 0:
                    account = TMCAccount.objects.select_for_update().get_or_create(tmc=tmc)[0]
                    if Decimal(account.balance) < pricing["amount_charged"]:
                        return Response(
                            {
                                "error": (
                                    f"Insufficient TMC wallet balance. This consultation requires Rs {pricing['amount_charged']}; "
                                    f"available TMC wallet balance is Rs {account.balance}. Please recharge the wallet first."
                                )
                            },
                            status=400,
                        )
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
                if pricing["amount_charged"] > 0:
                    payment = Payment.objects.create(
                        consultation=consultation,
                        amount=pricing["amount_charged"],
                        status=Payment.Status.PENDING,
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
        except InsufficientBalanceError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "message": "TMC consultation created successfully.",
                "consultation_id": consultation.id,
                "status": consultation.status,
                "is_free": consultation.is_free,
                "amount_charged": str(consultation.finance.amount_charged),
                "doctor_fee": str(consultation.finance.doctor_fee),
                "platform_fee": str(consultation.finance.platform_fee),
                "discount_amount": str(consultation.finance.discount_amount),
                "admin_subsidy_amount": str(consultation.finance.admin_subsidy_amount),
            },
            status=201,
        )


class PatientWalletSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "patient_profile"):
            return Response({"error": "Only patients can access this endpoint."}, status=403)
        reconcile_approved_patient_recharges(request.user.patient_profile)
        wallet, _ = PatientWallet.objects.get_or_create(patient=request.user.patient_profile)
        entries = wallet.entries.all()[:20]
        recharge_requests = request.user.patient_profile.wallet_recharge_requests.all()[:10]
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
            "recent_recharge_requests": [
                {
                    "id": row.id,
                    "amount": str(row.amount),
                    "status": row.status,
                    "provider": row.provider,
                    "reference_note": row.reference_note,
                    "admin_note": row.admin_note,
                    "gateway_order_id": row.gateway_order_id,
                    "created_at": row.created_at,
                    "processed_at": row.processed_at,
                }
                for row in recharge_requests
            ],
        }
        return Response(data, status=200)

    def post(self, request):
        if not hasattr(request.user, "patient_profile"):
            return Response({"error": "Only patients can access this endpoint."}, status=403)
        amount = request.data.get("amount")
        if amount is None:
            return Response({"error": "amount is required."}, status=400)
        try:
            recharge = create_patient_recharge_request(
                request.user.patient_profile,
                amount,
                requested_by=request.user,
                reference_note=request.data.get("reference_note"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "message": "Recharge request created. Complete gateway payment or wait for admin approval.",
                "id": recharge.id,
                "amount": str(recharge.amount),
                "status": recharge.status,
                "provider": recharge.provider,
            },
            status=201,
        )


class PatientWalletRechargeOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recharge_id):
        if not hasattr(request.user, "patient_profile"):
            return Response({"error": "Only patients can access this endpoint."}, status=403)
        recharge = get_object_or_404(
            PatientWalletRechargeRequest,
            pk=recharge_id,
            patient=request.user.patient_profile,
        )
        try:
            recharge = create_patient_recharge_order_reference(recharge)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "recharge_request_id": recharge.id,
                "order_id": recharge.gateway_order_id,
                "amount": str(recharge.amount),
                "amount_paise": int(Decimal(recharge.amount) * 100),
                "currency": "INR",
                "provider": recharge.provider,
                "razorpay_enabled": settings.RAZORPAY_ENABLED,
                "key_id": settings.RAZORPAY_KEY_ID if settings.RAZORPAY_ENABLED else "",
            },
            status=200,
        )


class PatientWalletRechargeVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recharge_id):
        if not hasattr(request.user, "patient_profile"):
            return Response({"error": "Only patients can access this endpoint."}, status=403)
        recharge = get_object_or_404(
            PatientWalletRechargeRequest,
            pk=recharge_id,
            patient=request.user.patient_profile,
        )
        try:
            processed, entry = mark_patient_recharge_success(
                recharge,
                request.data.get("razorpay_payment_id"),
                request.data.get("razorpay_signature"),
                payload=request.data,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "message": "Wallet recharge successful.",
                "id": processed.id,
                "status": processed.status,
                "balance_after": str(entry.balance_after),
            },
            status=200,
        )


class PatientWalletRechargeCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recharge_id):
        if not hasattr(request.user, "patient_profile"):
            return Response({"error": "Only patients can access this endpoint."}, status=403)
        recharge = get_object_or_404(
            PatientWalletRechargeRequest,
            pk=recharge_id,
            patient=request.user.patient_profile,
        )
        recharge = cancel_patient_recharge_request(recharge)
        return Response(
            {
                "message": "Razorpay transaction was canceled. No wallet amount was added.",
                "id": recharge.id,
                "status": recharge.status,
            },
            status=200,
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


class ConsultationVideoJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, consultation_id):
        consultation = get_object_or_404(
            Consultation.objects.select_related("patient__user", "doctor__user", "tmc__user"),
            pk=consultation_id,
        )
        if not _is_consultation_participant(request.user, consultation):
            return Response({"error": "You are not allowed to join this consultation video."}, status=403)
        if consultation.status not in [
            Consultation.StatusChoices.ACCEPTED,
            Consultation.StatusChoices.QUEUED,
            Consultation.StatusChoices.IN_PROGRESS,
            Consultation.StatusChoices.POSTPONED,
            Consultation.StatusChoices.COMPLETED,
        ]:
            return Response(
                {"error": "Video can be prepared after the consultation is accepted or started."},
                status=400,
            )
        if _completion_required(consultation):
            return Response(
                {"error": "This consultation has been in progress for more than 24 hours. Please ask the doctor to mark it complete before using video again."},
                status=400,
            )
        try:
            return Response(get_or_create_video_join(consultation, request.user), status=200)
        except VideoProviderError as exc:
            return Response({"error": str(exc), "config": video_config_status()}, status=400)


class ConsultationVideoRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, consultation_id):
        consultation = get_object_or_404(
            Consultation.objects.select_related("patient__user", "doctor__user", "tmc__user"),
            pk=consultation_id,
        )
        if not _is_consultation_participant(request.user, consultation):
            return Response({"error": "You are not allowed to request this consultation video."}, status=403)
        if consultation.status not in [
            Consultation.StatusChoices.ACCEPTED,
            Consultation.StatusChoices.QUEUED,
            Consultation.StatusChoices.IN_PROGRESS,
            Consultation.StatusChoices.POSTPONED,
            Consultation.StatusChoices.COMPLETED,
        ]:
            return Response({"error": "Video can be requested after the consultation is accepted or started."}, status=400)
        if _completion_required(consultation):
            return Response(
                {"error": "This consultation has been in progress for more than 24 hours. Mark it complete before requesting video again."},
                status=400,
            )
        try:
            video = request_video_session(consultation, request.user)
        except VideoProviderError as exc:
            return Response({"error": str(exc), "config": video_config_status()}, status=400)
        return Response({"message": "Video request sent.", "video": video}, status=200)


class ConsultationVideoRespondView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, consultation_id):
        consultation = get_object_or_404(
            Consultation.objects.select_related("patient__user", "doctor__user", "tmc__user"),
            pk=consultation_id,
        )
        if not _is_consultation_participant(request.user, consultation):
            return Response({"error": "You are not allowed to respond to this consultation video."}, status=403)
        try:
            video = respond_to_video_session(
                consultation,
                request.user,
                str(request.data.get("action") or "").lower(),
            )
        except VideoProviderError as exc:
            return Response({"error": str(exc), "config": video_config_status()}, status=400)
        return Response({"message": f"Video request {video['status'].lower()}.", "video": video}, status=200)


class TMCFinanceSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _get_tmc_profile(request.user):
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        tmc_profile = _get_tmc_profile(request.user)
        reconcile_approved_tmc_recharges(tmc_profile)
        account, _ = TMCAccount.objects.get_or_create(tmc=tmc_profile)
        entries = account.entries.all()[:20]
        recharge_requests = tmc_profile.recharge_requests.all()[:10]
        return Response(
            {
                "balance": str(account.balance),
                "total_charged": str(account.total_charged),
                "total_credited": str(account.total_credited),
                "total_debited": str(account.total_debited),
                "discount_percentage": str(tmc_profile.discount_percentage),
                "discounted_quota": tmc_profile.discounted_consultation_quota,
                "discounted_used": tmc_profile.discounted_consultations_used,
                "discounted_remaining": tmc_profile.discounted_consultations_remaining,
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
                "recent_recharge_requests": [
                    {
                        "id": r.id,
                        "amount": str(r.amount),
                        "status": r.status,
                        "provider": r.provider,
                        "reference_note": r.reference_note,
                        "gateway_order_id": r.gateway_order_id,
                        "admin_note": r.admin_note,
                        "created_at": r.created_at,
                        "processed_at": r.processed_at,
                    }
                    for r in recharge_requests
                ],
            },
            status=200,
        )


class TMCRechargeRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tmc = _get_tmc_profile(request.user)
        if not tmc:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        rows = tmc.recharge_requests.all()[:20]
        return Response(
            [
                {
                    "id": row.id,
                    "amount": str(row.amount),
                    "status": row.status,
                    "provider": row.provider,
                    "reference_note": row.reference_note,
                    "gateway_order_id": row.gateway_order_id,
                    "admin_note": row.admin_note,
                    "created_at": row.created_at,
                    "processed_at": row.processed_at,
                }
                for row in rows
            ],
            status=200,
        )

    def post(self, request):
        tmc = _get_tmc_profile(request.user)
        if not tmc:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        amount = request.data.get("amount")
        if amount is None:
            return Response({"error": "amount is required."}, status=400)
        try:
            recharge = create_tmc_recharge_request(
                tmc,
                amount,
                requested_by=request.user,
                reference_note=request.data.get("reference_note"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "message": "Recharge request submitted for admin approval.",
                "id": recharge.id,
                "amount": str(recharge.amount),
                "status": recharge.status,
                "provider": recharge.provider,
            },
            status=201,
        )


class TMCRechargeOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recharge_id):
        tmc = _get_tmc_profile(request.user)
        if not tmc:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        recharge = get_object_or_404(TMCRechargeRequest, pk=recharge_id, tmc=tmc)
        try:
            recharge = create_tmc_recharge_order_reference(recharge)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "recharge_request_id": recharge.id,
                "order_id": recharge.gateway_order_id,
                "amount": str(recharge.amount),
                "amount_paise": int(Decimal(recharge.amount) * 100),
                "currency": "INR",
                "provider": recharge.provider,
                "razorpay_enabled": settings.RAZORPAY_ENABLED,
                "key_id": settings.RAZORPAY_KEY_ID if settings.RAZORPAY_ENABLED else "",
            },
            status=200,
        )


class TMCRechargeVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recharge_id):
        tmc = _get_tmc_profile(request.user)
        if not tmc:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        recharge = get_object_or_404(TMCRechargeRequest, pk=recharge_id, tmc=tmc)
        try:
            processed, entry = mark_tmc_recharge_success(
                recharge,
                request.data.get("razorpay_payment_id"),
                request.data.get("razorpay_signature"),
                payload=request.data,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "message": "TMC wallet recharge successful.",
                "id": processed.id,
                "status": processed.status,
                "balance_after": str(entry.balance_after),
            },
            status=200,
        )


class TMCRechargeCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recharge_id):
        tmc = _get_tmc_profile(request.user)
        if not tmc:
            return Response({"error": "Only TMC operators can access this endpoint."}, status=403)
        recharge = get_object_or_404(TMCRechargeRequest, pk=recharge_id, tmc=tmc)
        recharge = cancel_tmc_recharge_request(recharge)
        return Response(
            {
                "message": "Razorpay transaction was canceled. No wallet amount was added.",
                "id": recharge.id,
                "status": recharge.status,
            },
            status=200,
        )


class RazorpayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        payment = get_object_or_404(Payment.objects.select_related("consultation"), pk=payment_id)
        consultation = payment.consultation
        if not _can_manage_consultation_payment(request.user, consultation):
            return Response({"error": "Unauthorized access."}, status=403)
        try:
            payment = create_razorpay_order_reference(payment)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "payment_id": payment.id,
                "provider": payment.provider,
                "gateway_order_id": payment.gateway_order_id,
                "amount": str(payment.amount),
                "amount_paise": int(Decimal(payment.amount) * 100),
                "currency": payment.currency,
                "key_id_configured": bool(settings.RAZORPAY_KEY_ID),
            },
            status=200,
        )


class RazorpayVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        payment = get_object_or_404(Payment.objects.select_related("consultation"), pk=payment_id)
        consultation = payment.consultation
        if not _can_manage_consultation_payment(request.user, consultation):
            return Response({"error": "Unauthorized access."}, status=403)
        gateway_payment_id = request.data.get("razorpay_payment_id")
        signature = request.data.get("razorpay_signature")
        if not gateway_payment_id or not signature:
            return Response({"error": "razorpay_payment_id and razorpay_signature are required."}, status=400)
        try:
            payment = mark_razorpay_payment_success(
                payment,
                gateway_payment_id=gateway_payment_id,
                gateway_signature=signature,
                payload=request.data,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response({"message": "Payment verified.", "status": payment.status}, status=200)

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
        if not getattr(self.request.user, "is_doctor", False):
            raise PermissionDenied("Only doctor accounts can access the doctor profile workflow.")
        
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
        was_completed_before = doctor_profile.profile_completed
        serializer = self.get_serializer(doctor_profile, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response({
                "error": serializer.errors,
                "message": "Validation failed. Please check the errors below."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if doctor_profile.profile_completed:
            from django.utils import timezone
            from users.models.profiles import (
                DoctorProfileChangeRequest,
                filter_proposed_data_to_actual_changes,
            )

            pending_count = doctor_profile.change_requests.filter(
                status=DoctorProfileChangeRequest.Status.PENDING
            ).count()
            if pending_count >= MAX_PENDING_DOCTOR_PROFILE_CHANGE_REQUESTS:
                return Response(
                    {
                        "error": "Maximum pending profile change requests reached.",
                        "message": (
                            f"You may have up to {MAX_PENDING_DOCTOR_PROFILE_CHANGE_REQUESTS} change requests "
                            "waiting for admin review. Please wait for a decision before submitting more."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            file_fields = {
                "photo": "proposed_photo",
                "identity_proof": "proposed_identity_proof",
                "registration_certificate": "proposed_registration_certificate",
            }
            proposed_data = {}
            proposed_files = {}
            for field, value in serializer.validated_data.items():
                if field in file_fields:
                    proposed_files[file_fields[field]] = value
                else:
                    proposed_data[field] = str(value) if isinstance(value, Decimal) else value
            proposed_data = filter_proposed_data_to_actual_changes(doctor_profile, proposed_data)
            if not proposed_data and not proposed_files:
                return Response(
                    {"error": "No profile changes were submitted."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cr = DoctorProfileChangeRequest.objects.create(
                doctor=doctor_profile,
                requested_by=request.user,
                proposed_data=proposed_data,
                **proposed_files,
            )
            summary_parts = cr.get_summary_parts()
            try:
                from users.email_verification import send_doctor_profile_change_request_submitted_email

                send_doctor_profile_change_request_submitted_email(request.user, summary_parts)
            except Exception:
                logger.exception(
                    "Failed to send profile-change-submitted email for doctor_profile_id=%s",
                    doctor_profile.id,
                )
            doctor_profile.has_pending_changes = True
            doctor_profile.pending_changes_updated_at = timezone.now()
            doctor_profile.save(update_fields=["has_pending_changes", "pending_changes_updated_at", "updated_at"])
            return Response(
                {
                    "message": "Profile change request submitted for admin approval. Your current approved profile remains active until approval.",
                    "profile": self.get_serializer(doctor_profile).data,
                    "profile_completed": doctor_profile.profile_completed,
                    "change_request_created": True,
                    "change_request_id": cr.id,
                    "change_request_summary": summary_parts,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        serializer.save()

        # Refresh from DB to get updated completion status
        doctor_profile.refresh_from_db()

        if doctor_profile.profile_completed and not was_completed_before:
            try:
                from users.email_verification import send_doctor_profile_completed_email

                send_doctor_profile_completed_email(doctor_profile.user)
            except Exception:
                logger.exception("Failed to send doctor profile-completed email to %s", doctor_profile.user_id)

        return Response({
            "message": "Profile submitted successfully. Admin verification is required before consultations are enabled.",
            "profile": serializer.data,
            "profile_completed": doctor_profile.profile_completed,
            "change_request_created": False,
        }, status=status.HTTP_200_OK)
