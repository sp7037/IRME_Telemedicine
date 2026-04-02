"""Staff-only operational reports and CSV exports."""

import csv
from decimal import Decimal
from io import StringIO

from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import PatientProfile

from .finance import patient_wallet_topup
from .models import (
    Consultation,
    ConsultationFinance,
    DoctorEarning,
    PatientWallet,
    PatientWalletEntry,
    Prescription,
    PrescriptionVersion,
    TMCAccountEntry,
)
from .permissions import IsStaffUser


class StaffPatientWalletTopupView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def post(self, request):
        patient_profile_id = request.data.get("patient_profile_id")
        amount = request.data.get("amount")
        if patient_profile_id is None or amount is None:
            return Response({"error": "patient_profile_id and amount are required."}, status=400)
        patient = get_object_or_404(PatientProfile, pk=patient_profile_id)
        desc = request.data.get("description") or "Staff wallet top-up"
        entry = patient_wallet_topup(patient, amount, description=desc)
        return Response(
            {
                "message": "Wallet top-up recorded.",
                "entry_id": entry.id,
                "balance_after": str(entry.balance_after),
            },
            status=201,
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
                "prescription",
            ),
            pk=consultation_id,
        )
        events = c.events.order_by("created_at")
        fin = getattr(c, "finance", None)
        pay = getattr(c, "payment", None)
        rx = getattr(c, "prescription", None)
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
