# Acceptance scenarios and regression gates

Status: specifications only; not executed tests. Use a separate PostgreSQL test database for financial, migration and locking scenarios. Use synthetic identities and mocked gateway responses unless deliberately running an isolated sandbox integration.

## Pricing and wallet eligibility

| ID | Given / action | Required result |
| --- | --- | --- |
| F01 | Reference 100, TMC flat discount 30, doctor payable 50; balance 100 | Charge 70; balance 30; snapshot discount 30 and doctor payable 50; no additional commission credit. |
| F02 | Same case with 30% discount | Same resolved amounts; mode/value preserved. |
| F03 | Free monthly slot, doctor payable 50; TMC balance 100 | Charge 0; balance unchanged; quota reserved; completion accrues 50 once. |
| F04 | Free slot with balance 99.99 | Reject; no booking/quota consumption/debit; Add Funds guidance. |
| F05 | Balance 100, charge 150 | Reject; no side effects. |
| F06 | Direct patient price 100; doctor payable 80 | Platform collects 100 once, doctor earns 80 on completion; no TMC or quota/commission entry. |
| F07 | Change policy after an existing booking | Existing pricing/doctor payable remain snapshotted; new bookings use the new policy. |
| F08 | Client submits lower amount, free flag, discount or doctor payout | Server disregards unauthorised overrides/rejects tampering; authoritative quote applied. |
| F09 | Invalid negative/over-limit percentage, discount or money input | Clear validation error; no partial configuration or financial entry. |
| F10 | Repeat same booking operation / completion / funding verification | One business effect per operation; stable response or explicit conflict; no duplicate charge/payable. |
| F11 | Two concurrent INR 70 bookings against balance 100 | At most one succeeds; second sees updated balance and eligibility; no negative balance. |
| F12 | Two bookings compete for the final free slot | Only one reserves it; other re-quotes paid or fails transparently; no silent price increase beyond accepted quote. |
| F13 | Monthly boundary, reschedule and cancellation | Allocation history preserved; behaviour follows signed-off P01/P02/P08; repeat jobs do not duplicate allowances. |
| F14 | TMC/full price and free cases with fixed doctor payable 50 | Doctor amount stays 50 for both; actual payout remains separate from accrued earnings. |
| F15 | Payment webhook repeated/out of order, bad signature, wrong amount/currency/order | Invalid events cannot credit; valid event posts once; checkout and webhook cannot double-credit. |
| F16 | Paid cancellation/refund and retry | Follow approved P03; preserve original posting and linked reversal; reconcile gateway/wallet/payable outcomes. |
| F17 | Weekly/monthly settlement repeated or partial failure | No duplicate allocation/payment; unpaid amount accurate; confirmed external reference and batch traceable. |
| F18 | Month report with free, paid, refunded and pending records | Separate booking/completion/posting bases; totals reconcile to ledger, quota and wallet. |
| F19 | Upgrade/backfill legacy finances | Before/after wallet totals and historical earnings reconcile; unknown terms flagged, never invented. |
| F20 | Funding 500 then consultation charge 70 | Wallet movement and consultation revenue distinguished; no revenue double count. |

## Accepted monthly quota and refund policy scenarios

Q01-Q12 specify future implementation checks for [ADR 0002](adr/0002-monthly-quota-and-refund-policy.md), accepted on 2026-11-20. They have not been executed against application behaviour; the current app is not claimed to satisfy them.

| ID | Given / action | Required result |
| --- | --- | --- |
| Q01 | New TMC with no admin free allocation | Zero free entitlement; no joining bonus or invented grant. |
| Q02 | Last instant of November vs first instant of December in India | Distinct Asia/Kolkata half-open monthly periods; UTC conversion correct; unused November units expire without rollover. |
| Q03 | November reservation completed in December | Consume original November reservation once; December allowance unaffected; doctor earns its independent snapshotted payable. |
| Q04 | November reservation canceled in November before service starts | Release once into November availability; no cash credit for a zero-charge booking, no doctor earning. |
| Q05 | November reservation canceled in December before service starts | Record original-period release but leave entitlement expired; no extra December slot. |
| Q06 | TMC paid 70 on reference 100, then eligible pre-start cancellation | Return 70 to original TMC wallet once; no extra 30 discount/commission credit and no patient cash refund from platform. |
| Q07 | Direct patient paid 100 from wallet, then doctor rejects before start | Return 100 to same patient wallet, no doctor earning; do not also refund the original wallet top-up. |
| Q08 | Proposed reschedule accepted vs rejected before start | Acceptance retains same booking/snapshot/reservation without duplicate charge; rejection returns actual charge/releases original reservation. |
| Q09 | No-show, failure after start, or completed dispute | Admin evidence/reasoned decision; no automatic penalty/refund or invented doctor adjustment; preserve prior ledger/settlement history. |
| Q10 | Cancellation repeated, gateway callback replayed, refund retry, or simultaneous completion | At most one authorised outcome; total confirmed/in-flight refunds cannot exceed amount charged; quota and payable updated once under locks. |
| Q11 | Acceptance automatically set IN_PROGRESS but actual service start is disputed | Do not equate status/scheduled time alone with proven service delivery; use reviewed evidence or admin adjudication. |
| Q12 | Eligible return while TMC balance is below 100, or provider refund pending/fails | Return not blocked by new-booking threshold; actual posting/provider confirmation required before success; clear pending/failed/retry trail. |

Separate future checks must cover mid-month allocation amendments, authoritative service-start recording, doctor substitution, mixed funding/legacy records and paid-doctor adjustments after those designs are resolved.

## Schema, compatibility and rollout specifications

S01-S16 are future implementation checks for [ADR 0003](adr/0003-financial-schema-and-compatibility.md), [schema design](FINANCIAL_SCHEMA_DESIGN.md) and [rollout design](FINANCIAL_COMPATIBILITY_ROLLOUT.md). They have not been run; documentation validation is not database enforcement verification.

| ID | Given / action | Required result |
| --- | --- | --- |
| S01 | Apply dormant additions to empty DB and representative legacy copy | Old IDs/amounts/history retained; existing rows LEGACY_V1; missing historic terms remain unknown; no applied migration rewritten. |
| S02 | Publish conflicting policy intervals or quote without payable policy | Conflict/missing policy rejected; no accidental zero/free defaults or ambiguous active version. |
| S03 | Modify quote participants, replay key with changed payload, or free quote loses its slot | Reject/re-quote without debit/quota/earning; same accepted operation returns stable original result. |
| S04 | Attempt unbalanced, partial-posted, cross-currency or mutated journal | Database/service boundary prevents spendable inconsistent state; posted evidence cannot be edited/deleted. |
| S05 | Legacy follow-up, admin top-up, checkout/webhook and reconciliation act on a journal-enabled wallet | All movements use one posting service, each with one existing API entry; no unjournaled legacy fallback or double credit. |
| S06 | Import verified opening balances with history | No new top-up/revenue/lifetime-total inflation; current balance and epoch journal reconcile; unresolved account not activated. |
| S07 | Wallet writer arrives during cutoff | Drain/lock protocol and high-water mark include it exactly once; no opening-plus-live double posting. |
| S08 | Legacy pre-cutoff consultation completes/refunds after account activation | No second booking charge/deferred import/accrual; explicit mapped legacy handling or admin review; original commercial terms retained. |
| S09 | Acceptance auto-sets IN_PROGRESS; follow-up starts; original completion repeats | Separate scoped start evidence; original payable/revenue not duplicated by workflow changes or follow-up completion. |
| S10 | Client tries to charge provider for already wallet-funded consultation | Block duplicate funding/charge; preserve original Payment ID and funding evidence. |
| S11 | Legacy history, V2 history and CSV consumed by old/new clients | Version and money strings explicit; old values unchanged; doctor_fee never silently becomes doctor payable; placeholders not treated as full costs; private payout data role-filtered. |
| S12 | Admin attempts direct wallet/earning edits, or deletes financial owners | Posting/audit path required; immutable evidence and protected references retained. |
| S13 | Refund/provider/settlement timeout, duplicate event or worker lease expiry | Outcome remains reserved/unknown until reconciliation; no second payment or premature success/capacity release. |
| S14 | Part-settlement then retry/adjustment of already paid earning | Allocation cap and locking correct; confirmed paid evidence immutable; adjustment separately authorised and linked. |
| S15 | Disable new bookings after real V2 postings | Existing V2 processing remains journal-aware; no old-code fallback, table drop or balance reset; external transactions reconciled before full restore. |
| S16 | Financial monthly reports include recharge, charge, free service, refunds, opening and payable | Balanced postings/contribution examples match; no top-up/opening counted as consultation revenue; quota periods and settlement dates labelled. |

## Consultation and onboarding regressions

First dormant-schema implementation gate: D01-D12 in [DORMANT_FINANCIAL_SLICE_REVIEW.md](DORMANT_FINANCIAL_SLICE_REVIEW.md) specify isolated PostgreSQL migration/introspection, scope/unique checks, competing inserts, ORM/SQL mutation protection, actor FK retention, admin access, legacy compatibility and guarded reversal. These are unexecuted specifications. They do not replace the broader S/F/Q gates or prove once-only financial business outcomes.

1. All three registrations, required validation, duplicate identities, verification, approved-account access and role isolation work.
2. Existing doctor credentials and approved public fields render; private documents and commercial terms stay private; moderated edits do not silently overwrite approved data.
3. TMC profile documents/approval and assisted-patient ownership continue working; other TMCs cannot list/book/read those records through alternate endpoints.
4. Doctor availability, overlaps, duration, daily limits and concurrency are enforced on all booking paths.
5. Accept/reject, queue/start/complete, postpone and patient/TMC accept/reject of suggested time follow allowed transitions; no double-active consultation or repeated charge on reschedule.
6. Original and follow-up chat, prescription/version/PDF, and video access/request/response work for authorised participants only.
7. Marketing/TMC/course inquiries persist and remain visible to authorised staff; notification failure does not lose a stored lead; validation/rate limits and existing location/SEO routes remain functional.
8. Direct patient and TMC dashboards display their own funds, prices, history and actions accurately on mobile and desktop. Display price, discount, free allowance, doctor payable and settlement with unambiguous audience-appropriate labels.
9. Logout/session expiry, cross-role and cross-record access, authenticated document downloads, file validation and restricted public serializers are verified.
10. Production-like restore, health checks and configuration checks pass without live secrets in output; deployment does not expose backend source or medical files as public assets.

## Evidence to record per phase

- Exact command, environment and result; relevant functional/manual checks and visual observations.
- Existing failures versus new regressions; tests not run and concrete blockers.
- Schema/migration changes and rollback boundary; before/after reconciliation for any financial backfill.
- No claims of full regression coverage from a frontend build or from test-file inspection alone.
