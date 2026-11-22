# Repository working instructions

## Required reading

Before modifying application code, read `README.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/BUSINESS_RULES.md`, `docs/CURRENT_STATE.md`, and `docs/adr/0001-consultation-pricing-and-ledger.md`. Read `docs/ACCEPTANCE_SCENARIOS.md` for relevant verification.

User instructions take precedence. These documents protect agreed behaviour; they do not claim that future implementation work is already complete.

For quota/cancellation/refund work also read `docs/adr/0002-monthly-quota-and-refund-policy.md`: its core business policies were explicitly accepted on 2026-11-20 but are not implemented. Do not treat the remaining design details as confirmed rules.

For financial schema/API changes also read `docs/adr/0003-financial-schema-and-compatibility.md`, `docs/FINANCIAL_SCHEMA_DESIGN.md` and `docs/FINANCIAL_COMPATIBILITY_ROLLOUT.md`. These are proposed technical designs, not implemented features or approval of open commercial policies. Before journal activation, every wallet writer, including legacy follow-up/funding/admin paths, must use the common posting service. Never roll back to raw legacy writers after new postings exist.

For the first dormant schema implementation, read `docs/DORMANT_FINANCIAL_SLICE_REVIEW.md` and `docs/adr/0005-first-dormant-financial-slice.md`. G1A is one unused operation identity table with D01-D12 verification, not the whole financial engine. Keep execution/result state separate; add no runtime caller, money/policy/quota table, existing version flag, seed/backfill or normal-database migration as incidental work.

For patient checkout/testing work, read `docs/adr/0006-direct-patient-checkout-direction.md` and `docs/PATIENT_PAYMENT_TESTING.md`. The owner confirmed per-consultation direct checkout as the target; do not re-ask that direction or confuse the current wallet-backed fee review with delivered gateway checkout. Preserve legacy credits/history and TMC wallets. Never expose test self-credit or bypass gateway verification; local funding uses explicit privileged posting with audit.

For rejection/cancellation work, also read `docs/adr/0007-verified-prestart-wallet-returns.md` and `docs/POSTPONEMENT_RETURNS.md`. Verified legacy wallet returns already exist; preserve their original/return references and consultation locking. Include this writer in any journal cutover. Do not refund a previously returned charge again, infer provider returns, reset legacy quota counters or run mass historical corrections. No further historical correction or mass backfill is authorised.

## Scope and source of truth

- Keep Django / DRF, React, and PostgreSQL. A PHP/Laravel/MySQL rewrite is outside the current scope.
- Edit backend code under `telemedicine_backend/`, frontend code under `telemedicine-frontend/`.
- Run Django commands from `telemedicine_backend/` with that folder's `manage.py`; root-level duplicate namespaces are not the canonical backend.
- Do not implement all roadmap phases in one change. Complete the next authorised phase and record its result before proceeding to another phase.
- Preserve existing registration, verification, inquiries, approved profile changes, booking, queues, postponement/rescheduling, chat/video, prescriptions/version history, follow-ups, wallets, reporting, and marketing routes.
- Check `git status --short` before work. Preserve pre-existing staged, unstaged, deleted, and untracked work. Do not reset, clean, checkout over, or silently revert it.

## Financial invariants

- Customer reference fee, TMC wallet charge, direct patient price, and doctor payable are distinct values. Never infer doctor payable from the TMC charge.
- TMC commission is a discount retained through separate collection by the TMC. Do not also credit or pay that same discount to the TMC.
- Check the TMC's available balance against INR 100 before every new TMC consultation, including free ones. Also require enough for any charge. The balance may fall below INR 100 afterward. This eligibility threshold is not a fee or reserved deposit.
- Admin controls TMC flat/percentage discount, optional monthly free quota, and the doctor's independent payable rule. Quotas default to zero; no automatic entitlement for new TMCs.
- Free for the TMC does not mean free doctor work. Accrue the configured doctor payable on eligible completion and track actual settlement separately.
- Direct consultations have no TMC charge, discount, quota consumption, or commission.
- Quote and enforce prices on the server. An ordinary request's `amount` is not authority to change pricing.
- Snapshot pricing, policy versions, payer/source, and quota period when booking commits. Historical transactions must not be recalculated from current settings.
- Use Decimal / two-decimal INR amounts. Balance mutations, quota reservations, booking and financial postings must be atomic and idempotent under concurrency.
- Reversals must be linked entries; do not erase financial history. A gateway event, a wallet entry, an earning, and a payout are different records.
- Resolve the explicitly open policies in `docs/BUSINESS_RULES.md` before implementing their affected financial behaviour. Do not invent cancellation, quota restoration, or payout rules.

## Safe implementation and handoff

- Preserve the financial admin/API boundaries in `docs/adr/0004-financial-admin-boundaries.md`: never restore generic balance/status/usage-counter editing or owner deletion to work around a missing workflow. Register future financial models with protected admin behaviour and explicit write permissions; privileged ORM/SQL maintenance is not protected by admin mixins.

- Prefer additive migrations and API compatibility. Never rewrite applied migrations to change historical finances. Plan backfills, reconcile old/new totals, and protect unknown legacy values from fabricated defaults.
- Database-backed financial/concurrency verification must use a separate PostgreSQL test database, never the production or ordinary development database. Confirm its identity before running tests or migrations. Do not replace PostgreSQL with SQLite to claim locking tests passed.
- Never expose `.env`, credentials, medical records, or identity files in logs, documentation, git, or tool output. Production backups must include uploaded files and be restore-tested.
- Cleanup requires exact candidate paths, reference/import/build/deployment checks, and a recoverable copy or verified version-control history. Do not delete untracked work simply because it resembles a duplicate.
- Do not label code as tested unless the test actually ran. Record command, result, and environment limitations. Preserve relevant existing tests; change expectations only for an explicitly documented business-rule change.
- At phase completion update the phase status, files changed, verification results, unresolved decisions, and next step in `docs/DEVELOPMENT_PLAN.md`. Record architectural or business-rule changes in an ADR or amendment.
