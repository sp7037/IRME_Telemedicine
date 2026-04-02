from decimal import Decimal

from django.db import transaction
from django.db.models import F

from .models import (
    Consultation,
    ConsultationFinance,
    DoctorEarning,
    PatientWallet,
    PatientWalletEntry,
    TMCAccount,
    TMCAccountEntry,
)


def _resolve_source_type(consultation):
    if consultation.consultation_type == Consultation.ConsultationType.TMC:
        return ConsultationFinance.SourceType.TMC
    return ConsultationFinance.SourceType.DIRECT_PATIENT


@transaction.atomic
def create_consultation_finance(consultation, payment=None, amount=None):
    amount = Decimal(str(amount or "0"))
    source_type = _resolve_source_type(consultation)
    is_paid = amount > 0 and not consultation.is_free

    billing_type = ConsultationFinance.BillingType.PAID if is_paid else ConsultationFinance.BillingType.FREE
    payer_entity = ConsultationFinance.PayerEntity.NONE
    payment_status = ConsultationFinance.PaymentStatus.NOT_REQUIRED
    wallet_used = False
    tmc_billed = False

    if billing_type == ConsultationFinance.BillingType.PAID:
        payment_status = ConsultationFinance.PaymentStatus.SUCCESS
        if source_type == ConsultationFinance.SourceType.DIRECT_PATIENT:
            payer_entity = ConsultationFinance.PayerEntity.PATIENT
            wallet = PatientWallet.objects.select_for_update().get_or_create(
                patient=consultation.patient
            )[0]
            wallet.balance = Decimal(wallet.balance) - amount
            wallet.total_debited = Decimal(wallet.total_debited) + amount
            wallet.save(update_fields=["balance", "total_debited", "updated_at"])
            PatientWalletEntry.objects.create(
                wallet=wallet,
                entry_type=PatientWalletEntry.EntryType.DEBIT,
                amount=amount,
                balance_after=wallet.balance,
                consultation=consultation,
                description="Consultation charge",
            )
            wallet_used = True
        else:
            payer_entity = ConsultationFinance.PayerEntity.TMC
            account = TMCAccount.objects.select_for_update().get_or_create(
                tmc=consultation.tmc
            )[0]
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
                description="TMC consultation charge",
            )
            tmc_billed = True
    else:
        if source_type == ConsultationFinance.SourceType.DIRECT_PATIENT:
            wallet = PatientWallet.objects.select_for_update().get_or_create(
                patient=consultation.patient
            )[0]
            PatientWalletEntry.objects.create(
                wallet=wallet,
                entry_type=PatientWalletEntry.EntryType.FREE_RECORD,
                amount=Decimal("0.00"),
                balance_after=wallet.balance,
                consultation=consultation,
                description="Free consultation record",
            )
            payer_entity = ConsultationFinance.PayerEntity.NONE
        else:
            account = TMCAccount.objects.select_for_update().get_or_create(
                tmc=consultation.tmc
            )[0]
            TMCAccountEntry.objects.create(
                account=account,
                entry_type=TMCAccountEntry.EntryType.FREE_RECORD,
                amount=Decimal("0.00"),
                balance_after=account.balance,
                consultation=consultation,
                description="Free TMC consultation record",
            )
            payer_entity = ConsultationFinance.PayerEntity.TMC
            tmc_billed = True

    finance, _ = ConsultationFinance.objects.update_or_create(
        consultation=consultation,
        defaults={
            "source_type": source_type,
            "billing_type": billing_type,
            "payer_entity": payer_entity,
            "payment_status": payment_status,
            "doctor_earning_status": ConsultationFinance.DoctorEarningStatus.PENDING
            if billing_type == ConsultationFinance.BillingType.PAID
            else ConsultationFinance.DoctorEarningStatus.NOT_APPLICABLE,
            "amount_charged": amount,
            "wallet_used": wallet_used,
            "tmc_billed": tmc_billed,
            "payment": payment,
        },
    )
    return finance


@transaction.atomic
def ensure_doctor_earning_for_completion(consultation):
    finance = getattr(consultation, "finance", None)
    if not finance:
        return None

    if finance.billing_type == ConsultationFinance.BillingType.FREE:
        earning_amount = Decimal("0.00")
        status = DoctorEarning.Status.NOT_APPLICABLE
        finance_status = ConsultationFinance.DoctorEarningStatus.NOT_APPLICABLE
    else:
        earning_amount = Decimal(finance.amount_charged)
        status = DoctorEarning.Status.EARNED
        finance_status = ConsultationFinance.DoctorEarningStatus.EARNED

    earning, _ = DoctorEarning.objects.update_or_create(
        consultation=consultation,
        defaults={
            "doctor": consultation.doctor,
            "source_type": finance.source_type,
            "billing_type": finance.billing_type,
            "gross_amount": finance.amount_charged,
            "earning_amount": earning_amount,
            "status": status,
        },
    )
    finance.doctor_earning_status = finance_status
    finance.save(update_fields=["doctor_earning_status", "updated_at"])
    return earning


@transaction.atomic
def patient_wallet_topup(patient_profile, amount, description="Wallet top-up"):
    amount = Decimal(str(amount))
    wallet, _ = PatientWallet.objects.select_for_update().get_or_create(patient=patient_profile)
    wallet.balance = Decimal(wallet.balance) + amount
    wallet.total_credited = Decimal(wallet.total_credited) + amount
    wallet.save(update_fields=["balance", "total_credited", "updated_at"])
    return PatientWalletEntry.objects.create(
        wallet=wallet,
        entry_type=PatientWalletEntry.EntryType.CREDIT,
        amount=amount,
        balance_after=wallet.balance,
        description=description,
    )
