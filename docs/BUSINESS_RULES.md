# Consultation business rules

Recorded: 2026-11-20. Source: owner instructions in this chat, including two explicit clarifications. This document specifies intended behaviour, not current implementation completeness.

Phase 2A update: the owner confirmed the core monthly quota and cancellation/refund rules on 2026-11-20. [ADR 0002](adr/0002-monthly-quota-and-refund-policy.md) records their exact scope, exceptions and implementation safeguards. Application behaviour has not yet changed.

Phase 2B design is available in [ADR 0003](adr/0003-financial-schema-and-compatibility.md), [schema specification](FINANCIAL_SCHEMA_DESIGN.md) and [compatibility/rollout specification](FINANCIAL_COMPATIBILITY_ROLLOUT.md). Technical proposals there do not resolve unanswered commercial policies, change historical transactions or implement these rules.

## 1. Separate prices and obligations

| Concept | Meaning |
| --- | --- |
| Reference consultation fee | Admin-approved customer-facing consultation fee used as the discount / percentage basis. |
| TMC discount benefit | Flat amount or percentage of the reference fee, set by admin. This is the TMC earning opportunity through its own collection. |
| TMC wallet charge | The amount the platform deducts for this consultation. May be full price, discounted, or zero. |
| Direct patient charge | Amount paid by a direct patient to the platform; no TMC participates. |
| Doctor payable | Independent amount owed by the platform to the doctor for eligible completed work. |
| Platform consultation contribution | Platform consultation revenue less doctor payable, before gateway fees and other costs; can be negative for subsidised work. Not a bank or wallet balance. |

Do not use one ambiguous `doctor_fee` field for the reference fee and doctor payable. UI labels, APIs, reports, and ledger descriptions must preserve this distinction.

## 2. TMC-assisted consultations (confirmed)

- The TMC collects from its patient separately. The platform must not claim that collection occurred unless explicitly recorded with a source/reference.
- For reference fee INR 100 and TMC discount INR 30, deduct INR 70 from the TMC wallet. Record INR 30 as the discount benefit, not another amount payable by the platform to the TMC.
- Support an admin-set percentage or flat discount. A 30% discount on INR 100 also produces INR 70 charge. Flat and percentage rules must have explicit modes; do not apply both accidentally.
- Admin may charge the TMC INR 100, INR 50, or zero independently of the doctor's payable. An explicit TMC price override can be designed if discount mode alone cannot express an authorised policy; precedence must be unambiguous.
- Optional monthly free consultation allowances are set by admin per TMC and can be zero, one, or more. New TMCs do not receive an automatic allowance.
- A free-quota consultation has zero wallet charge, with a referenced quota allocation/reservation/consumption record. Doctor payable remains independently configured.
- Check available TMC wallet balance >= INR 100 before every booking, paid or free. For paid work also require balance >= charge: required pre-booking balance is `max(100, charge)`.
- The INR 100 threshold is an eligibility check, not a minimum ending balance, fee, or frozen deposit. A balance of INR 100 can become INR 30 after an INR 70 booking.
- With INR 99.99 balance, reject even a free consultation; show the required balance and an Add Funds action. With INR 100 and charge INR 150, reject for insufficient charge coverage.
- Add Funds must expose existing supported funding mechanisms, pending/failed/success status, and references. Credit only on authorised verified confirmation, once.
- Check wallet eligibility, reserve quota, and create/post the booking in one transaction with appropriate locks. Two simultaneous requests cannot overspend or consume the same free slot.

## 3. Doctor payable and settlement (confirmed direction)

- Admin sets the doctor's payout basis independently of TMC pricing: for example reference fee INR 100, doctor payable INR 50, while TMC charge is INR 100, INR 50, or zero.
- Support fixed payable or percentage deduction from the reference fee. For example INR 100 with 20% platform retention gives INR 80 doctor payable; 50% gives INR 50. Document whether a configured flat deduction is also required before exposing that mode.
- Doctor payable accrues on eligible consultation completion, including free TMC consultations. Pending/booked work is not yet settled or earned.
- Admin settles weekly or monthly according to configured doctor terms. The first implementation should support recorded, referenced manual payouts; automated bank disbursement is separate scope.
- Settlement needs a batch, covered consultations, allocations, totals, status, actor, timestamps, and external payment reference. Never equate a button press or scheduled date with confirmed payment.
- Track accrued, unsettled, allocated, and paid amounts separately. Repeated completion or settlement requests cannot create duplicate earnings or payment allocations.

## 4. Direct patient consultations (confirmed)

- Source is DIRECT, with no TMC attached to that consultation.
- Patient pays the platform; the platform owes the configured doctor payable after eligible completion.
- Reference/direct price INR 100 and doctor payable INR 80 means INR 20 consultation contribution before costs. It does not mean charge INR 120.
- Owner confirmed on 2026-11-21: direct patients should review/pay per consultation before booking, without a separately prefunded wallet as the primary flow. Preserve legacy balances/history during transition. [ADR 0006](adr/0006-direct-patient-checkout-direction.md) records this direction; true gateway-to-booking checkout remains to be implemented, while current wallet preflight/local testing is a compatibility step.
- A patient record originally created by a TMC does not automatically make every later consultation TMC sourced. Determine authorisation and source explicitly per booking.

## 5. Immutable financial evidence

Implemented admin/API maintenance boundary (2026-11-20): [ADR 0004](adr/0004-financial-admin-boundaries.md) makes existing financial admin records view-only, prevents admin deletion through owners, protects usage counters and maps staff financial writes to explicit model permissions. Actual business transitions still use the existing services. This does not implement the proposed journal, database immutability or new payout/refund rules.

At booking, store a server-generated pricing snapshot: consultation reference, doctor, patient, optional TMC, source, currency, reference fee, patient/TMC charge, discount mode/value/amount, free reason, quota period/reference, doctor payable mode/value/amount, policy identifiers/versions, and effective time.

Every money movement needs an immutable unique reference, actor/system source, timestamp, amount, account, transaction type, consultation/funding/payout/refund link as applicable, and reversal/original link. Wallet entries include balance after posting. A funding request can exist without a consultation; a settlement covers multiple referenced consultations.

Use balanced journal transactions for new financial flows, with clear account mapping and transaction boundaries. Wallet funds are liabilities/prepayments until consumed, not immediate consultation revenue. Doctor earnings are payables until settled. Do not count wallet recharge and subsequent wallet consumption twice as revenue. Gateway fees and cash settlement reconciliation remain separate from consultation contribution.

Retain legacy entries as legacy evidence. Do not manufacture historical policy versions or doctor payable values from current settings. Reconciliation and an explicit migration policy must precede a ledger switch.

## 6. Financial examples

All amounts INR. TMC examples assume separately collected reference price 100 for illustration, not evidence of actual patient collection. Contribution is charge minus doctor payable before other costs.

| Case | Reference | TMC charge | Direct charge | TMC discount benefit | Doctor payable | Platform contribution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TMC full price | 100 | 100 | — | 0 | 50 | 50 |
| TMC 30 flat / 30% discount | 100 | 70 | — | 30 | 50 | 20 |
| TMC 50 discount | 100 | 50 | — | 50 | 50 | 0 |
| TMC monthly free allowance | 100 | 0 | — | Report free benefit separately | 50 | -50 |
| Direct, 20% platform retention | 100 | — | 100 | — | 80 | 20 |
| Direct, fixed doctor payable 50 | 100 | — | 100 | — | 50 | 50 |

Free benefits must not inflate earned/paid TMC commission totals. No extra platform fee is automatically added to these examples. Any future surcharge needs an explicit approved policy and customer disclosure.

## 7. Monthly reporting

Per TMC and reporting month: bookings, completed, pending, canceled/rejected, free reserved/consumed, paid consultations, actual charges, discounts, refunds, top-ups, opening/closing balance, and net wallet movements. Define separate booking-month, completion-month, and posting-month filters; never silently mix them.

Per doctor: completed consultations split by DIRECT/TMC and free/paid, accrued payables, reversals, unpaid balance, settlement allocations and actual paid references. Platform totals must reconcile to the ledger without counting wallet top-ups as consultation revenue.

Monthly allowance boundaries are confirmed as Indian calendar months (Asia/Kolkata) with UTC storage. Unused units expire without rollover; reserve at booking, consume on completion and restore eligible cancellations only to their original period. Releases into a closed month remain expired and do not increase a later allowance. Existing reservations remain linked to their original month when fulfilment occurs later. Reporting period semantics must be labelled explicitly; do not use a destructive reset of lifetime counters.

## 8. Policy decisions still required before affected implementation

Status is mixed: P01-P03 core policies below are now confirmed in ADR 0002; remaining items are proposals/questions. Resolve relevant open details before dependent implementation.

| ID | Decision required | Proposed starting point |
| --- | --- | --- |
| P01 | Core accepted; amendment details open | Asia/Kolkata calendar months, unused expiry/no rollover. Admin allocation remains explicit; mid-month amendments/generation need design. No automatic joining entitlement introduced. |
| P02 | Core accepted; implementation pending | Reserve at booking, consume on completion, release eligible cancellations/rejections once to original period; closed-period releases do not add current-month units. |
| P03 | Core accepted; start evidence/refund mechanics open | Full actual platform charge returned to original payer for eligible pre-start cancellations/rejections, with no doctor earning. No-shows, failures after start and completed disputes require admin evidence review and linked adjustments. |
| P04 | Discount scope, precedence and limits | Per-TMC default, optional doctor-specific override; flat OR percentage, never stacked; reject invalid amounts. |
| P05 | Admin-configurable wallet eligibility threshold | Initial business rule is INR 100; making it editable later requires an explicit audited policy decision. |
| P06 | Doctor payable on cancellations/no-shows, and payout calendar | Completion-only initially; confirm weekly/monthly cutoffs, timezone, and partial-settlement rules. |
| P07 | Direct checkout direction accepted; mechanics/follow-ups open | Pay per direct consultation without mandatory prefunding is confirmed in ADR 0006. Preserve legacy balances/history; review intent/booking/reconciliation/refund mechanics and follow-up billing separately before activation. |
| P08 | Pricing changes after postponement or doctor substitution | Preserve snapshot for same-doctor reschedule; re-quote and require acceptance for a doctor change. |
| P09 | Is separate TMC collection amount recorded? | Optional referenced collection evidence; never infer collected cash from the reference price. |
| P10 | Legacy data and admin subsidy account semantics | Reconcile before backfill; do not let an internal platform wallet accidentally prevent accrual of a doctor's genuine payable. |

## 9. Protected non-financial scope

Preserve patient/doctor/TMC registration, email verification, account status controls, inquiries and their stored leads, TMC applications/documents, doctor credentials and verification, change approval, schedules, acceptance/queue/start/completion, proposed rescheduling with patient/TMC response, chat/video, prescription history and follow-ups.

Presentation improvements should expose approved doctor photo, qualification, specialty/expertise, experience, verification, price, availability, and consultation modes clearly. Private identity evidence, payout terms, and internal notes must not leak into public doctor profiles. No fabricated ratings, credentials, availability, or comparative claims.
