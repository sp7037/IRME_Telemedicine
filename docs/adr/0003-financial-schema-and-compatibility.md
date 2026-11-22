# ADR 0003: Financial schema and compatibility design

Date: 2026-11-20. Status: **Design baseline proposed; not implemented.** Phase 2B design deliverable complete; unresolved business choices and rollout gates remain explicit.

## Context and evidence

The accepted commercial rules are in [ADR 0001](0001-consultation-pricing-and-ledger.md) and [ADR 0002](0002-monthly-quota-and-refund-policy.md). This ADR selects a technical direction for review, not new commercial entitlements or permission to deploy.

Source inspection identified two booking writers (generic serializer and TMC view), multiple completion paths, direct wallet mutation in follow-up billing, admin/manual funding, recharge reconciliation, legacy platform-wallet accounting and auto-start on doctor acceptance. Existing `Payment` and `DoctorEarning` each have a one-to-one consultation relationship. They cannot be reused as a list of funding events, refunds or settlement attempts.

## Design decisions

1. Keep a single Django/PostgreSQL application and existing consultation, account and user identifiers. No new wallet system or microservice.
2. Add immutable commercial policy versions and per-booking snapshots. Separate reference price, actual charge, TMC discount, quota benefit and doctor payable. Missing policy blocks a new-engine quote; it does not imply a free service.
3. Reuse existing wallet balances and entry APIs as atomic projections of one posting service. All writers, including legacy follow-ups and admin actions, must go through that service before new journal-backed accounts are enabled.
4. Introduce balanced append-only journal transactions, operation idempotency, gateway-event inbox and durable outgoing work. Do not perform external network calls while holding wallet/consultation database locks.
5. Separate service-start evidence from scheduling status. Proposed UX is an assigned-doctor action, with a visible timestamp and optional participant acknowledgement; disputed/missing evidence goes to admin. This UX requires review before activation.
6. Keep each legacy consultation on its recorded financial engine. New-engine bookings are enabled only for validated policies, compatible clients and accounts with a reconciled opening checkpoint. A feature flag cannot change an existing booking's engine or historical amounts.
7. Extend existing doctor earning records with version/provenance and separate settlement allocations/adjustments. Do not use legacy `update_or_create` completion logic to overwrite a settled earning.
8. Phase additive schema, common posting adapters and tested orchestration before activating new pricing. The roadmap's ordering is not permission to enable pricing before quota, refund and payable dependencies are coherent.
9. Never use the old admin platform wallet as a source of truth for bank cash or as a condition for accruing a genuine doctor liability. Legacy operations remain labelled until mapped and reconciled.

## Detailed specifications

2026-11-20 technical refinement: [ADR 0005](0005-first-dormant-financial-slice.md) and the [G1A review](../DORMANT_FINANCIAL_SLICE_REVIEW.md) select one immutable operation identity table as the first dormant implementation slice. Mutable execution state/resource/results belong to later separate records/services. No tables or runtime callers are implemented by that review; the remaining gates below still apply.

- [Financial schema, constraints and transaction design](../FINANCIAL_SCHEMA_DESIGN.md)
- [API compatibility, migration, rollout and recovery](../FINANCIAL_COMPATIBILITY_ROLLOUT.md)
- [Acceptance specifications](../ACCEPTANCE_SCENARIOS.md), especially S01-S16

## Alternatives rejected

- A second patient/TMC wallet: would split available funds and create reconciliation ambiguity.
- Treating every reference to `IN_PROGRESS` as proven clinical service: acceptance and follow-up workflow already use it for other purposes.
- Recording only new booking writers in the ledger: misses existing follow-up, funding and reconciliation writers touching the same accounts.
- Reconstructing old doctor payable from current policy: invents historical agreements.
- Rolling back by switching to old application code after new postings: old writers cannot safely maintain new journal/refund/settlement invariants.
- Adding only status flags to `Payment`: does not express partial refunds, retry evidence or many-consultation settlements.

## Remaining review gates

P04 policy precedence/legacy discount quotas, service-start UX, mid-month allowance amendment behaviour, settlement calendars/partial payouts and legacy admin-account mapping still require the specified review. Direct gateway checkout, new follow-up prices and bank automation remain excluded until separately decided. Proposed technical field names/rounding/permissions below may be refined before implementation, with an ADR amendment; confirmed owner policies must not be silently changed.

## Verification and preservation

This phase writes documentation only. No Django migrations/models or test expectations changed, no database connected, and no gateway/hosting operation performed. Existing documents were ZIP/hash verified into `.local-recovery/phase2b-design-20261120/`; current application source hashes and git status/HEAD were captured before edits. Validation results and handoff live in `../DEVELOPMENT_PLAN.md`. New scenarios are specifications, not passing tests.
