"""Staff-only operational reports and CSV exports."""

import csv
import logging
from decimal import Decimal
from io import StringIO

from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import DoctorProfileChangeRequest, PatientProfile, TMCProfile
from users.models import DoctorProfile

from .finance import (
    admin_platform_topup,
    patient_wallet_topup,
    process_patient_recharge_request,
    process_tmc_recharge_request,
    tmc_account_topup,
)

logger = logging.getLogger(__name__)
from .models import (
    AdminPlatformAccount,
    AdminPlatformEntry,
    ConsultationFeeSetting,
    Consultation,
    ConsultationFinance,
    DoctorEarning,
    PatientWallet,
    PatientWalletEntry,
    PatientWalletRechargeRequest,
    Prescription,
    PrescriptionVersion,
    TMCAccount,
    TMCAccountEntry,
    TMCRechargeRequest,
)
from .permissions import IsStaffUser, FinancialWritePermission


class StaffPatientWalletTopupView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser, FinancialWritePermission]
    financial_write_permission = "consultations.change_patientwallet"

    def post(self, request):
        patient_profile_id = request.data.get("patient_profile_id")
        amount = request.data.get("amount")
        if patient_profile_id is None or amount is None:
            return Response({"error": "patient_profile_id and amount are required."}, status=400)
        patient = get_object_or_404(PatientProfile, pk=patient_profile_id)
        desc = request.data.get("description") or "Staff wallet top-up"
        try:
            entry = patient_wallet_topup(patient, amount, description=f"Staff #{request.user.pk}: {desc}")
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "message": "Wallet top-up recorded.",
                "entry_id": entry.id,
                "balance_after": str(entry.balance_after),
            },
            status=201,
        )


class StaffTMCWalletTopupView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser, FinancialWritePermission]
    financial_write_permission = "consultations.change_tmcaccount"

    def post(self, request):
        tmc_profile_id = request.data.get("tmc_profile_id")
        amount = request.data.get("amount")
        if tmc_profile_id is None or amount is None:
            return Response({"error": "tmc_profile_id and amount are required."}, status=400)
        tmc = get_object_or_404(TMCProfile, pk=tmc_profile_id)
        desc = request.data.get("description") or "Staff TMC wallet top-up"
        try:
            entry = tmc_account_topup(tmc, amount, description=f"Staff #{request.user.pk}: {desc}")
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "message": "TMC wallet top-up recorded.",
                "entry_id": entry.id,
                "balance_after": str(entry.balance_after),
            },
            status=201,
        )


class StaffTMCRechargeRequestProcessView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser, FinancialWritePermission]
    financial_write_permission = "consultations.change_tmcrechargerequest"

    def post(self, request, recharge_id):
        recharge = get_object_or_404(TMCRechargeRequest, pk=recharge_id)
        action = (request.data.get("action") or "approve").lower()
        if action not in {"approve", "reject"}:
            return Response({"error": "action must be approve or reject."}, status=400)
        try:
            processed, entry = process_tmc_recharge_request(
                recharge,
                approve=action == "approve",
                processed_by=request.user,
                admin_note=request.data.get("admin_note"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "message": f"Recharge request {processed.status.lower()}.",
                "id": processed.id,
                "status": processed.status,
                "entry_id": entry.id if entry else None,
            },
            status=200,
        )


class StaffPatientRechargeRequestProcessView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser, FinancialWritePermission]
    financial_write_permission = "consultations.change_patientwalletrechargerequest"

    def post(self, request, recharge_id):
        recharge = get_object_or_404(PatientWalletRechargeRequest, pk=recharge_id)
        action = (request.data.get("action") or "approve").lower()
        if action not in {"approve", "reject"}:
            return Response({"error": "action must be approve or reject."}, status=400)
        try:
            processed, entry = process_patient_recharge_request(
                recharge,
                approve=action == "approve",
                processed_by=request.user,
                admin_note=request.data.get("admin_note"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "message": f"Patient recharge request {processed.status.lower()}.",
                "id": processed.id,
                "status": processed.status,
                "entry_id": entry.id if entry else None,
            },
            status=200,
        )


class StaffAdminPlatformWalletTopupView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser, FinancialWritePermission]
    financial_write_permission = "consultations.change_adminplatformaccount"

    def post(self, request):
        amount = request.data.get("amount")
        if amount is None:
            return Response({"error": "amount is required."}, status=400)
        desc = request.data.get("description") or "Staff admin platform wallet top-up"
        try:
            entry = admin_platform_topup(amount, description=f"Staff #{request.user.pk}: {desc}")
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "message": "Admin platform wallet top-up recorded.",
                "entry_id": entry.id,
                "balance_after": str(entry.balance_after),
            },
            status=201,
        )


class StaffPatientRechargeRequestListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        rows = PatientWalletRechargeRequest.objects.select_related(
            "patient__user", "requested_by"
        ).order_by("-created_at")[:200]
        return Response(
            [
                {
                    "id": row.id,
                    "patient_profile_id": row.patient_id,
                    "patient_email": row.patient.user.email,
                    "patient_name": row.patient.user.get_full_name() or row.patient.user.email,
                    "amount": str(row.amount),
                    "status": row.status,
                    "provider": row.provider,
                    "reference_note": row.reference_note,
                    "admin_note": row.admin_note,
                    "created_at": row.created_at,
                    "processed_at": row.processed_at,
                }
                for row in rows
            ],
            status=200,
        )


class StaffTMCRechargeRequestListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        rows = TMCRechargeRequest.objects.select_related("tmc__user", "requested_by").order_by("-created_at")[:200]
        return Response(
            [
                {
                    "id": row.id,
                    "tmc_profile_id": row.tmc_id,
                    "tmc_email": row.tmc.user.email,
                    "tmc_name": row.tmc.user.get_full_name() or row.tmc.user.email,
                    "amount": str(row.amount),
                    "status": row.status,
                    "reference_note": row.reference_note,
                    "admin_note": row.admin_note,
                    "created_at": row.created_at,
                    "processed_at": row.processed_at,
                }
                for row in rows
            ],
            status=200,
        )


class StaffTMCOfferSerializer(serializers.Serializer):
    free_consultation_quota = serializers.IntegerField(min_value=0, required=False)
    discounted_consultation_quota = serializers.IntegerField(min_value=0, required=False)
    discount_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100"), required=False,
    )


class StaffTMCListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser, FinancialWritePermission]
    financial_write_permission = "users.change_tmcprofile"

    def get(self, request):
        rows = TMCProfile.objects.select_related("user").order_by("-created_at")[:200]
        return Response(
            [
                {
                    "id": row.id,
                    "name": row.user.get_full_name() or row.user.email,
                    "email": row.user.email,
                    "phone_number": row.user.phone_number,
                    "is_active": row.is_active,
                    "free_quota": row.free_consultation_quota,
                    "free_used": row.free_consultations_used,
                    "discount_percentage": str(row.discount_percentage),
                    "discounted_quota": row.discounted_consultation_quota,
                    "discounted_used": row.discounted_consultations_used,
                }
                for row in rows
            ],
            status=200,
        )

    def patch(self, request):
        tmc_profile_id = request.data.get("tmc_profile_id")
        if not tmc_profile_id:
            return Response({"error": "tmc_profile_id is required."}, status=400)
        if {"free_consultations_used", "discounted_consultations_used"}.intersection(request.data):
            return Response({"error": "Usage counters are recorded by consultations and cannot be edited."}, status=400)
        serializer = StaffTMCOfferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data:
            return Response({"error": "No TMC offer fields supplied."}, status=400)
        from django.contrib.admin.models import LogEntry, CHANGE
        from django.db import transaction

        with transaction.atomic():
            tmc = get_object_or_404(TMCProfile.objects.select_for_update(), pk=tmc_profile_id)
            for field, value in serializer.validated_data.items():
                setattr(tmc, field, value)
            tmc.save(update_fields=list(serializer.validated_data))
            LogEntry.objects.log_actions(
                user_id=request.user.pk, queryset=[tmc], action_flag=CHANGE,
                change_message=[{"changed": {"fields": list(serializer.validated_data)}}],
            )
        return Response(
            {
                "message": "TMC offer settings updated.",
                "id": tmc.id,
                "free_quota": tmc.free_consultation_quota,
                "free_used": tmc.free_consultations_used,
                "discount_percentage": str(tmc.discount_percentage),
                "discounted_quota": tmc.discounted_consultation_quota,
                "discounted_used": tmc.discounted_consultations_used,
            },
            status=200,
        )


class StaffPatientListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        rows = PatientProfile.objects.select_related("user").order_by("-created_at")[:300]
        data = []
        for row in rows:
            wallet, _ = PatientWallet.objects.get_or_create(patient=row)
            direct_count = Consultation.objects.filter(
                patient=row,
                consultation_type=Consultation.ConsultationType.DIRECT,
            ).count()
            tmc_qs = Consultation.objects.filter(
                patient=row,
                consultation_type=Consultation.ConsultationType.TMC,
            ).select_related("tmc__user")
            tmc_count = tmc_qs.count()
            if direct_count and tmc_count:
                patient_type = "BOTH"
            elif tmc_count:
                patient_type = "TMC_ASSISTED"
            elif direct_count:
                patient_type = "DIRECT"
            else:
                patient_type = "REGISTERED"
            tmc_names = sorted(
                {
                    c.tmc.user.get_full_name() or c.tmc.user.email
                    for c in tmc_qs
                    if c.tmc_id and c.tmc
                }
            )
            data.append(
                {
                    "id": row.id,
                    "name": row.user.get_full_name() or row.user.email,
                    "email": row.user.email,
                    "phone_number": row.user.phone_number,
                    "gender": row.gender,
                    "age": row.age,
                    "is_active": row.is_active,
                    "patient_type": patient_type,
                    "direct_consultations": direct_count,
                    "tmc_consultations": tmc_count,
                    "tmc_names": tmc_names,
                    "wallet_balance": str(wallet.balance),
                    "wallet_credited": str(wallet.total_credited),
                    "wallet_debited": str(wallet.total_debited),
                    "created_at": row.created_at,
                }
            )
        return Response(data, status=200)


class StaffFeeSettingSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, default="Default consultation fees")
    direct_patient_fee = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0"), default=0)
    tmc_consultation_fee = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0"), default=0)
    platform_fee_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100"), default=0,
    )
    currency = serializers.CharField(max_length=10, default="INR")


class StaffFeeSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser, FinancialWritePermission]
    financial_write_permission = "consultations.add_consultationfeesetting"

    def get(self, request):
        rows = ConsultationFeeSetting.objects.order_by("-created_at")[:20]
        return Response(
            [
                {
                    "id": row.id,
                    "name": row.name,
                    "direct_patient_fee": str(row.direct_patient_fee),
                    "tmc_consultation_fee": str(row.tmc_consultation_fee),
                    "platform_fee_percentage": str(row.platform_fee_percentage),
                    "currency": row.currency,
                    "is_active": row.is_active,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                }
                for row in rows
            ],
            status=200,
        )

    def post(self, request):
        serializer = StaffFeeSettingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from django.db import transaction

        with transaction.atomic():
            ConsultationFeeSetting.objects.filter(is_active=True).update(is_active=False)
            setting = ConsultationFeeSetting.objects.create(
                **serializer.validated_data, is_active=True, created_by=request.user,
            )
        return Response(
            {
                "message": "Fee setting activated.",
                "id": setting.id,
                "direct_patient_fee": str(setting.direct_patient_fee),
                "tmc_consultation_fee": str(setting.tmc_consultation_fee),
                "platform_fee_percentage": str(setting.platform_fee_percentage),
                "currency": setting.currency,
            },
            status=201,
        )


class StaffDoctorVerificationListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        doctors = DoctorProfile.objects.select_related("user").order_by("-created_at")[:200]
        return Response(
            [
                {
                    "id": doctor.id,
                    "email": doctor.user.email,
                    "name": doctor.user.get_full_name() or doctor.user.email,
                    "phone_number": doctor.user.phone_number,
                    "specialty": doctor.specialty,
                    "qualification": doctor.qualification,
                    "profile_completed": doctor.profile_completed,
                    "admin_verified": doctor.admin_verified,
                    "is_approved": doctor.is_approved,
                    "has_pending_changes": doctor.has_pending_changes,
                    "pending_change_request_count": doctor.change_requests.filter(
                        status=DoctorProfileChangeRequest.Status.PENDING
                    ).count(),
                    "created_at": doctor.created_at,
                }
                for doctor in doctors
            ],
            status=200,
        )


class StaffDoctorVerificationUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def post(self, request, doctor_profile_id):
        doctor = get_object_or_404(DoctorProfile, pk=doctor_profile_id)
        was_verified_before = doctor.admin_verified
        was_approved_before = doctor.is_approved
        action = (request.data.get("action") or "").lower()
        if action not in {"verify", "unverify", "approve", "unapprove"}:
            return Response(
                {"error": "action must be verify, unverify, approve, or unapprove."},
                status=400,
            )

        from django.utils import timezone

        fields = []
        pending_applied = False

        if action == "verify":
            pending_request = doctor.change_requests.filter(
                status=DoctorProfileChangeRequest.Status.PENDING
            ).order_by("-requested_at").first()
            if pending_request:
                doctor = pending_request.apply_to_profile(
                    reviewed_by=request.user,
                    admin_note=request.data.get("admin_note"),
                )
                pending_applied = True
            else:
                if not doctor.profile_completed:
                    return Response({"error": "Doctor profile is not complete."}, status=400)
                doctor.admin_verified = True
                doctor.admin_verified_at = timezone.now()
                doctor.admin_verified_by = request.user
                doctor.has_pending_changes = False
                doctor.pending_changes_updated_at = None
                fields = [
                    "admin_verified",
                    "admin_verified_at",
                    "admin_verified_by",
                    "has_pending_changes",
                    "pending_changes_updated_at",
                    "updated_at",
                ]

        elif action == "unverify":
            doctor.admin_verified = False
            doctor.is_approved = False
            doctor.admin_verified_at = None
            doctor.admin_verified_by = None
            fields = ["admin_verified", "is_approved", "admin_verified_at", "admin_verified_by", "updated_at"]

        elif action == "approve":
            if not doctor.profile_completed:
                return Response({"error": "Doctor profile is not complete."}, status=400)
            if not doctor.admin_verified:
                return Response(
                    {"error": "Verify the doctor profile before approving consultations."},
                    status=400,
                )
            doctor.is_approved = True
            fields = ["is_approved", "updated_at"]

        elif action == "unapprove":
            doctor.is_approved = False
            fields = ["is_approved", "updated_at"]

        if fields:
            doctor.save(update_fields=fields)

        if action == "verify" and doctor.admin_verified and not was_verified_before and not pending_applied:
            try:
                from users.email_verification import send_doctor_profile_admin_verified_email

                send_doctor_profile_admin_verified_email(doctor.user)
            except Exception:
                logger.exception("Failed to send profile-verified email for doctor_profile_id=%s", doctor.id)

        if action == "approve" and doctor.is_approved and not was_approved_before:
            try:
                from users.email_verification import send_doctor_consultations_approved_email

                send_doctor_consultations_approved_email(doctor.user)
            except Exception:
                logger.exception("Failed to send consultations-approved email for doctor_profile_id=%s", doctor.id)

        return Response(
            {
                "message": "Doctor verification updated.",
                "id": doctor.id,
                "admin_verified": doctor.admin_verified,
                "is_approved": doctor.is_approved,
            },
            status=200,
        )


class StaffOperationsReportView(APIView):
    """JSON summary for operations / finance audit (staff only)."""

    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        qs = Consultation.objects.all()
        fin = ConsultationFinance.objects.all()
        by_status = {
            row["status"]: row["c"]
            for row in qs.values("status").annotate(c=Count("id"))
        }
        direct = qs.filter(consultation_type=Consultation.ConsultationType.DIRECT).count()
        tmc_src = qs.filter(consultation_type=Consultation.ConsultationType.TMC).count()
        free_fin = fin.filter(billing_type=ConsultationFinance.BillingType.FREE).count()
        paid_fin = fin.filter(billing_type=ConsultationFinance.BillingType.PAID).count()

        doctor_counts = list(
            qs.values("doctor__user__email")
            .annotate(n=Count("id"))
            .order_by("-n")[:50]
        )
        earning_by_doctor = list(
            DoctorEarning.objects.values("doctor__user__email")
            .annotate(total=Sum("earning_amount"), n=Count("id"))
            .order_by("-total")[:50]
        )

        wallet_agg = PatientWallet.objects.aggregate(
            wallets=Count("id"),
            sum_balance=Sum("balance"),
        )
        tmc_fin_agg = ConsultationFinance.objects.filter(
            source_type=ConsultationFinance.SourceType.TMC
        ).aggregate(
            n=Count("id"),
            charged=Sum("amount_charged"),
        )
        admin_account = AdminPlatformAccount.objects.first()

        terminal = Consultation.StatusChoices
        recent_terminal = qs.filter(
            status__in=[
                terminal.CANCELED,
                terminal.REJECTED,
                terminal.REJECTED_BY_PATIENT,
                terminal.POSTPONED,
            ]
        ).order_by("-last_status_changed_at")[:30]

        rx_count = Prescription.objects.count()
        recent_rx = PrescriptionVersion.objects.order_by("-created_at")[:15]

        stuck = qs.filter(
            status__in=[Consultation.StatusChoices.PENDING, Consultation.StatusChoices.ACCEPTED, Consultation.StatusChoices.QUEUED]
        ).filter(last_status_changed_at__isnull=False)[:50]

        missing_finance_completed = list(
            Consultation.objects.filter(
                status=Consultation.StatusChoices.COMPLETED, finance__isnull=True
            ).values_list("id", flat=True)[:20]
        )

        data = {
            "consultations_total": qs.count(),
            "consultations_by_status": {k: by_status.get(k, 0) for k in [s[0] for s in Consultation.StatusChoices.choices]},
            "consultations_by_source": {"DIRECT": direct, "TMC": tmc_src},
            "finance_free_count": free_fin,
            "finance_paid_count": paid_fin,
            "doctor_consultation_counts": list(doctor_counts),
            "doctor_earning_totals": [
                {"doctor__user__email": r["doctor__user__email"], "total": str(r["total"] or "0"), "n": r["n"]}
                for r in earning_by_doctor
            ],
            "patient_wallets": {
                "count": wallet_agg["wallets"] or 0,
                "sum_balance": str(wallet_agg["sum_balance"] or Decimal("0")),
            },
            "tmc_finance_rollups": {
                "finance_rows": tmc_fin_agg["n"] or 0,
                "amount_charged_sum": str(tmc_fin_agg["charged"] or Decimal("0")),
                "account_count": TMCAccount.objects.count(),
                "pending_recharge_requests": TMCRechargeRequest.objects.filter(
                    status=TMCRechargeRequest.Status.PENDING
                ).count(),
            },
            "admin_platform_wallet": {
                "balance": str(admin_account.balance if admin_account else Decimal("0")),
                "total_platform_fees": str(admin_account.total_platform_fees if admin_account else Decimal("0")),
                "total_doctor_subsidies": str(admin_account.total_doctor_subsidies if admin_account else Decimal("0")),
                "recent_entries": [
                    {
                        "id": entry.id,
                        "entry_type": entry.entry_type,
                        "amount": str(entry.amount),
                        "balance_after": str(entry.balance_after),
                        "consultation_id": entry.consultation_id,
                        "description": entry.description,
                        "created_at": entry.created_at,
                    }
                    for entry in AdminPlatformEntry.objects.order_by("-created_at")[:20]
                ],
            },
            "recent_cancellations_rejections_postponed": [
                {
                    "id": c.id,
                    "status": c.status,
                    "doctor": c.doctor.user.email,
                    "patient": c.patient.user.email,
                    "last_status_changed_at": c.last_status_changed_at,
                    "terminal_reason": c.terminal_reason,
                }
                for c in recent_terminal
            ],
            "prescription_count": rx_count,
            "recent_prescription_version_activity": [
                {
                    "prescription_id": v.prescription_id,
                    "version_number": v.version_number,
                    "created_at": v.created_at,
                    "created_by": v.created_by.email if v.created_by else None,
                }
                for v in recent_rx
            ],
            "integrity_hints": {
                "completed_without_finance_row_sample": list(missing_finance_completed),
                "open_consultations_sample_ids": [c.id for c in stuck[:20]],
            },
        }
        return Response(data, status=200)


def _csv_response(filename, rows, header):
    buf = StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for row in rows:
        w.writerow(row)
    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


class StaffExportConsultationsCSVView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        rows = []
        header = [
            "id",
            "status",
            "consultation_type",
            "is_free",
            "doctor_email",
            "patient_email",
            "tmc_email",
            "queue_number",
            "created_at",
            "finance_billing_type",
            "finance_amount_charged",
            "finance_doctor_fee",
            "finance_platform_fee",
            "finance_discount_amount",
            "finance_admin_subsidy_amount",
            "finance_payment_status",
        ]
        for c in Consultation.objects.select_related(
            "doctor__user", "patient__user", "tmc__user", "finance"
        ).order_by("-id")[:5000]:
            fin = getattr(c, "finance", None)
            rows.append(
                [
                    c.id,
                    c.status,
                    c.consultation_type,
                    c.is_free,
                    c.doctor.user.email,
                    c.patient.user.email,
                    c.tmc.user.email if c.tmc else "",
                    c.queue_number or "",
                    c.created_at.isoformat() if c.created_at else "",
                    fin.billing_type if fin else "",
                    str(fin.amount_charged) if fin else "",
                    str(fin.doctor_fee) if fin else "",
                    str(fin.platform_fee) if fin else "",
                    str(fin.discount_amount) if fin else "",
                    str(fin.admin_subsidy_amount) if fin else "",
                    fin.payment_status if fin else "",
                ]
            )
        return _csv_response("consultations_export.csv", rows, header)


class StaffExportDoctorEarningsCSVView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        header = [
            "id",
            "consultation_id",
            "doctor_email",
            "billing_type",
            "source_type",
            "earning_amount",
            "status",
            "created_at",
        ]
        rows = []
        for e in DoctorEarning.objects.select_related("doctor__user", "consultation").order_by("-id")[:5000]:
            rows.append(
                [
                    e.id,
                    e.consultation_id,
                    e.doctor.user.email,
                    e.billing_type,
                    e.source_type,
                    str(e.earning_amount),
                    e.status,
                    e.created_at.isoformat() if e.created_at else "",
                ]
            )
        return _csv_response("doctor_earnings_export.csv", rows, header)


class StaffExportTMCEntriesCSVView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        header = [
            "id",
            "tmc_email",
            "entry_type",
            "amount",
            "balance_after",
            "consultation_id",
            "description",
            "created_at",
        ]
        rows = []
        for e in TMCAccountEntry.objects.select_related("account__tmc__user").order_by("-id")[:5000]:
            rows.append(
                [
                    e.id,
                    e.account.tmc.user.email,
                    e.entry_type,
                    str(e.amount),
                    str(e.balance_after),
                    e.consultation_id or "",
                    (e.description or "")[:200],
                    e.created_at.isoformat() if e.created_at else "",
                ]
            )
        return _csv_response("tmc_account_entries_export.csv", rows, header)


class StaffExportPatientWalletCSVView(APIView):
    """Export ledger for one patient (patient_profile_id query param)."""

    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        pid = request.query_params.get("patient_profile_id")
        if not pid:
            return Response({"error": "patient_profile_id query parameter is required."}, status=400)
        patient = get_object_or_404(PatientProfile, pk=pid)
        wallet, _ = PatientWallet.objects.get_or_create(patient=patient)
        header = ["id", "entry_type", "amount", "balance_after", "consultation_id", "description", "created_at"]
        rows = []
        for e in wallet.entries.order_by("-id")[:5000]:
            rows.append(
                [
                    e.id,
                    e.entry_type,
                    str(e.amount),
                    str(e.balance_after),
                    e.consultation_id or "",
                    (e.description or "")[:200],
                    e.created_at.isoformat() if e.created_at else "",
                ]
            )
        return _csv_response(f"patient_wallet_{pid}_ledger.csv", rows, header)


class StaffExportSummaryCSVView(APIView):
    """Single CSV with high-level counts (staff)."""

    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        qs = Consultation.objects.all()
        fin = ConsultationFinance.objects.all()
        header = ["metric", "value"]
        data_rows = [
            ["consultations_total", str(qs.count())],
            ["direct_consultations", str(qs.filter(consultation_type=Consultation.ConsultationType.DIRECT).count())],
            ["tmc_consultations", str(qs.filter(consultation_type=Consultation.ConsultationType.TMC).count())],
            ["finance_free", str(fin.filter(billing_type=ConsultationFinance.BillingType.FREE).count())],
            ["finance_paid", str(fin.filter(billing_type=ConsultationFinance.BillingType.PAID).count())],
            ["prescriptions", str(Prescription.objects.count())],
            ["prescription_versions", str(PrescriptionVersion.objects.count())],
            ["doctor_earning_records", str(DoctorEarning.objects.count())],
            ["patient_wallets", str(PatientWallet.objects.count())],
        ]
        return _csv_response("operations_summary.csv", data_rows, header)


class StaffConsultationAuditView(APIView):
    """Single consultation drill-down for support (staff)."""

    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request, consultation_id):
        c = get_object_or_404(
            Consultation.objects.select_related(
                "doctor__user",
                "patient__user",
                "tmc__user",
                "payment",
                "finance",
            ),
            pk=consultation_id,
        )
        events = c.events.order_by("created_at")
        fin = getattr(c, "finance", None)
        pay = getattr(c, "payment", None)
        rx = Prescription.objects.filter(consultation=c).order_by("-updated_at", "-id").first()
        earning = DoctorEarning.objects.filter(consultation_id=c.id).first()
        wallet_entries = list(
            PatientWalletEntry.objects.filter(consultation=c).values(
                "id", "entry_type", "amount", "description", "created_at"
            )
        )
        tmc_entries = list(
            TMCAccountEntry.objects.filter(consultation=c).values(
                "id", "entry_type", "amount", "description", "created_at"
            )
        )
        rx_versions = []
        if rx:
            rx_versions = list(
                rx.versions.order_by("version_number").values(
                    "version_number", "created_at", "created_by_id"
                )
            )
        return Response(
            {
                "consultation": {
                    "id": c.id,
                    "status": c.status,
                    "consultation_type": c.consultation_type,
                    "is_free": c.is_free,
                    "doctor": c.doctor.user.email,
                    "patient": c.patient.user.email,
                    "tmc": c.tmc.user.email if c.tmc else None,
                    "queue_number": c.queue_number,
                    "terminal_reason": c.terminal_reason,
                    "last_status_changed_at": c.last_status_changed_at,
                    "created_at": c.created_at,
                },
                "payment": (
                    {
                        "id": pay.id,
                        "amount": str(pay.amount),
                        "status": pay.status,
                        "paid_by_tmc": pay.paid_by_tmc,
                    }
                    if pay
                    else None
                ),
                "finance": (
                    {
                        "source_type": fin.source_type,
                        "billing_type": fin.billing_type,
                        "payment_status": fin.payment_status,
                        "amount_charged": str(fin.amount_charged),
                        "doctor_fee": str(fin.doctor_fee),
                        "platform_fee": str(fin.platform_fee),
                        "discount_amount": str(fin.discount_amount),
                        "admin_subsidy_amount": str(fin.admin_subsidy_amount),
                        "doctor_earning_status": fin.doctor_earning_status,
                        "notes": fin.notes,
                    }
                    if fin
                    else None
                ),
                "doctor_earning": (
                    {
                        "earning_amount": str(earning.earning_amount),
                        "status": earning.status,
                        "billing_type": earning.billing_type,
                    }
                    if earning
                    else None
                ),
                "events_chronological": [
                    {
                        "event_type": e.event_type,
                        "from_status": e.from_status,
                        "to_status": e.to_status,
                        "actor": e.actor.email if e.actor else None,
                        "note": e.note,
                        "created_at": e.created_at,
                    }
                    for e in events
                ],
                "wallet_entries_for_consultation": wallet_entries,
                "tmc_entries_for_consultation": tmc_entries,
                "prescription": (
                    {"id": rx.id, "updated_at": rx.updated_at} if rx else None
                ),
                "prescription_version_rows": rx_versions,
            },
            status=200,
        )
