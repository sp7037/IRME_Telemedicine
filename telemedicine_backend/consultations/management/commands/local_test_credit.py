"""Explicit local test funding through the existing ledger services; no gateway."""
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from users.models import User, PatientProfile, TMCProfile
from consultations.finance import patient_wallet_topup, tmc_account_topup


class Command(BaseCommand):
    help = "Record labelled local test credit for one patient or TMC. Requires DEBUG and a local database."

    def add_arguments(self, parser):
        target = parser.add_mutually_exclusive_group(required=True)
        target.add_argument("--patient-id", type=int)
        target.add_argument("--tmc-id", type=int)
        parser.add_argument("--amount", required=True)
        parser.add_argument("--actor-email", required=True)
        parser.add_argument("--confirm-local", action="store_true", required=True)

    def handle(self, *args, **options):
        db = settings.DATABASES["default"]
        if not (settings.DEBUG and options["confirm_local"] and db.get("HOST") in {"127.0.0.1", "localhost", "::1"}
                and db.get("ENGINE") == "django.db.backends.postgresql"):
            raise CommandError("Test credit is restricted to explicit local PostgreSQL development with DEBUG enabled.")
        try:
            amount = Decimal(options["amount"])
            if not amount.is_finite() or amount <= 0 or amount > Decimal("99999999.99") or amount != amount.quantize(Decimal("0.01")):
                raise ValueError()
        except (ValueError, InvalidOperation):
            raise CommandError("Amount must be positive INR with at most two decimal places.")
        actor = User.objects.filter(email=options["actor_email"], is_active=True, is_staff=True).first()
        is_patient = options.get("patient_id") is not None
        permission = "consultations.change_patientwallet" if is_patient else "consultations.change_tmcaccount"
        if not actor or not actor.has_perm(permission):
            raise CommandError("An active staff actor with the target wallet change permission is required.")
        model, target_id, poster = ((PatientProfile, options["patient_id"], patient_wallet_topup) if is_patient
                                   else (TMCProfile, options["tmc_id"], tmc_account_topup))
        profile = model.objects.filter(pk=target_id).first()
        if not profile:
            raise CommandError("Target profile not found; no credit recorded.")
        with transaction.atomic():
            entry = poster(profile, amount, description=f"LOCAL TEST CREDIT; staff #{actor.pk}; no external payment")
            LogEntry.objects.log_actions(user_id=actor.pk, queryset=[entry], action_flag=CHANGE,
                change_message="Explicit local test credit through the existing finance posting service; no external payment.")
        self.stdout.write(self.style.SUCCESS(f"Local test entry #{entry.pk} recorded; balance INR {entry.balance_after}."))
