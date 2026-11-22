# ADR 0001: Keep the existing stack and separate consultation financial rules

Date: 2026-11-20.

Status: stack and owner-confirmed business direction accepted for planning; schema and implementation proposed, pending phase review. Open policies are listed in `../BUSINESS_RULES.md`.

2026-11-20 amendment: [ADR 0002](0002-monthly-quota-and-refund-policy.md) accepts core P01-P03 monthly quota/refund decisions. It does not mark the proposed schema or implementation complete.

Phase 2B adds the proposed technical design in [ADR 0003](0003-financial-schema-and-compatibility.md); actual models/migrations and rollout remain pending.

## Context

The owner wants careful incremental improvements while choosing suitable Python hosting. Existing code already implements onboarding, consultation workflows, financial records and marketing. The workspace includes substantial uncommitted work and historical duplicate files.

Current pricing adds a platform percentage to the consultation base and treats that base as doctor earning. TMC discounts/free quotas subsidise that same base. This does not express the owner's independent doctor payout and TMC pricing model safely.

The owner confirmed that INR 100 reference price with INR 30 TMC discount means INR 70 wallet deduction and separate TMC collection. The INR 100 eligibility threshold is checked before deduction, including free consultations; it need not remain after deduction.

## Decision

1. Retain Django / DRF, React and PostgreSQL. No technology rewrite in this roadmap.
2. Canonical source is `telemedicine_backend/` and `telemedicine-frontend/`. Historical snapshots and root duplicates are not active edit targets.
3. Represent customer reference price, TMC charge/discount, direct patient price, and doctor payable independently. The doctor payout is an obligation of the platform, including when the TMC charge is zero.
4. Model TMC earnings as a discount benefit in this phase, not an additional cash commission payable. A later cash commission model would require a new decision and must not double-pay the existing discount.
5. Resolve server-side policy versions and persist immutable pricing snapshots. Existing completed/posted finances remain unchanged when policies change.
6. Introduce auditable monthly quota allocations and atomic reservations. Keep INR 100 pre-booking wallet eligibility separate from charging and quota eligibility.
7. Accrue doctor payable once on eligible completion. Weekly/monthly settlement is a separate referenced process; first support manual confirmed payouts rather than automatic transfers.
8. Financial mutation services use PostgreSQL transactions, deterministic locking and idempotency keys backed by constraints. Use an append-only balanced journal for new accounting flows, with wallet/earning projections and reconciliation. This is a financial correctness measure, not a microservices rewrite.
9. Refunds reverse linked original postings and settlement allocations as permitted by an explicit policy. Never delete the original evidence.
10. Introduce schema additively, test and reconcile before switching new bookings; never silently reinterpret legacy `doctor_fee` or `platform_fee` fields.

## Proposed conceptual records (not yet models)

- Effective-dated doctor commercial policy: reference/direct fee, independent payable mode/value, settlement frequency and version.
- Effective-dated TMC commercial policy: discount mode/value, applicable scope, monthly allowance and version.
- Monthly TMC quota allocation and reservation/consumption/release events.
- Consultation pricing snapshot with source/payer and all resolved amounts and policy references.
- Journal transaction, balanced lines and account mapping, unique operation/event keys, reversal links and actors.
- Refund request/attempt and verified external status/reference.
- Doctor payable, settlement batch and per-consultation payment allocation.
- Gateway event inbox: unique provider event ID, verified signature, processing status/retry history.

Final field names and existing-model reuse belong to a reviewed schema design. Do not create duplicate wallet balances without an explicit reconciliation strategy. Zero-charge bookings still require a snapshot and free/quota event; zero-value accounting lines need not be manufactured to balance a journal.

## Alternatives considered

- Rewrite to PHP now: rejected for this scope; it would combine financial changes with migration risk and discard useful work.
- Reuse a single fee for every amount: rejected; cannot express independent doctor pay and TMC charge.
- Credit TMC commission after deducting its discounted price: rejected; pays the same benefit twice.
- Reset free counters monthly: rejected; erases period evidence and complicates concurrent bookings and historical reports.
- Recompute historical amounts from latest policies: rejected; changes the meaning of already posted transactions.

## Consequences

More explicit records and reconciliation work are required, but each charge, benefit, doctor obligation and settlement can be traced. The platform can show negative contribution for free/subsidised work without making the doctor's payable disappear. Existing API consumers require compatibility during rollout, and existing tests embodying old fee arithmetic need intentional, documented replacement expectations.

## Verification

Use `../ACCEPTANCE_SCENARIOS.md`. Do not mark this decision implemented merely because this ADR exists. Phase gates and actual verification results live in `../DEVELOPMENT_PLAN.md`.
