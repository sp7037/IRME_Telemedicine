# Postponement rejection: notifications and verified wallet returns

Date: 2026-11-21. This is a narrow legacy-flow correction under [ADR 0007](adr/0007-verified-prestart-wallet-returns.md), not the new journal/refund/quota engine.

## User-visible outcome

- Rejecting the proposed time closes that request and explains that the patient can choose another doctor or request this doctor again when available. Existing same-doctor cooldown and availability checks still apply.
- The patient sees the confirmed return amount, original-payer destination and return reference, or an explicit administrator-review message when the outcome is uncertain. History retains the rejected request.
- The doctor sees that the patient declined the time and the request is closed. Polling compares full history, not just the disappearing pending-request list.
- A persistent outcome panel appears on both dashboards. Existing status notices are fixed in the viewport below the header, so they do not require scrolling to the page top. Financial messages never infer a refund from a status change alone.
- Accepting a proposed time retains the original debit; it does not charge again. Patient response decisions now lock the consultation for the entire transaction, preventing stale accept/reject requests from partially updating its schedule.

## Financial boundary

Automatic legacy wallet returns are limited to terminal rejection/cancellation from PENDING or POSTPONED with a recorded booking request, recorded pre-start postponement when applicable, and no contradictory start/completion/chat/prescription/earning evidence. ACCEPTED/QUEUED or uncertain legacy cases take review rather than treating absence of a start event as proof.

For a positive charge, require one matching original debit, original owner, matching successful wallet Payment/finance amount, INR currency and validated platform-fee evidence. Provider/mixed payments, duplicate or changed debits, earlier refunds, existing adjustments and insufficient provenance are review cases. Do not manufacture a wallet destination or perform a provider refund.

Return the full original debit, including its platform charge, to the original patient wallet or TMC account. TMC discounts are not paid again and the patient receives no platform credit for TMC cash collection. The INR 100 new-booking threshold does not block returning funds. Current prices do not recalculate the return.

Create an existing-type REFUND entry and a debit ADJUSTMENT reversing the original platform-fee credit, with structured original/reversal IDs in the terminal event metadata and human-readable references in entry descriptions. Preserve original Payment PAID status, original charge/debit and gross counters as historical evidence; mark ConsultationFinance REFUNDED and unperformed doctor earning NOT_APPLICABLE. Credit/refund and platform debit counters record the new movements without erasing old ones. Platform fee totals remain historical gross; the linked adjustment supplies the reversal. The platform's internal balance may become negative after a reversal; it is not a bank balance or permission to withhold a verified wallet return.

All effects and the terminal status/event commit together. Lock order: consultation, payment, finance, original debit, payer wallet, platform account. Repeated/concurrent patient rejection returns the existing outcome without a second credit. A failed posting rolls back the rejection and all postings. Late payment verification cannot overwrite REFUNDED finance, and refunded consultation order/verify endpoints are denied.

Free direct cases create no cash refund. Legacy free TMC/monthly periods and lifetime discount/free counters are not reset here: their period/restoration semantics cannot be reconstructed reliably. They receive an explicit review outcome. No new free entitlement, monthly allocation or quota reversal is claimed.

## Evidence and permissions

The canonical transition service is the only new live return caller, after existing participant/doctor permissions. There is no self-credit or generic refund HTTP endpoint. Public role-scoped consultation history adds `wallet_return` with only status, confirmed amount, currency, destination and reference. Internal original-entry IDs/reason codes remain in event metadata/admin evidence.

This implementation uses existing consultation/entry foreign keys, REFUND/ADJUSTMENT entry types and structured event links; it adds no table, column or migration. It does not provide database-enforced reversal uniqueness/immutability against privileged SQL. The new journal/posting work must replace this legacy adapter with protected unique references and cover it in the writer inventory before activation.

## Historical maintenance

Individual review/correction evidence is held privately. This release authorises no additional historical refunds or mass backfill. Preserve original and linked return references.

## Verification and recovery

The pre-deployment 126-test backend suite and 11 frontend tests passed on isolated PostgreSQL and synthetic data. Current release verification is recorded separately. Private recovery copies contain operational evidence and must never be uploaded to Git. Provider refunds, monthly quota restoration and the new journal remain separate.
