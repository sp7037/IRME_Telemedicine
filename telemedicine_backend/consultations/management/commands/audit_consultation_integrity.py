"""Report (and optionally repair) common consultation / finance inconsistencies."""

from django.core.management.base import BaseCommand

from consultations.finance import ensure_doctor_earning_for_completion
from consultations.models import Consultation, ConsultationFinance, DoctorEarning, Prescription, PrescriptionVersion


class Command(BaseCommand):
    help = "List integrity issues; use --repair-earnings to backfill DoctorEarning for completed paid rows."

    def add_arguments(self, parser):
        parser.add_argument(
            "--repair-earnings",
            action="store_true",
            help="Create/update DoctorEarning for completed consultations that have ConsultationFinance but no earning.",
        )

    def handle(self, *args, **options):
        repair = options["repair_earnings"]

        missing_finance = list(
            Consultation.objects.filter(
                status=Consultation.StatusChoices.COMPLETED, finance__isnull=True
            ).values_list("id", flat=True)[:100]
        )
        if missing_finance:
            self.stdout.write(f"Completed without ConsultationFinance (sample up to 100): {missing_finance}")

        missing_rx_version = []
        for p in Prescription.objects.all()[:500]:
            if not PrescriptionVersion.objects.filter(prescription_id=p.pk).exists():
                missing_rx_version.append(p.id)
        if missing_rx_version:
            self.stdout.write(f"Prescriptions without any PrescriptionVersion row: {missing_rx_version}")

        earning_gaps = []
        for c in Consultation.objects.filter(
            status=Consultation.StatusChoices.COMPLETED
        ).iterator():
            fin = ConsultationFinance.objects.filter(consultation_id=c.id).first()
            if not fin or fin.billing_type != ConsultationFinance.BillingType.PAID:
                continue
            if not DoctorEarning.objects.filter(consultation_id=c.id).exists():
                earning_gaps.append(c.id)
        if earning_gaps:
            self.stdout.write(f"Completed + paid finance but no DoctorEarning: {earning_gaps[:50]}")

        if repair and earning_gaps:
            for cid in earning_gaps:
                c = Consultation.objects.filter(pk=cid).first()
                if c:
                    ensure_doctor_earning_for_completion(c)
                    self.stdout.write(self.style.SUCCESS(f"Repaired earning for consultation {cid}"))
        elif repair:
            self.stdout.write("No earning gaps to repair.")
