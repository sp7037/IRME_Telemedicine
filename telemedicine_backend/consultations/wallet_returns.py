"""Conservative legacy pre-start wallet returns. No provider refund or quota reset."""
from decimal import Decimal

from django.db import transaction

from .models import (
    Consultation, ConsultationEvent, ConsultationFinance, Payment, DoctorEarning,
    PatientWallet, PatientWalletEntry, TMCAccount, TMCAccountEntry,
    AdminPlatformAccount, AdminPlatformEntry, ConsultationChat, Prescription,
)


def wallet_return_summary(consultation):
    event = consultation.events.filter(metadata__has_key="wallet_return").order_by("-id").first()
    data = (event.metadata or {}).get("wallet_return", {}) if event else {}
    return {key: data[key] for key in ("status", "amount", "currency", "destination", "reference") if key in data}


@transaction.atomic
def record_historical_rejection_review(consultation_id):
    """Trusted operator/system repair only; no HTTP route or automatic backfill."""
    consultation = Consultation.objects.select_for_update().get(pk=consultation_id)
    existing = wallet_return_summary(consultation)
    if existing:
        return existing
    decision = consultation.events.filter(event_type=ConsultationEvent.EventType.POSTPONE_REJECTED,
        from_status=Consultation.StatusChoices.POSTPONED,
        to_status=Consultation.StatusChoices.REJECTED_BY_PATIENT).order_by("id").first()
    if consultation.status != Consultation.StatusChoices.REJECTED_BY_PATIENT or not decision:
        raise ValueError("No recorded historical postponement rejection to review.")
    outcome = return_verified_prestart_charge(consultation, decision.from_status, actor=None)
    ConsultationEvent.objects.create(consultation=consultation,
        event_type=ConsultationEvent.EventType.POSTPONE_REJECTED,
        from_status=consultation.status, to_status=consultation.status,
        note="System financial reconciliation of the earlier rejection; no new consultation decision.",
        metadata={"financial_reconciliation": True, "original_decision_event_id": decision.pk,
                  "wallet_return": outcome})
    return wallet_return_summary(consultation)


@transaction.atomic
def return_verified_prestart_charge(consultation, from_status, actor):
    """Caller holds consultation lock and commits this outcome with its terminal event."""
    consultation = Consultation.objects.select_for_update().get(pk=consultation.pk)
    def review(code):
        return {"status": "REVIEW_REQUIRED", "reason_code": code, "currency": "INR"}

    existing = wallet_return_summary(consultation)
    if existing:
        return existing
    if consultation.status not in {Consultation.StatusChoices.REJECTED_BY_PATIENT,
                                  Consultation.StatusChoices.REJECTED, Consultation.StatusChoices.CANCELED}:
        return review("NOT_A_TERMINAL_CANCELLATION")
    if from_status not in {Consultation.StatusChoices.PENDING, Consultation.StatusChoices.POSTPONED}:
        return review("START_EVIDENCE_REQUIRES_REVIEW")
    events = consultation.events.all()
    if not events.filter(event_type=ConsultationEvent.EventType.REQUESTED).exists():
        return review("MISSING_BOOKING_EVIDENCE")
    if from_status == Consultation.StatusChoices.POSTPONED and not events.filter(
        event_type=ConsultationEvent.EventType.POSTPONED, from_status=Consultation.StatusChoices.PENDING,
    ).exists():
        return review("MISSING_PRESTART_POSTPONEMENT")
    if (events.filter(event_type__in=[ConsultationEvent.EventType.STARTED, ConsultationEvent.EventType.COMPLETED]).exists()
            or ConsultationChat.objects.filter(consultation=consultation).exists()
            or Prescription.objects.filter(consultation=consultation).exists()
            or DoctorEarning.objects.filter(consultation=consultation).exists()):
        return review("CONFLICTING_SERVICE_EVIDENCE")
    payment = Payment.objects.select_for_update().filter(consultation=consultation).first()
    finance = ConsultationFinance.objects.select_for_update().filter(consultation=consultation).first()
    if not finance:
        return review("MISSING_FINANCE")
    if finance.amount_charged == 0:
        if consultation.tmc_id:
            return review("LEGACY_QUOTA_PERIOD_UNKNOWN")
        return {"status": "NO_CHARGE", "amount": "0.00", "currency": "INR"}
    if not (payment and payment.status == Payment.Status.PAID and payment.provider == "WALLET"
            and payment.currency == "INR" and not payment.gateway_order_id and not payment.gateway_payment_id
            and payment.amount == finance.amount_charged and finance.payment_id == payment.pk
            and finance.payment_status == ConsultationFinance.PaymentStatus.SUCCESS
            and finance.billing_type == ConsultationFinance.BillingType.PAID):
        return review("UNVERIFIED_OR_MIXED_FUNDING")
    is_direct = consultation.consultation_type == Consultation.ConsultationType.DIRECT and consultation.tmc_id is None
    if is_direct:
        entry_model, account_model, account_field, debit_type = PatientWalletEntry, PatientWallet, "wallet", "DEBIT"
        owner_filter = {"wallet__patient_id": consultation.patient_id}
        if not finance.wallet_used or finance.source_type != "DIRECT_PATIENT" or finance.payer_entity != "PATIENT":
            return review("PAYER_MISMATCH")
    elif consultation.consultation_type == Consultation.ConsultationType.TMC and consultation.tmc_id:
        entry_model, account_model, account_field, debit_type = TMCAccountEntry, TMCAccount, "account", "CHARGE"
        owner_filter = {"account__tmc_id": consultation.tmc_id}
        if not finance.tmc_billed or finance.source_type != "TMC" or finance.payer_entity != "TMC":
            return review("PAYER_MISMATCH")
    else:
        return review("PAYER_MISMATCH")
    debits = list(entry_model.objects.select_for_update().filter(consultation=consultation, entry_type=debit_type))
    if len(debits) != 1 or not entry_model.objects.filter(pk=debits[0].pk, **owner_filter).exists():
        return review("ORIGINAL_DEBIT_NOT_UNIQUE")
    debit = debits[0]
    if debit.amount <= 0 or debit.amount != finance.amount_charged:
        return review("DEBIT_AMOUNT_MISMATCH")
    if (PatientWalletEntry.objects.filter(consultation=consultation, entry_type="REFUND").exists()
            or TMCAccountEntry.objects.filter(consultation=consultation, entry_type="REFUND").exists()):
        return review("EXISTING_RETURN_NEEDS_RECONCILIATION")
    platform_entries = list(AdminPlatformEntry.objects.filter(consultation=consultation, entry_type="PLATFORM_FEE"))
    fee = Decimal(finance.platform_fee)
    if fee < 0 or (fee == 0 and platform_entries) or (fee > 0 and (len(platform_entries) != 1 or platform_entries[0].amount != fee)):
        return review("PLATFORM_FEE_EVIDENCE_MISMATCH")
    if AdminPlatformEntry.objects.filter(consultation=consultation, entry_type="ADJUSTMENT").exists():
        return review("EXISTING_PLATFORM_ADJUSTMENT")
    account = account_model.objects.select_for_update().get(pk=getattr(debit, f"{account_field}_id"))
    amount = Decimal(debit.amount)
    account.balance += amount
    account.total_credited += amount
    account.save(update_fields=["balance", "total_credited", "updated_at"])
    entry = entry_model.objects.create(**{account_field: account}, entry_type="REFUND", amount=amount,
        balance_after=account.balance, consultation=consultation,
        description=f"Pre-start return of {entry_model.__name__} #{debit.pk}; actor #{actor.pk if actor else 'system'}")
    result = {"status": "RETURNED", "amount": str(amount), "currency": "INR",
        "destination": "patient wallet" if is_direct else "TMC wallet",
        "reference": f"{'PWR' if is_direct else 'TWR'}-{entry.pk}",
        "original_entry_id": debit.pk, "return_entry_id": entry.pk}
    if fee > 0:
        original = platform_entries[0]
        platform = AdminPlatformAccount.objects.select_for_update().get(pk=original.account_id)
        platform.balance -= fee
        platform.total_debited += fee
        platform.save(update_fields=["balance", "total_debited", "updated_at"])
        reversal = AdminPlatformEntry.objects.create(account=platform, entry_type="ADJUSTMENT", amount=fee,
            balance_after=platform.balance, consultation=consultation,
            description=f"Debit reversal of platform fee entry #{original.pk}; wallet return {result['reference']}")
        result.update(platform_original_entry_id=original.pk, platform_return_entry_id=reversal.pk)
    finance.payment_status = ConsultationFinance.PaymentStatus.REFUNDED
    finance.doctor_earning_status = ConsultationFinance.DoctorEarningStatus.NOT_APPLICABLE
    finance.notes = f"{finance.notes or ''}\nFull pre-start wallet return {result['reference']}; original charge retained."
    finance.save(update_fields=["payment_status", "doctor_earning_status", "notes", "updated_at"])
    return result
