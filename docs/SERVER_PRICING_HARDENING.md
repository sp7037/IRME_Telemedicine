# Server-controlled booking prices

Date: 2026-11-20. Scope: prevent ordinary booking request amounts from overriding configured fees. No new financial schema, monthly-quota implementation, independent doctor-payable policy or refund workflow is introduced.

## Implemented behaviour

- `resolve_doctor_consultation_amount` accepts consultation type and selected doctor only. It resolves the persisted doctor's consultation fee, falling back to the existing configured direct/TMC default when the doctor has no positive fee. It no longer accepts an amount override.
- Both generic patient booking (DIRECT or TMC) and dedicated TMC dashboard booking use this resolver. Request `amount`, `doctor_fee`, `is_free` and discount fields do not determine fees or eligibility.
- Generic booking keeps the legacy validated `amount` input for client compatibility but never uses it as a price. Invalid legacy field formats may still fail input validation; valid lower/zero/higher values cannot alter a price.
- Financial/wallet validation occurs after the final doctor selection. The serializer's internal resolved amount is server-derived and passed to the existing atomic finance service, not copied from request JSON.
- Existing same-price availability fallback remains. If an alternative doctor has a different configured base fee, booking is rejected before any charge/record, asking the user to select a doctor and confirm the price. No quote endpoint or silent different-price substitution is introduced.
- Existing server-configured platform fee, TMC discount/free-quota arithmetic and ledger entries remain unchanged. Existing historical consultations are not repriced. The trusted internal finance helper may still take a resolved amount; future callers must never pass raw request amounts to it.

The stored doctor/global fee precedence and zero/missing-fee semantics are retained. This is a focused security fix, not publication of the proposed versioned policies/snapshots or approval of new commercial defaults. Role/ownership checks on generic TMC funding, admin financial edits, effective-date concurrency and the future quote handshake remain separate G0/design work.

## Source changes

- `consultations/finance.py`: remove request-style override from the booking resolver.
- `consultations/serializers.py`: price final selected doctor, reject differently priced alternatives, keep server-resolved booking input only.
- `consultations/views.py`: dedicated TMC booking no longer passes request amount to the resolver.
- `consultations/tests/test_consultation_booking.py`: existing price tests explicitly configure stored fees instead of depending on client authority; add six regression methods.

## Regression specifications

New tests exercise direct, patient/TMC and TMC dashboard paths with low, zero, high and omitted amounts. Nested transactions isolate repeated attempts so wallet/booking state does not leak between subcases.

They verify actual payment/finance amounts and wallet debits, server-calculated platform fees/discounts, inability to bypass insufficient balances, configured global fallback, and rejection of a different-price fallback without a booking or charge. Existing same-price fallback tests remain active.

Final verification: **66/66 passed** in 73.166 seconds on guarded isolated PostgreSQL, including the different-fee rejection guard. The final run used an optional fast test-only password hasher; real application settings/password hashes were unchanged. An initial 66-test run with normal hashing passed in 597.197 seconds before the extra fallback guard; it is preliminary evidence, not the final-code run. All six new regression methods remained enabled; no tests skipped. Project-wide migration dry-run reports `No changes detected`.

The test database was destroyed and disposable PostgreSQL stopped after verification. The backend alone was restarted after ownership checks; frontend and backend both return HTTP 200, and CORS still allows frontend 3800. No live consultation or payment was submitted to test pricing; all financial regressions use isolated PostgreSQL.

## Local demo accounts requested by owner

Three synthetic accounts were created in the configured local app database, after a verified database backup. They are explicitly labelled LOCAL DEMO, non-staff/non-superuser, use reserved `.test` addresses and do not represent real patients, clinicians or facilities. Doctor/TMC approval flags are enabled solely for local testing; no medical/identity proof documents were fabricated or uploaded.

Login uses email. All three actual login endpoints returned HTTP 200 with the expected role; the doctor goes to its dashboard. Passwords are supplied to the owner in chat only, not placed in repository documentation, fixtures or tracked files.

The patient and TMC each have INR 5,000 of separately labelled synthetic opening credit via existing wallet services; no external funds/payment were received. Doctor base fee is INR 100 and global platform settings were not altered. The demo patient is also associated with the demo TMC so both direct and assisted paths can be tried; complete/cancel an open consultation before booking another for that patient.

No existing users were reset and no real email or gateway request was sent. Owner-driven demo bookings will create local consultation/financial records; synthetic credit is not actual cash.

## Verification, recovery and runtime

- Source/document checkpoint: `.local-recovery/server-pricing-20261120/files-before.zip`; prior hashes and git state captured.
- Local database backup: `database-before-demo.dump` in that same ignored folder; complete archive read/decompression verified before fixture creation. This is database-only, not a media/roles backup or a full restore test.
- Demo ownership/funding/login evidence: private `local-demo-manifest.json`; no passwords or JWT tokens in this manifest.
- Final logs: `.local-validation/server-pricing-final-tests.log` (final code, fast test-only hashing), `server-pricing-tests.log` (initial draft, normal hashing), `server-pricing-migration-check.log`, `server-pricing-database-finished.log` and `dev-server-health.json`. Final tested files/documents are preserved in verified `files-after.zip`; `final-code-hashes.json` identifies the exact tested source.
- Regression tests use only the guarded isolated PostgreSQL test database. Demo account creation/login checks use the owner-requested configured local app database. These are distinct operations and targets.
- Backend was restarted after verification because it uses `--noreload`. Its current parent PID is recorded in `.local-validation/dev-processes.json`; current backend logs are `dev-backend-pricing.stdout.log` / `dev-backend-pricing.stderr.log`. Frontend 3800 and the other app on `127.0.0.4:3700` were left untouched.

Next financial-development task should review remaining G0 role/account ownership and admin-write/deletion authority before activating the proposed new financial tables/engine.
