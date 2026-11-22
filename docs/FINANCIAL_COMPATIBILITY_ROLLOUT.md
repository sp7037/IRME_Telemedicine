# Financial API compatibility, migration and rollout

Date: 2026-11-20. **Design only; no rollout or migrations executed.** Read [schema design](FINANCIAL_SCHEMA_DESIGN.md), [ADR 0003](adr/0003-financial-schema-and-compatibility.md) and accepted [ADR 0002](adr/0002-monthly-quota-and-refund-policy.md).

## 1. Writer inventory and single posting authority

This is an implementation checklist derived from current source, not proof that all paths already use a common service. Repeat the mutation search before implementing because the working tree may evolve.

| Current path / function | Required adapter / compatibility behaviour |
| --- | --- |
| `ConsultationBookingView`, `ConsultationBookingSerializer.create`, `TMCBookConsultationView` | Common quote/booking orchestration, explicit source/payer, engine selection and operation key; no client-controlled charge |
| `finance.create_consultation_finance` | Legacy engine retains recorded semantics; new engine uses snapshot and common posting; never call both against one booking |
| `wallet_returns.return_verified_prestart_charge`, trusted historical rejection review | Legacy original-payer return plus platform adjustment; must use the common posting adapter before the payer wallet is journal-enabled. Keep original/return references and once-only result; no duplicate legacy fallback. See ADR 0007 |
| `DoctorResponseView`, status-update, start/complete views, `services.transition_consultation` | Keep scheduling transitions; common scope/evidence/completion orchestration across all completion routes |
| `finance.ensure_doctor_earning_for_completion` | Engine-specific accrual with completion idempotency; must not overwrite settled earning on repeat calls |
| `views._charge_followup_if_needed` / follow-up doctor response | Preserve existing billable/free decision while routing its wallet movement through common posting; no new follow-up price/payable policy |
| `patient_wallet_topup`, `tmc_account_topup`, staff top-up views | One referenced posting and API entry, authorised manual evidence, no direct balance editing |
| Recharge approval, Razorpay verify/order/cancel, `reconcile_approved_patient_recharges` and equivalent TMC reconciliation | Same original-funding operation guard; approval/checkout/webhook/reconciliation cannot credit independently |
| `_credit_platform_fee`, `_debit_admin_doctor_subsidy`, `admin_platform_topup` | Preserve and label legacy movements; map to reviewed legacy administrative accounts, not bank cash; new engine does not reuse these to accrue independent doctor payable |
| Django admin finance/wallet/earning inlines and registered models | Existing monetary projections/history become read-only; changes go through audited services. Do not allow direct model edits/deletes as a ledger bypass |
| Management/import scripts, repair tools, signals and future jobs | Inventory all writes including bulk updates/raw SQL; route through the same service or explicitly disable before account cutover |

Maintain an allowlist of posting writers and review the source search for balance/total changes. All engine versions that touch an activated wallet must emit the common journal plus existing wallet entry atomically. A legacy consultation can keep old price rules while its new wallet movement is recorded as `LEGACY_OBSERVED`; do not invent a new booking snapshot for it.

This is a writer migration, not dual charging: one business operation has one journal and one compatibility entry, both projections of the same balance change. If a writer cannot be adapted, that account/flow is not eligible for activation; no unjournaled fallback.

## 2. Existing endpoint contracts

Retain current paths, existing IDs, role ownership, monetary strings and history ordering during transition. These are current relative paths under `/consultations/`:

| Existing endpoint family | Compatibility plan |
| --- | --- |
| `book-consultation/`, `tmc/book-consultation/` | Add quote ID and idempotency header for V2; serve legacy/V2 through one authorised adapter. New money is server-resolved; `amount` is not permission to override it |
| `history/`, `tmc/consultations/`, `tmc/summary/` | Preserve workflow fields and IDs. Add explicit `financial_version` and role-filtered `pricing`/quota summaries |
| `doctor-response/<pk>/`, `patient-response/<pk>/`, `update-status/<pk>/`, `start-consultation/<id>/`, `complete-consultation/<id>/` | Keep status contract for old bookings; add service-evidence path/response for V2 without redefining automatic IN_PROGRESS as proof of service |
| `patient/wallet/`, `tmc/finance-summary/` | Keep balance/recent entries; append operation/reference and separate pending/refunded amounts. POST patient wallet continues creating a pending request, not a credit |
| Patient/TMC `recharge-requests/.../razorpay/order|verify/`, cancel and staff approval | Preserve ownership/IDs and response fields; shared verified funding operation underneath |
| `payments/<id>/razorpay/order|verify/` | Keep original Payment ID. Disallow a second external charge when a wallet already funded that same consultation; old ambiguous records require review |
| `doctor/earnings-summary/`, staff reports and CSV exports | Preserve original columns; add a versioned detailed report rather than silently relabel old columns. Reconcile source totals and distinguish earned/paid and recharge/revenue |
| Chat/video/prescription/follow-up and user/marketing routes | No route removals or broad refactor in the financial change; protect with existing and new regression tests |

Future paths such as quote, service-evidence, refund-case, gateway webhook and settlement actions are **proposals**. Final route names/OpenAPI definitions belong to the implementation slice. Do not document them as live endpoints.

### New booking handshake (example, not implemented)

1. Authenticated client requests a quote for the selected patient/doctor/source/TMC; server returns reference, actual price, benefit/quota reason, expiry and opaque quote ID. Doctor payable is omitted from patient/TMC/public responses.
2. Client submits accepted quote ID and a scoped idempotency key with existing booking inputs. No client monetary value can change the snapshot.
3. Server rechecks quote expiry, participant/doctor, policy versions, monthly period, availability/quota and funds under locks. A changed amount or free entitlement returns a structured conflict/re-quote result without side effects.
4. Same operation/payload replays original result. Same key/different payload conflicts. Different key cannot evade resource-level duplicate charge/completion constraints.

```json
{
  "financial_version": "V2",
  "pricing": {
    "currency": "INR",
    "reference_fee": "100.00",
    "payer": "TMC",
    "amount_charged": "70.00",
    "tmc_discount_amount": "30.00",
    "free_reason": null
  }
}
```

The example omits participant IDs and private payout terms deliberately. Patient/TMC statements show their own debits/returns, not another account's payout or raw journal.

### Legacy monetary fields

| Existing field | Legacy rows | Proposed V2 compatibility projection |
| --- | --- | --- |
| `amount_charged` | Original value unchanged | Actual payer charge from immutable snapshot |
| `doctor_fee` | Original base fee unchanged | Reference fee, explicitly deprecated label; never independent doctor payable |
| `platform_fee` | Original additive fee unchanged | Zero when no explicit approved additive surcharge; use new contribution fields for margin |
| `discount_amount` | Original discount unchanged | Actual paid TMC discount; quota-free benefit reported separately |
| `admin_subsidy_amount` | Original legacy subsidy unchanged | Legacy-only meaning, zero compatibility placeholder for V2; new expense/contribution comes from journal, not this field |
| `DoctorEarning.earning_amount` | Original recorded earning unchanged | Actual original-scope payable amount, linked to snapshot/journal |

These proposed projections require contract tests and dashboard label updates before V2 bookings reach clients using old finance displays. No existing persisted value is rewritten. Staff reports must identify V2 placeholders and never sum `admin_subsidy_amount` as complete platform cost. Private payable amounts are available only through authorised doctor/admin views.

An old client without the V2 handshake may continue only on an explicitly supported legacy booking path with trusted server pricing, or receive a clear upgrade/re-quote response. It must not silently create a V2 booking at an unshown price. Preserving an endpoint does not mean preserving authority for untrusted `amount` overrides; that existing risk needs a bounded hardening change before rollout, for legacy as well as V2 paths.

## 3. Legacy classification and opening balances

No production dataset was inspected in Phase 2B. The steps below are a future migration/reconciliation plan, not claims about actual balances.

1. On a restore-tested staging copy, inventory consultations, wallet accounts/entries, recharge/payment references, uncompleted bookings, quotas, earnings and settlements. Record counts, sum checks, duplicate references and orphaned relationships without exporting patient identities.
2. Add engine/provenance/checkpoint fields and new tables initially nullable/dormant. Existing records remain `LEGACY_V1`; absence of V2 snapshot is not an error or evidence of a free booking. Do not default pre-existing rows to V2.
3. Classify each legacy record as reproducible from posted evidence, incomplete-but-retainable, or unresolved. Unknown historic doctor agreements/quota periods/start times remain unknown. Current policy is not a backfill source.
4. Reconcile wallet current balance against recorded credits/debits and adjustments. Accounts with unexplained differences are excluded from activation pending owner-reviewed reconciliation; do not reset balances to force equality.
5. Establish an immutable `FinancialCutoverCheckpoint` per activated account/epoch: owner/account, cutoff/high-water mark, old balance and totals, evidence digest/counts, reconciliation status/actor, opening journal and activation time.
6. Import only verified account opening liabilities and known unpaid doctor liabilities into the new ledger against a separately labelled legacy-opening clearing/suspense/equity mapping approved for that import. Do not create historical cash, revenue or expenses. A wallet balance is evidence of its liability, not evidence of an equal current bank balance.
7. An opening entry does not create a new wallet top-up or lifetime credited amount. Preserve old entries/IDs; link checkpoint and new ledger. Use a read-only history union, with an explicit opening boundary rather than duplicate transaction lists.
8. Legacy consultations already charged before cutoff need booking-level deferred/revenue/refund mappings before new journal cancellation/completion processing. Do not add deferred revenue again because their payer wallet now has an opening. Unmapped cases remain on a controlled legacy/manual review lane and cannot bypass common wallet posting.
9. Reserve already-known unpaid doctor liabilities exactly once at opening; later confirmed payout debits that opening liability. Never accrue them again on replay. Legacy SETTLED status without payment evidence is labelled unresolved; no invented settlement reference.

Default policy when historical evidence is insufficient: preserve and flag, do not automate. Read-only history can remain available while affected financial mutations are temporarily restricted with a clear reason.

## 4. Staged implementation and activation gates

This breaks implementation into reversible, reviewable slices. It does not authorise all slices at once.

| Gate | Deliverable | Exit evidence / rollback boundary |
| --- | --- | --- |
| G0: baseline maintenance | Address two existing test issues and marketing index drift separately; price-authority, financial admin-edit and deletion paths audited | Fresh isolated PostgreSQL suite; mocked external calls; approved server-pricing contract; no applied migration rewritten |
| G1: dormant additions | New schema/policy/snapshot/operation constraints and version fields, explicit index names | Empty-database migration and representative legacy restore tests; no runtime path switched; additions safely unused |
| G2: common posting adapter | All wallet writers and projections use one atomic journal service; admin direct edits disabled | Every writer and race tested; no double entry/credit; backward API tests. No account activation with a missing writer |
| G3: reconcile and activate accounts | Checkpoints/openings plus controlled old-engine/new-journal adapters | Quiesce financial writes or lock and drain all in-flight writers around cutoff; verify high-water marks and totals; activate atomically with no missing/double movements |
| G4: coherent V2 booking lifecycle | Trusted quotes, independent pricing, monthly quota, accepted cancellation rules, evidence path, once-only doctor accrual, compatible UI all ready | F/Q/S specifications implemented on isolated PostgreSQL; relevant open policy/UI decisions settled. No pricing-only feature flag that omits refunds or payables |
| G5: limited new-booking cohort | Enable explicit doctor/TMC/direct cohort; store V2 engine on creation | Monitoring and per-account/per-booking reconciliation; no stale old clients; manual support/exception route; existing bookings never change engine |
| G6: settlement/report extensions | Referenced manual settlement, approved adjustment workflow and version-aware reporting | Allocation/partial failure/retry tests; confirmed paid evidence; no bank automation introduced |

Monthly scheduler, webhook worker and outbox sweeper are deployment capabilities, not guaranteed by cPanel/Python hosting. Choose supported persistent workers or bounded scheduled batches with the same idempotent services; do not rely on an in-process task that disappears when a request ends. Allowance eligibility must remain correct if a scheduler is late.

First G1 sub-slice reviewed (documentation only): [G1A](DORMANT_FINANCIAL_SLICE_REVIEW.md) and [ADR 0005](adr/0005-first-dormant-financial-slice.md) specify one dormant operation identity table, named checks/unique indexes, protected actor reference, UPDATE/DELETE protection and D01-D12 tests. No existing engine/version fields, backfill or runtime writer in G1A. Later slices supply the remaining policy/snapshot/execution and journal requirements; G1 is not complete with the identity table alone. Implementation and ordinary-database application are separate actions, not performed by this review.

2026-11-20 G0 maintenance update: the two test issues are fixed and the existing backend suite passes 60/60 on isolated PostgreSQL; see [baseline report](BACKEND_TEST_BASELINE.md). [Marketing index alignment](MARKETING_INDEX_MAINTENANCE.md) also passes the project-wide migration dry-run, actual PostgreSQL index verification and a fresh 60/60 regression run. Price-authority/admin/deletion audits remain unfinished G0 work. This does not mark G0 or financial activation complete.

Later G0 update: [server-controlled pricing](SERVER_PRICING_HARDENING.md) is implemented for request amounts across current booking paths, including different-fee fallback rejection; final regression suite passes 66/66 (test-only fast hashing). Wider role/account ownership and admin-write/deletion checks remain. Versioned quote/snapshot APIs and new financial engine are not activated by this fix.

Latest G0 update: [TMC wallet ownership](TMC_WALLET_OWNERSHIP.md) restricts spending to the owning operator across booking, paid follow-ups and consultation payment actions. Recharge ownership/staff boundaries also have negative regressions. Final isolated PostgreSQL suite passes 84/84. Direct financial admin edits and deletion paths still require their own audit; G0 and the new financial engine are not complete.

A model cannot enforce complete cross-row journal rules just by defining fields. Database constraints/triggers, posting permissions and migration reversibility need explicit code review and isolated tests at G1/G2. Each subsequent code slice must update the plan and actual verification result.

Admin/API G0 audit completed: [audit report](FINANCIAL_ADMIN_AUDIT.md) and [ADR 0004](adr/0004-financial-admin-boundaries.md) record read-only financial administration, protected admin owner deletion, usage-counter restrictions, specific staff financial write permissions and service-backed manual decisions. Final isolated suite passes 103/103. Legacy ORM/SQL deletion and description-based reconciliation risks remain explicit for G1/G2 constraints/posting work. No new financial tables, account cutover or V2 activation is authorised by this checkpoint.

## 5. Financial engine dispatch and controlled rollback

- `LEGACY_V1` vs `V2` is stored per booking at creation. Account ledger activation is a separate checkpoint: old and new bookings can use one journal-enabled wallet without changing old commercial terms.
- New financial postings require the matching engine implementation and account checkpoint. No implicit fallback to raw legacy arithmetic after V2 errors.
- Before any new journal posting: dormant additions/flags may be disabled while preserving old source behaviour, subject to compatibility tests.
- After accounts/journal/V2 postings exist: stop admitting new V2 bookings if necessary, retain read/history and supported completion/refund processing, drain or pause workers deliberately and reconcile uncertain operations. Keep the journal-aware application version running.
- Do not deploy the old binary, delete additive tables, reset balances, drop new rows or replay funding to simulate rollback. Recovery is a forward fix or an explicitly planned consistent full restore.
- Full restore requires matching database and media backups, worker/HTTP write freeze and reconciliation of external payments since the recovery point. A database restore cannot undo a real gateway payment or doctor transfer.
- After external timeout, classify outcome unknown and reconcile using stable references before issuing another request. Do not free in-flight refund/settlement capacity solely because a process lease expired.

## 6. Required reconciliation and monitoring

- Per posted journal: debit sum = credit sum in INR; no orphan/draft lines affecting projections.
- Per wallet: opening liability plus journal movements equals current spendable projection; wallet entries reference each actual movement once. Preserve separate lifetime vs checkpoint-period totals.
- Per original consultation: one snapshot/charge/reservation, actual refunds <= original charge, completion revenue/doctor accrual once. Original and follow-up scopes separate.
- Per TMC period: granted/amended, active reserved, consumed, released and expired quantities consistent; no late release boosting current allocation.
- Per doctor: verified opening unpaid + accruals + signed adjustments - confirmed settlements = outstanding liability, with reserved allocations shown separately.
- Per gateway payment: one funding/charge authority, captured vs refunded vs settled amounts reconciled; clearing/fee reports separate from wallet available funds and consultation contribution.
- Per rollout epoch: processed high-water marks, unresolved legacy records, pending external outcomes, duplicate/conflicting operations and outbox retry age visible to authorised staff. Redact logs.

## 7. Remaining business/UI choices and safe defaults

No unapproved commercial choice is converted into a default because a schema has a column.

| Item | Design accommodation | Activation condition |
| --- | --- | --- |
| P04 discount precedence/old discount quotas | Versioned per-TMC rule, no accidental stacking, reference-base snapshot | Confirm supported precedence/quota semantics; do not auto-grant unlimited new discount rights |
| Service-start evidence | Assigned-doctor attestation, optional acknowledgement/dispute, scope-specific evidence | Review UX/permissions; ambiguous legacy evidence goes to admin |
| Mid-month allowance changes | Append-only amendment with protected reservations | Confirm decrease/visibility behaviour; no automatic entitlement introduced |
| P06 settlement dates/partial payout | Batch/allocation/attempt records | Admin sets and confirms period/cutoff and partial-payment treatment |
| P07 direct checkout/follow-up billing | Keep existing wallet and follow-up record scope; explicit funding source | New direct checkout/new follow-up pricing disabled until decided |

2026-11-21 P07 refinement: [ADR 0006](adr/0006-direct-patient-checkout-direction.md) accepts per-consultation direct checkout without mandatory patient prefunding as the product direction. Intent/booking/reconciliation/expiry/refund and legacy-credit mechanics still require design/implementation; the new checkout remains disabled. Current wallet-backed preflight/local testing is explicitly a transition step, and TMC wallets remain separate.
| P08 doctor substitution | Quote binds doctor and payable terms | Re-quote/acceptance design reviewed; no old doctor snapshot reused for replacement |
| P09 separate TMC collection | Optional external evidence reference | Never assume collection or pay platform cash against it |
| P10 legacy admin account mapping | Provenance and unresolved/reconciliation lane | Owner-reviewed mapping before automatic import/posting; no fake cash |

Phase 2B is complete as a bounded design artifact, not as approval of these unresolved settings or as proof of executable migrations.

## 8. Phase 2B preservation and verification

Before editing, 10 existing documents were ZIP/hash verified at `.local-recovery/phase2b-design-20261120/documents-before.zip`; hashes for 228 active source files, original staged status and HEAD were captured alongside it. This is document/source-preservation evidence, not an operational database/media backup.

Only documentation/agent guidance is changed in this phase. Validate links, cross-document scope and exact unchanged-source/staged evidence. No database, application tests, migration generation or network integration checks are warranted by a documentation-only edit; Phase 1's known results remain the baseline. S01-S16 are future test specifications, not executed checks.
