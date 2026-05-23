import hmac
import hashlib
import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import base64
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    AdminPlatformAccount,
    AdminPlatformEntry,
    Consultation,
    ConsultationFinance,
    ConsultationFeeSetting,
    DoctorEarning,
    PatientWallet,
    PatientWalletEntry,
    PatientWalletRechargeRequest,
    Payment,
    TMCAccount,
    TMCAccountEntry,
    TMCRechargeRequest,
)


class InsufficientBalanceError(ValueError):
    pass


def _create_razorpay_order(amount, currency, receipt, notes):
    amount_paise = int(normalize_money(amount) * 100)
    gateway_payload = {
        "amount_paise": amount_paise,
        "currency": currency or "INR",
        "configured": settings.RAZORPAY_ENABLED,
    }
    if not settings.RAZORPAY_ENABLED:
        gateway_payload["id"] = f"order_dev_{uuid.uuid4().hex[:18]}"
        return gateway_payload["id"], gateway_payload

    auth = base64.b64encode(
        f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode("utf-8")
    ).decode("ascii")
    payload = {
        "amount": amount_paise,
        "currency": currency or "INR",
        "receipt": receipt[:40],
        "notes": notes,
    }
    req = Request(
        "https://api.razorpay.com/v1/orders",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=20) as response:
            gateway_payload["razorpay_order"] = json.loads(response.read().decode("utf-8") or "{}")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Razorpay order creation failed ({exc.code}): {detail}") from exc
    except URLError as exc:
        raise ValueError(f"Razorpay order creation failed: {exc.reason}") from exc
    order_id = gateway_payload["razorpay_order"].get("id")
    if not order_id:
        raise ValueError("Razorpay did not return an order id.")
    return order_id, gateway_payload


def normalize_money(amount):
    return Decimal(str(amount or "0")).quantize(Decimal("0.01"))


def normalize_percentage(value):
    percentage = Decimal(str(value or "0"))
    if percentage < 0:
        return Decimal("0.00")
    if percentage > 100:
        return Decimal("100.00")
    return percentage.quantize(Decimal("0.01"))


def _resolve_source_type(consultation):
    if consultation.consultation_type == Consultation.ConsultationType.TMC:
        return ConsultationFinance.SourceType.TMC
    return ConsultationFinance.SourceType.DIRECT_PATIENT


def get_default_consultation_amount(consultation_type):
    setting = ConsultationFeeSetting.active()
    if consultation_type == Consultation.ConsultationType.TMC:
        return normalize_money(setting.tmc_consultation_fee)
    return normalize_money(setting.direct_patient_fee)


def resolve_consultation_amount(consultation_type, amount=None):
    amount = normalize_money(amount)
    if amount > 0:
        return amount
    return get_default_consultation_amount(consultation_type)


def resolve_doctor_consultation_amount(consultation_type, doctor=None, amount=None):
    amount = normalize_money(amount)
    if amount > 0:
        return amount
    doctor_fee = normalize_money(getattr(doctor, "consultation_fee", None))
    if doctor_fee > 0:
        return doctor_fee
    return get_default_consultation_amount(consultation_type)


def get_platform_fee_percentage():
    return normalize_percentage(ConsultationFeeSetting.active().platform_fee_percentage)


def calculate_percentage_amount(amount, percentage):
    amount = normalize_money(amount)
    percentage = normalize_percentage(percentage)
    return (amount * percentage / Decimal("100")).quantize(Decimal("0.01"))


def calculate_platform_fee(doctor_fee):
    return calculate_percentage_amount(doctor_fee, get_platform_fee_percentage())


def estimate_tmc_consultation_pricing(tmc, doctor_fee, is_free=None):
    doctor_fee = normalize_money(doctor_fee)
    platform_fee = calculate_platform_fee(doctor_fee)
    is_free = tmc.free_consultations_remaining > 0 if is_free is None else bool(is_free)
    if is_free:
        return {
            "billing_type": ConsultationFinance.BillingType.FREE,
            "doctor_fee": doctor_fee,
            "platform_fee": Decimal("0.00"),
            "discount_amount": Decimal("0.00"),
            "admin_subsidy_amount": doctor_fee,
            "amount_charged": Decimal("0.00"),
            "discount_applied": False,
        }

    discount_applied = (
        tmc.discounted_consultations_remaining > 0
        and normalize_percentage(tmc.discount_percentage) > 0
    )
    discount_amount = calculate_percentage_amount(doctor_fee, tmc.discount_percentage) if discount_applied else Decimal("0.00")
    discounted_doctor_fee = max(doctor_fee - discount_amount, Decimal("0.00"))
    return {
        "billing_type": ConsultationFinance.BillingType.PAID,
        "doctor_fee": doctor_fee,
        "platform_fee": platform_fee,
        "discount_amount": discount_amount,
        "admin_subsidy_amount": discount_amount,
        "amount_charged": normalize_money(discounted_doctor_fee + platform_fee),
        "discount_applied": discount_applied,
    }


def get_admin_platform_account(lock=False):
    qs = AdminPlatformAccount.objects
    if lock:
        qs = qs.select_for_update()
    return qs.get_or_create(name="Platform Wallet")[0]


@transaction.atomic
def admin_platform_topup(amount, description="Admin platform wallet top-up"):
    amount = normalize_money(amount)
    if amount <= 0:
        raise ValueError("Top-up amount must be greater than zero.")
    account = get_admin_platform_account(lock=True)
    account.balance = Decimal(account.balance) + amount
    account.total_credited = Decimal(account.total_credited) + amount
    account.save(update_fields=["balance", "total_credited", "updated_at"])
    return AdminPlatformEntry.objects.create(
        account=account,
        entry_type=AdminPlatformEntry.EntryType.CREDIT,
        amount=amount,
        balance_after=account.balance,
        description=description,
    )


def _credit_platform_fee(consultation, amount):
    amount = normalize_money(amount)
    if amount <= 0:
        return None
    if AdminPlatformEntry.objects.filter(
        consultation=consultation,
        entry_type=AdminPlatformEntry.EntryType.PLATFORM_FEE,
    ).exists():
        return None
    account = get_admin_platform_account(lock=True)
    account.balance = Decimal(account.balance) + amount
    account.total_credited = Decimal(account.total_credited) + amount
    account.total_platform_fees = Decimal(account.total_platform_fees) + amount
    account.save(update_fields=["balance", "total_credited", "total_platform_fees", "updated_at"])
    return AdminPlatformEntry.objects.create(
        account=account,
        entry_type=AdminPlatformEntry.EntryType.PLATFORM_FEE,
        amount=amount,
        balance_after=account.balance,
        consultation=consultation,
        description="Platform fee earned on consultation",
    )


def _debit_admin_doctor_subsidy(consultation, amount):
    amount = normalize_money(amount)
    if amount <= 0:
        return None
    if AdminPlatformEntry.objects.filter(
        consultation=consultation,
        entry_type=AdminPlatformEntry.EntryType.DOCTOR_SUBSIDY,
    ).exists():
        return None
    account = get_admin_platform_account(lock=True)
    account.balance = Decimal(account.balance) - amount
    account.total_debited = Decimal(account.total_debited) + amount
    account.total_doctor_subsidies = Decimal(account.total_doctor_subsidies) + amount
    account.save(update_fields=["balance", "total_debited", "total_doctor_subsidies", "updated_at"])
    return AdminPlatformEntry.objects.create(
        account=account,
        entry_type=AdminPlatformEntry.EntryType.DOCTOR_SUBSIDY,
        amount=amount,
        balance_after=account.balance,
        consultation=consultation,
        description="Admin subsidy paid toward doctor earning",
    )


@transaction.atomic
def create_consultation_finance(consultation, payment=None, amount=None):
    """Idempotent per consultation: duplicate calls do not double-post ledger entries."""
    consultation = Consultation.objects.select_for_update().get(pk=consultation.pk)
    existing = ConsultationFinance.objects.filter(consultation_id=consultation.pk).first()
    if existing:
        return existing
    doctor_fee = resolve_consultation_amount(consultation.consultation_type, amount)
    source_type = _resolve_source_type(consultation)
    platform_fee = calculate_platform_fee(doctor_fee)
    discount_amount = Decimal("0.00")
    admin_subsidy_amount = Decimal("0.00")
    amount_charged = normalize_money(doctor_fee + platform_fee)
    discount_applied = False
    if source_type == ConsultationFinance.SourceType.TMC and consultation.tmc_id:
        pricing = estimate_tmc_consultation_pricing(
            consultation.tmc,
            doctor_fee,
            is_free=consultation.is_free,
        )
        platform_fee = pricing["platform_fee"]
        discount_amount = pricing["discount_amount"]
        admin_subsidy_amount = pricing["admin_subsidy_amount"]
        amount_charged = pricing["amount_charged"]
        discount_applied = pricing["discount_applied"]

    is_paid = amount_charged > 0 and not consultation.is_free

    billing_type = ConsultationFinance.BillingType.PAID if is_paid else ConsultationFinance.BillingType.FREE
    payer_entity = ConsultationFinance.PayerEntity.NONE
    payment_status = ConsultationFinance.PaymentStatus.NOT_REQUIRED
    wallet_used = False
    tmc_billed = False

    if billing_type == ConsultationFinance.BillingType.PAID:
        if source_type == ConsultationFinance.SourceType.DIRECT_PATIENT:
            payer_entity = ConsultationFinance.PayerEntity.PATIENT
            wallet = PatientWallet.objects.select_for_update().get_or_create(
                patient=consultation.patient
            )[0]
            if Decimal(wallet.balance) < amount_charged:
                raise InsufficientBalanceError(
                    f"Insufficient patient wallet balance. Required {amount_charged}, available {wallet.balance}."
                )
            wallet.balance = Decimal(wallet.balance) - amount_charged
            wallet.total_debited = Decimal(wallet.total_debited) + amount_charged
            wallet.save(update_fields=["balance", "total_debited", "updated_at"])
            PatientWalletEntry.objects.create(
                wallet=wallet,
                entry_type=PatientWalletEntry.EntryType.DEBIT,
                amount=amount_charged,
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
            if Decimal(account.balance) < amount_charged:
                raise InsufficientBalanceError(
                    f"Insufficient TMC wallet balance. Required {amount_charged}, available {account.balance}."
                )
            account.balance = Decimal(account.balance) - amount_charged
            account.total_charged = Decimal(account.total_charged) + amount_charged
            account.total_debited = Decimal(account.total_debited) + amount_charged
            account.save(update_fields=["balance", "total_charged", "total_debited", "updated_at"])
            TMCAccountEntry.objects.create(
                account=account,
                entry_type=TMCAccountEntry.EntryType.CHARGE,
                amount=amount_charged,
                balance_after=account.balance,
                consultation=consultation,
                description=(
                    f"TMC consultation charge: doctor fee {doctor_fee}, "
                    f"discount {discount_amount}, platform fee {platform_fee}"
                ),
            )
            tmc_billed = True
            if discount_applied:
                consultation.tmc.discounted_consultations_used += 1
                consultation.tmc.save(update_fields=["discounted_consultations_used"])

        payment_status = ConsultationFinance.PaymentStatus.SUCCESS
        if payment:
            payment.amount = amount_charged
            payment.status = Payment.Status.PAID
            payment.save(update_fields=["amount", "status", "updated_at"])
        _credit_platform_fee(consultation, platform_fee)
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
            payer_entity = ConsultationFinance.PayerEntity.ADMIN
            tmc_billed = True

    finance, _ = ConsultationFinance.objects.update_or_create(
        consultation=consultation,
        defaults={
            "source_type": source_type,
            "billing_type": billing_type,
            "payer_entity": payer_entity,
            "payment_status": payment_status,
            "doctor_earning_status": ConsultationFinance.DoctorEarningStatus.PENDING
            if doctor_fee > 0
            else ConsultationFinance.DoctorEarningStatus.NOT_APPLICABLE,
            "amount_charged": amount_charged,
            "doctor_fee": doctor_fee,
            "platform_fee": platform_fee,
            "discount_amount": discount_amount,
            "admin_subsidy_amount": admin_subsidy_amount,
            "wallet_used": wallet_used,
            "tmc_billed": tmc_billed,
            "payment": payment,
            "notes": (
                f"doctor_fee={doctor_fee}; platform_fee={platform_fee}; "
                f"discount={discount_amount}; admin_subsidy={admin_subsidy_amount}"
            ),
        },
    )
    return finance


@transaction.atomic
def ensure_doctor_earning_for_completion(consultation):
    finance = getattr(consultation, "finance", None)
    if not finance:
        return None

    earning_amount = normalize_money(finance.doctor_fee or finance.amount_charged)
    status = DoctorEarning.Status.EARNED if earning_amount > 0 else DoctorEarning.Status.NOT_APPLICABLE
    finance_status = (
        ConsultationFinance.DoctorEarningStatus.EARNED
        if earning_amount > 0
        else ConsultationFinance.DoctorEarningStatus.NOT_APPLICABLE
    )
    _debit_admin_doctor_subsidy(consultation, finance.admin_subsidy_amount)

    earning, _ = DoctorEarning.objects.update_or_create(
        consultation=consultation,
        defaults={
            "doctor": consultation.doctor,
            "source_type": finance.source_type,
            "billing_type": finance.billing_type,
            "gross_amount": finance.doctor_fee or finance.amount_charged,
            "earning_amount": earning_amount,
            "status": status,
        },
    )
    finance.doctor_earning_status = finance_status
    finance.save(update_fields=["doctor_earning_status", "updated_at"])
    return earning


@transaction.atomic
def patient_wallet_topup(patient_profile, amount, description="Wallet top-up"):
    amount = normalize_money(amount)
    if amount <= 0:
        raise ValueError("Top-up amount must be greater than zero.")
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


@transaction.atomic
def create_patient_recharge_request(patient_profile, amount, requested_by=None, reference_note=None):
    amount = normalize_money(amount)
    if amount <= 0:
        raise ValueError("Recharge amount must be greater than zero.")
    return PatientWalletRechargeRequest.objects.create(
        patient=patient_profile,
        amount=amount,
        requested_by=requested_by,
        reference_note=reference_note,
    )


@transaction.atomic
def process_patient_recharge_request(recharge_request, approve, processed_by=None, admin_note=None):
    recharge = PatientWalletRechargeRequest.objects.select_for_update().get(pk=recharge_request.pk)
    if recharge.status != PatientWalletRechargeRequest.Status.PENDING:
        raise ValueError("Recharge request has already been processed.")
    recharge.processed_by = processed_by
    recharge.processed_at = timezone.now()
    recharge.admin_note = admin_note
    if approve:
        entry = patient_wallet_topup(
            recharge.patient,
            recharge.amount,
            description=f"Approved recharge request #{recharge.id}",
        )
        recharge.status = PatientWalletRechargeRequest.Status.APPROVED
        recharge.save(update_fields=["status", "processed_by", "processed_at", "admin_note", "updated_at"])
        return recharge, entry
    recharge.status = PatientWalletRechargeRequest.Status.REJECTED
    recharge.save(update_fields=["status", "processed_by", "processed_at", "admin_note", "updated_at"])
    return recharge, None


@transaction.atomic
def reconcile_approved_patient_recharges(patient_profile):
    """
    Credit approved patient recharge requests that were marked approved outside
    the processing endpoint, for example by direct Django admin status edits.
    """
    created_entries = []
    approved = PatientWalletRechargeRequest.objects.select_for_update().filter(
        patient=patient_profile,
        status=PatientWalletRechargeRequest.Status.APPROVED,
    )
    wallet, _ = PatientWallet.objects.select_for_update().get_or_create(patient=patient_profile)
    for recharge in approved:
        description = f"Approved recharge request #{recharge.id}"
        if PatientWalletEntry.objects.filter(wallet=wallet, description=description).exists():
            continue
        entry = patient_wallet_topup(patient_profile, recharge.amount, description=description)
        created_entries.append(entry)
    return created_entries


@transaction.atomic
def create_patient_recharge_order_reference(recharge_request):
    recharge = PatientWalletRechargeRequest.objects.select_for_update().get(pk=recharge_request.pk)
    if recharge.status != PatientWalletRechargeRequest.Status.PENDING:
        raise ValueError("Recharge request has already been processed.")
    if not recharge.gateway_order_id:
        order_id, gateway_payload = _create_razorpay_order(
            recharge.amount,
            "INR",
            f"wallet_{recharge.patient_id}_{recharge.id}",
            {"wallet_recharge_id": str(recharge.id), "patient_id": str(recharge.patient_id)},
        )
        recharge.gateway_order_id = order_id.replace("order_dev_", "order_dev_wallet_", 1)
        recharge.provider = PatientWalletRechargeRequest.Provider.RAZORPAY
        recharge.gateway_payload = gateway_payload
        recharge.save(update_fields=["gateway_order_id", "provider", "gateway_payload", "updated_at"])
    return recharge


@transaction.atomic
def mark_patient_recharge_success(recharge_request, gateway_payment_id, gateway_signature, payload=None):
    recharge = PatientWalletRechargeRequest.objects.select_for_update().get(pk=recharge_request.pk)
    if recharge.status != PatientWalletRechargeRequest.Status.PENDING:
        raise ValueError("Recharge request has already been processed.")
    if not verify_razorpay_signature(recharge.gateway_order_id, gateway_payment_id, gateway_signature):
        raise ValueError("Invalid Razorpay signature.")
    recharge.provider = PatientWalletRechargeRequest.Provider.RAZORPAY
    recharge.gateway_payment_id = gateway_payment_id
    recharge.gateway_signature = gateway_signature
    recharge.gateway_payload = payload or {}
    recharge.status = PatientWalletRechargeRequest.Status.APPROVED
    recharge.processed_at = timezone.now()
    recharge.save(
        update_fields=[
            "provider",
            "gateway_payment_id",
            "gateway_signature",
            "gateway_payload",
            "status",
            "processed_at",
            "updated_at",
        ]
    )
    entry = patient_wallet_topup(
        recharge.patient,
        recharge.amount,
        description=f"Razorpay wallet recharge #{recharge.id}",
    )
    return recharge, entry


@transaction.atomic
def cancel_patient_recharge_request(recharge_request, note="Razorpay checkout was closed before payment."):
    recharge = PatientWalletRechargeRequest.objects.select_for_update().get(pk=recharge_request.pk)
    if recharge.status != PatientWalletRechargeRequest.Status.PENDING:
        return recharge
    recharge.status = PatientWalletRechargeRequest.Status.CANCELED
    recharge.processed_at = timezone.now()
    recharge.admin_note = note
    recharge.save(update_fields=["status", "processed_at", "admin_note", "updated_at"])
    return recharge


@transaction.atomic
def tmc_account_topup(tmc_profile, amount, description="TMC wallet recharge"):
    amount = normalize_money(amount)
    if amount <= 0:
        raise ValueError("Recharge amount must be greater than zero.")
    account, _ = TMCAccount.objects.select_for_update().get_or_create(tmc=tmc_profile)
    account.balance = Decimal(account.balance) + amount
    account.total_credited = Decimal(account.total_credited) + amount
    account.save(update_fields=["balance", "total_credited", "updated_at"])
    return TMCAccountEntry.objects.create(
        account=account,
        entry_type=TMCAccountEntry.EntryType.CREDIT,
        amount=amount,
        balance_after=account.balance,
        description=description,
    )


@transaction.atomic
def create_tmc_recharge_request(tmc_profile, amount, requested_by=None, reference_note=None):
    amount = normalize_money(amount)
    if amount <= 0:
        raise ValueError("Recharge amount must be greater than zero.")
    return TMCRechargeRequest.objects.create(
        tmc=tmc_profile,
        amount=amount,
        requested_by=requested_by,
        reference_note=reference_note,
    )


@transaction.atomic
def create_tmc_recharge_order_reference(recharge_request):
    recharge = TMCRechargeRequest.objects.select_for_update().get(pk=recharge_request.pk)
    if recharge.status != TMCRechargeRequest.Status.PENDING:
        raise ValueError("Recharge request has already been processed.")
    if not recharge.gateway_order_id:
        order_id, gateway_payload = _create_razorpay_order(
            recharge.amount,
            "INR",
            f"tmc_{recharge.tmc_id}_{recharge.id}",
            {"tmc_recharge_id": str(recharge.id), "tmc_id": str(recharge.tmc_id)},
        )
        recharge.gateway_order_id = order_id.replace("order_dev_", "order_dev_tmc_", 1)
        recharge.provider = TMCRechargeRequest.Provider.RAZORPAY
        recharge.gateway_payload = gateway_payload
        recharge.save(update_fields=["gateway_order_id", "provider", "gateway_payload", "updated_at"])
    return recharge


@transaction.atomic
def mark_tmc_recharge_success(recharge_request, gateway_payment_id, gateway_signature, payload=None):
    recharge = TMCRechargeRequest.objects.select_for_update().get(pk=recharge_request.pk)
    if recharge.status != TMCRechargeRequest.Status.PENDING:
        raise ValueError("Recharge request has already been processed.")
    if not verify_razorpay_signature(recharge.gateway_order_id, gateway_payment_id, gateway_signature):
        raise ValueError("Invalid Razorpay signature.")
    recharge.provider = TMCRechargeRequest.Provider.RAZORPAY
    recharge.gateway_payment_id = gateway_payment_id
    recharge.gateway_signature = gateway_signature
    recharge.gateway_payload = payload or {}
    recharge.status = TMCRechargeRequest.Status.APPROVED
    recharge.processed_at = timezone.now()
    recharge.save(
        update_fields=[
            "provider",
            "gateway_payment_id",
            "gateway_signature",
            "gateway_payload",
            "status",
            "processed_at",
            "updated_at",
        ]
    )
    entry = tmc_account_topup(
        recharge.tmc,
        recharge.amount,
        description=f"Razorpay TMC wallet recharge #{recharge.id}",
    )
    return recharge, entry


@transaction.atomic
def cancel_tmc_recharge_request(recharge_request, note="Razorpay checkout was closed before payment."):
    recharge = TMCRechargeRequest.objects.select_for_update().get(pk=recharge_request.pk)
    if recharge.status != TMCRechargeRequest.Status.PENDING:
        return recharge
    recharge.status = TMCRechargeRequest.Status.CANCELED
    recharge.processed_at = timezone.now()
    recharge.admin_note = note
    recharge.save(update_fields=["status", "processed_at", "admin_note", "updated_at"])
    return recharge


@transaction.atomic
def process_tmc_recharge_request(recharge_request, approve, processed_by=None, admin_note=None):
    recharge = TMCRechargeRequest.objects.select_for_update().get(pk=recharge_request.pk)
    if recharge.status != TMCRechargeRequest.Status.PENDING:
        raise ValueError("Recharge request has already been processed.")
    recharge.processed_by = processed_by
    recharge.processed_at = timezone.now()
    recharge.admin_note = admin_note
    if approve:
        entry = tmc_account_topup(
            recharge.tmc,
            recharge.amount,
            description=f"Approved recharge request #{recharge.id}",
        )
        recharge.status = TMCRechargeRequest.Status.APPROVED
        recharge.save(update_fields=["status", "processed_by", "processed_at", "admin_note", "updated_at"])
        return recharge, entry
    recharge.status = TMCRechargeRequest.Status.REJECTED
    recharge.save(update_fields=["status", "processed_by", "processed_at", "admin_note", "updated_at"])
    return recharge, None


@transaction.atomic
def reconcile_approved_tmc_recharges(tmc_profile):
    """
    Credit approved TMC recharge requests that were marked approved outside the
    processing endpoint, for example by direct Django admin status edits.
    """
    created_entries = []
    approved = TMCRechargeRequest.objects.select_for_update().filter(
        tmc=tmc_profile,
        status=TMCRechargeRequest.Status.APPROVED,
    )
    account, _ = TMCAccount.objects.select_for_update().get_or_create(tmc=tmc_profile)
    for recharge in approved:
        description = f"Approved recharge request #{recharge.id}"
        if TMCAccountEntry.objects.filter(account=account, description=description).exists():
            continue
        entry = tmc_account_topup(tmc_profile, recharge.amount, description=description)
        created_entries.append(entry)
    return created_entries


def create_razorpay_order_reference(payment):
    """
    Razorpay-ready order preparation.

    If keys are not configured yet, this still stores a deterministic internal
    order reference so frontend/payment wiring can be developed safely.
    """
    if not payment.gateway_order_id:
        order_id, gateway_payload = _create_razorpay_order(
            payment.amount,
            payment.currency,
            f"consult_{payment.consultation_id}_{payment.id}",
            {"consultation_id": str(payment.consultation_id), "payment_id": str(payment.id)},
        )
        payment.gateway_order_id = order_id
        payment.provider = "RAZORPAY"
        payment.gateway_payload = gateway_payload
        payment.save(update_fields=["gateway_order_id", "provider", "gateway_payload", "updated_at"])
    return payment


def verify_razorpay_signature(order_id, payment_id, signature):
    if not settings.RAZORPAY_KEY_SECRET:
        return False
    payload = f"{order_id}|{payment_id}".encode("utf-8")
    digest = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature or "")


@transaction.atomic
def mark_razorpay_payment_success(payment, gateway_payment_id, gateway_signature, payload=None):
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if not verify_razorpay_signature(payment.gateway_order_id, gateway_payment_id, gateway_signature):
        raise ValueError("Invalid Razorpay signature.")
    payment.provider = "RAZORPAY"
    payment.gateway_payment_id = gateway_payment_id
    payment.gateway_signature = gateway_signature
    payment.gateway_payload = payload or {}
    payment.status = Payment.Status.PAID
    payment.save(
        update_fields=[
            "provider",
            "gateway_payment_id",
            "gateway_signature",
            "gateway_payload",
            "status",
            "updated_at",
        ]
    )
    finance = ConsultationFinance.objects.filter(payment=payment).first()
    if finance:
        finance.payment_status = ConsultationFinance.PaymentStatus.SUCCESS
        finance.save(update_fields=["payment_status", "updated_at"])
    return payment
