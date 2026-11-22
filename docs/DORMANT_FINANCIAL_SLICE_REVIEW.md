# First dormant financial-schema slice: implementation review

Date: 2026-11-20. **Review complete; no models, tables or migrations implemented.** This narrows G1 into separately implemented slices. [ADR 0005](adr/0005-first-dormant-financial-slice.md) records the architectural refinement; existing commercial authority remains [BUSINESS_RULES.md](BUSINESS_RULES.md).

## 1. Selected first slice: G1A operation identity

Introduce exactly one dormant model, `FinancialOperation`, with immutable operation identity and request fingerprint. Its later purpose is to identify a retry and distinguish it from a changed request. The first implementation must not call it from any runtime booking, funding, completion or reporting path.

This is the smallest foundation independent of unresolved discount precedence, monthly amendments, service-start evidence, settlement calendars and legacy accounting. A policy-first slice could prematurely encode those decisions. A full journal-first slice would combine account mapping, opening balances and every writer before their separate implementation reviews.

Split the broad Phase 2B operation concept into immutable identity now and separate execution/result/attempt records later. Do not put a mutable execution state or result into the identity row and then weaken its immutability on the first retry. This record is not evidence of a payment, successful booking, doctor earning or completed business action.

| Included in the next implementation slice | Excluded |
| --- | --- |
| One model/table, identity constraints and stable names | New policies, prices, quotes or snapshots |
| Protected user-scope reference | Changes to legacy FK/cascade definitions |
| Read-only admin using the existing safety mixin | Generic create/change/delete APIs or actions |
| Database protection against UPDATE/DELETE | Ledger accounts, journal/posting adapter, wallet movements |
| One additive migration with empty-table reverse guard | Existing consultation version fields, defaults or backfills |
| Isolated PostgreSQL migration, identity and concurrency tests | Quota reservations, refund/settlement states, live activation |

No financial amounts belong in G1A. Existing reference price, TMC charge, direct price and independent doctor payable remain distinct requirements for later snapshots. The INR 100 pre-booking threshold and free-month rules are unchanged specifications, not implemented by an operation table.

## 2. Proposed exact field contract

Use canonical `telemedicine_backend/consultations/models.py`; table `consultations_financialoperation`. Existing user/consultation/wallet identifiers remain unchanged. New operation IDs are UUIDs; do not expose an operation endpoint in this slice.

| Field | Proposed representation | Required behaviour |
| --- | --- | --- |
| `id` | UUID primary key; server UUID generation | Stable identity, never copied from a client-supplied record ID |
| `scope_type` | Non-null varchar(8), USER or SYSTEM | Explicit; no implicit system/default scope |
| `scope_user` | Nullable FK to configured user model, `on_delete=PROTECT`, explicit index below instead of an automatically named standalone index | Required only for USER scope; preserves actor ownership; existing numeric user IDs retained |
| `system_scope` | Nullable varchar(64), deterministic C collation | Required only for SYSTEM scope; server-owned namespace, not a caller-selectable bypass |
| `kind` | Non-null varchar(32) | Explicit symbolic kind from the list below; no business processing implied |
| `idempotency_key` | Non-null varchar(128), deterministic C collation | Case-sensitive exact identity; reject whitespace/invalid shape, do not trim or lowercase into a different key |
| `request_digest` | Non-null varchar(64), deterministic C collation | Exactly 64 lowercase hexadecimal SHA-256 characters; never raw request/medical data |
| `fingerprint_version` | Non-null positive small integer, explicit value 1 | Format version; no inferred legacy fingerprint |
| `created_at` | Non-null timezone-aware creation timestamp | Server creation time; not financial service-start/payment/completion evidence |

Kinds: BOOKING, FUNDING, COMPLETION, CANCELLATION, REFUND, SETTLEMENT, QUOTA_AMENDMENT, ADJUSTMENT. These names reserve structural namespaces only. They do not approve a refund rule, entitlement, payout or new follow-up price.

System-scope pattern: `[A-Z0-9][A-Z0-9_.:-]{0,63}`. Key pattern: `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}`. Use full-string matches, with explicit length and null checks. Fingerprint version 1 identifies the future canonical request contract; the canonicaliser and its exact input allowlist must be reviewed with the first writer, not invented inside a migration. G1A verifies fingerprint shape only, not whether a supplied digest matches a real request.

All fields except the generated UUID/time require explicit values. Do not add a status, successful-result flag, patient/doctor/TMC relation, balance, money field, free allowance, raw payload or unconstrained metadata JSON. A resource may not exist when an intent is recorded; attach authorised resources and results through later protected records instead of editing this identity.

## 3. Constraints, indexes and write protection

| Explicit name | Enforcement |
| --- | --- |
| `finop_scope_valid` | USER requires a non-null user and null system scope; SYSTEM requires a null user and a non-null valid system scope. Reject both/neither/unknown scope. |
| `finop_kind_valid` | Kind belongs to the explicit list; choices in a form alone are insufficient. |
| `finop_key_valid` | Full bounded ASCII key pattern; non-empty. |
| `finop_digest_valid` | Full lowercase SHA-256 hex pattern. |
| `finop_fpv_valid` | Fingerprint version is exactly 1 in this slice. Future versions require an explicit schema/contract review. |
| `finop_user_key_uq` | Partial unique constraint on `(scope_user, kind, idempotency_key)` where USER. |
| `finop_system_key_uq` | Partial unique constraint on `(system_scope, kind, idempotency_key)` where SYSTEM. |
| `finop_created_idx` | Index on `(created_at, id)` for bounded internal review/history. |
| `finop_user_time_idx` | Unconditional index on `(scope_user, created_at, id)` for actor history and FK reference checks. |

The two scope constraints make null uniqueness behaviour explicit. Keep the unconditional user index: an actor-history/FK lookup may lack the USER predicate needed by the partial unique index. The explicit user-history index supplies the FK prefix lookup, so do not additionally create an automatically named standalone FK index. Constraint/index names must remain identical in models and generated migration state; use names within Django's portable name-length limit.

Add a PostgreSQL row trigger, explicitly named `finop_no_mutation`, using a dedicated `finop_reject_mutation` trigger function, rejecting every UPDATE and DELETE on the new table, including no-op updates. Use normal constraint/error handling in tests. This must cover model save/delete, queryset update/delete and direct SQL UPDATE/DELETE, not just the admin form. Do not catch an immutability error and silently report success. Inserts still require the relational/shape/unique constraints.

`PROTECT` prevents ORM user deletion when a USER-scoped identity refers to it; the actual PostgreSQL FK must also reject a committed SQL deletion of that referenced user. Do not use SET_NULL, fabricate a replacement actor or modify old rows when a user is deactivated. Deactivation does not change an existing identity.

The trigger is not protection against a privileged owner dropping/disabling it, TRUNCATE, dropping the table or a database restore. These remain operational privileges. Runtime database-role restrictions must be reviewed before live use. Do not advertise complete database immutability or full S04/S12 compliance from this one row trigger.

Admin registration uses `ReadOnlyFinancialAdminMixin`. Proposed model `default_permissions=("view",)` creates no generic operation add/change/delete permissions. No action, management seed, signal, scheduler, startup hook or internal live writer may create operations in this slice. Isolated test fixtures are the sole intended records until a separately reviewed writer is implemented.

## 4. Retry meaning reserved for later services

When a future authenticated writer is introduced, derive USER/SYSTEM scope on the server, validate actor/resource permission first, compute a versioned fingerprint and insert/retrieve by the unique scoped key. Same scope/kind/key plus same fingerprint identifies the same operation. A different fingerprint or fingerprint version for that key is a conflict; never overwrite the original. Different scopes/kinds can reuse a key safely.

A unique violation is not a replay response by itself: the writer must read and compare the winner after correct transaction rollback/savepoint handling. Processing state, result and failure/unknown outcome need separate locked records before a real writer can use this identity. There is no implemented replay response in G1A.

Different keys can still describe the same charge/completion. Resource-level uniqueness, execution locks, atomic posting and once-only business outcomes remain mandatory G2/G4 work. Do not enable a money writer merely because a scoped key is unique.

## 5. Additive migration and compatibility plan

Current reviewed consultation leaf: `0022_video_request_state_and_patient_recharge_cancel`; user leaf: `0019_tmcprofile_discount_quota`. Recheck both before coding. A proposed new migration is `0023_financial_operation_identity`; never edit applied migrations. Depend on the actual consultation leaf plus the configured user model's swappable dependency.

Forward operations: create the new table/constraints/indexes, then install the trigger/function, then add the reverse safety guard. Do not alter existing rows/columns/defaults, create financial engine markers, grant user/group permissions, seed records, import a legacy operation, reset a counter or infer a historic doctor's payable. Framework content-type/view-permission metadata is expected from post-migrate; granting it to existing users is excluded.

Reverse order must first refuse reversal if the operation table contains any rows. Only after an empty-table check may it remove the trigger/function and table. Implement the guard as the last forward operation so it runs first in reverse. Migration reversal requires an exclusive maintenance window preventing concurrent inserts; it is not an online recovery mechanism. Populated tables require a reviewed forward fix, not deleting evidence to make reversal pass.

Legacy ORM/code must not import/query the new model, and APIs/serializers/CSV responses retain existing shapes. No new nullable links or engine flags are necessary yet. Existing bookings, financial rows, balances, earned/settled flags, profile approvals and all IDs must compare unchanged after migration on a synthetic legacy fixture. No assumption that a missing operation row proves a legacy action never happened.

Existing user/profile/consultation CASCADE/SET_NULL chains remain unchanged. Their eventual protected-reference migration must inventory orphan/unknown legacy rows, inspect deletion effects and test historical references separately. New operation protection does not repair those old chains or legitimise their raw SQL deletion.

## 6. Required tests before this slice is marked implemented

These are **future tests, not results from this review**. Add a separate backend test module under the canonical consultations tests folder. Use verified isolated PostgreSQL, never SQLite or the ordinary development database.

| ID | Verification to implement | Pass condition |
| --- | --- | --- |
| D01 | Fresh database migration, introspection, migration dry-run | Exact table, field types/collation, FK, checks, unique indexes, trigger and names; no generated drift. |
| D02 | USER/SYSTEM scope truth table through ORM and SQL | Valid scopes accepted; both/neither/unknown/empty system scope rejected without a partial record. |
| D03 | Key/digest/version/kind invalid values and boundary lengths | DB constraints reject malformed values even when bypassing model validation. Explicit null behaviour tested. |
| D04 | Same scoped key with equal vs different digest/version | At most one identity; original immutable. No schema-level claim of a business replay response. |
| D05 | Same key across different users, system namespaces and kinds | Allowed independent identities; USER and SYSTEM cannot collide. |
| D06 | Competing inserts from independent PostgreSQL connections | Exactly one winner for the same scope/kind/key; losing transaction is rolled back cleanly; no wallet/booking side effect. Use barriers/timeouts and verify no hung workers. |
| D07 | Instance/queryset/SQL UPDATE and DELETE | Rejected, including changing only timestamp/digest/scope and a no-op update; original evidence retained. |
| D08 | Referenced user deletion, deactivation and SQL commit | ORM user delete protected; SQL FK prevents committed deletion; deactivation remains allowed without identity mutation. |
| D09 | Superuser, delegated view staff and ordinary user admin requests | Correct view boundary; no generic add/change/delete/single or bulk action. Only view permission generated, no grants. |
| D10 | Migrate from prior leaf with representative synthetic legacy history | All old record IDs, fields, wallet totals, usage counters and financial references unchanged; new table empty. Normal database untouched. |
| D11 | Reverse empty vs populated migration | Empty reversal succeeds in isolated maintenance; populated reversal refuses before dropping trigger/table; failed reverse leaves schema/data intact. |
| D12 | Existing full backend suite, API contract and writer search | Current regressions pass; no live path references the new model; no frontend/API change, worker or seed introduced. |

Migration tests must control and restore their schema explicitly. Concurrency tests may commit only to the guarded disposable database. Its test runner/owner can perform normal isolated teardown such as TRUNCATE after assertions; that is privileged test maintenance, not proof of production TRUNCATE protection. Do not disable triggers while asserting D07/D08. Restore migrations/close connections before the rest of the suite; do not repair failed tests by changing financial expectations.

D01/D10/D11 require a synthetic fixture migrated from the prior state, including paid/free and DIRECT/TMC histories, wallets/entries, recharges and earned/settled records. A production backup contains private data and is not needed for this test. This compatibility test is not a restore rehearsal for the production backup/media.

## 7. Exact implementation boundary and exit gate

Expected next implementation files: `consultations/models.py`, `consultations/admin.py`, one new consultation migration and one new test module, plus phase documentation. Avoid editing booking/finance/services/views/serializers, users, frontend or normal settings unless a demonstrated dependency is separately reviewed and recorded.

G1A is done only after D01-D12 and the full isolated suite pass, generated migration is reviewed, current source is recoverably preserved and phase evidence is saved. The next task after implementing G1A is review of the next dormant slice; it is not live pricing activation. G1/G2/G3/G4 remain incomplete after G1A alone.

Before policy publication or booking activation, resolve relevant P04 discount precedence/legacy limits, monthly amendment details, service-start evidence, payout calendar/partial settlement and legacy account mapping. A later policy row must preserve missing values as unknown, never silently supply zero payable or grant a joining quota. No business decision is changed by this review.

## 8. Evidence for this review

Reviewed current models, finance/manual processing, admin safety, migration leaf source, ADRs 0001/0003/0004, schema/rollout design and acceptance scenarios. Local virtualenv reports Django 5.1.6. No database connection, application test, migration command, gateway call or server restart was performed for this documentation task. PostgreSQL/Django constraint behaviour above remains subject to the specified implementation tests.

Recovery: `.local-recovery/dormant-schema-review-20261120/` contains verified before/after document ZIPs, 233 application source hashes, original staged/HEAD evidence and final verification. Existing 45 migration sources and application source must remain unchanged. Historical backend 103/103 and frontend 6/6/build results remain the prior baseline, not new test runs for D01-D12.
