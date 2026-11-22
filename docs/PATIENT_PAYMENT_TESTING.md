# Patient fee review and local funding

Date: 2026-11-21. See [ADR 0006](adr/0006-direct-patient-checkout-direction.md) for the agreed patient checkout direction and current implementation boundary.

## The reported low balance

Current legacy arithmetic adds a configured platform charge to the doctor base fee. In the reported case, base 100 plus platform 20 requires 120, while the patient balance is 100. The doctor card previously displayed only 100. The new card labels that as base fee and opens a server-generated full-price review before any booking POST.

The review shows base, platform charge, total, the authenticated patient's own balance and exact shortfall. Insufficient balance disables confirmation and links to the balance panel. Sufficient balance still requires explicit confirmation. A balance/add-funds/history shortcut is visible beside Profile in the patient header, including compact layouts, and on every patient page. Existing history is retained.

GET `/consultations/book-consultation/preview/?doctor_id=...` is patient-only, reads existing settings/wallet without creating either, and ignores submitted price/payer IDs. It is advisory: no quota, slot, price or money is reserved. Missing/unsupported INR settings return 409. Existing verified/approved doctor restrictions apply; booking performs its own availability checks.

The updated patient UI sends optional `expected_total` with confirmation. It is a consent guard, never pricing authority. The server rejects a mismatch both before booking and after actual finance creation inside the transaction, rolling back all postings if the price changed during creation. Old clients without the field retain their existing API contract. This is not a durable V2 quote or operation/idempotency service.

## Test now without making a payment

Use the existing authorised administrator account in the React app:

1. Open `http://127.0.0.1:3800/admin/patients`. In Patient Management, select the patient's profile, enter an amount (for example 500), put `LOCAL TEST CREDIT — no external payment` in the description, and select **Top Up Patient**.
2. For TMC testing open `http://127.0.0.1:3800/admin/tmc-wallets`, select the centre in **TMC Wallet Top-up**, enter the test amount/description and select **Record Top-up**.
3. Return to the patient/TMC dashboard and refresh. The credit and ledger history should be visible. In the reported 100/120 case, 20 is the current shortfall; adding a larger test amount allows several tests.

These routes use the existing posting services and explicit wallet-change permissions. A superuser has them; delegated staff need the mapped permission in [the admin audit](FINANCIAL_ADMIN_AUDIT.md). Generic Django wallet balance fields remain read-only. No patient/TMC self-credit endpoint, gateway signature bypass or fake successful Razorpay payment was added.

## Optional backend command

Run from `telemedicine_backend/` using its virtualenv. Replace the example profile ID and staff email with the actual local profile/admin. The patient/TMC profile ID is the ID in its Django admin profile URL, not necessarily the user ID.

```powershell
.\venv\Scripts\python.exe manage.py local_test_credit --patient-id 12 --amount 500 --actor-email "admin@example.test" --confirm-local
.\venv\Scripts\python.exe manage.py local_test_credit --tmc-id 8 --amount 500 --actor-email "admin@example.test" --confirm-local
```

Each successful invocation adds the specified credit once for that invocation; rerunning is another explicit credit. No target is credited automatically by installing this command. It requires DEBUG enabled, PostgreSQL configured on a loopback host, an explicit local confirmation and an active staff actor with the target wallet-change permission. It rejects production DEBUG=false, remote database hosts, invalid/non-finite amounts and missing/unauthorised actors. It posts through the existing atomic finance service, labels the entry `LOCAL TEST CREDIT`, and records actor and admin log in the same transaction. It makes no external payment and cannot be called by an HTTP patient request.

This is a privileged operator command, not authentication by knowing an email address; running backend management commands already requires trusted code/database access. Use only the intended local development environment. No ordinary account was credited or reset during this implementation because the requested patient/TMC target IDs were not supplied.

For testing the actual checkout integration later, Razorpay provides separate Test Mode keys and simulated payments without real money: [official test/live guide](https://github.com/razorpay/markdown-docs/blob/master/payments/dashboard/test-live-modes.md). No keys or provider mode were changed by this task. Do not substitute a production signature bypass for Test Mode.

## Verification and recovery

Actual final results belong to the executed record in [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md). New backend tests cover the reported 100/120 shortfall, preview privacy/no-write behaviour, malformed/unapproved doctors, global fallback, successful confirmed debit, stale-price denial, transactional rollback after a mid-creation price change, local command credits and production/permission/amount guards. Component tests cover low-balance confirmation blocking, add-funds navigation and explicit confirmation/cancellation.

Final results: **113/113 backend tests passed in 99.124 seconds** on guarded isolated PostgreSQL; **8/8 frontend tests passed in 7.611 seconds**, three suites. Canonical virtualenv runner `.local-validation/run_backend_baseline.py --fast-password-hashing` uses test-only fast hashing, isolated email/media and mocked/blocked external services. Final logs: `.local-validation/patient-preflight-tests-final.log` and `.local-validation/patient-preflight-frontend-tests-complete.log`. Initial new-fixture/dependency/encoding failures were corrected; the final results supersede those runs without removing tests or changing existing money expectations.

`CI=false npm run build` passed with the two existing hook warnings in ConsultationDetailModal lines 18/30. Migration dry-run under isolated settings returned `No changes detected`; existing migration sources remain unchanged. Test database destruction and disposable PostgreSQL shutdown verified. Only the owned backend was restarted; backend 8100 and frontend 3800 both return HTTP 200 with correct CORS. No real gateway integration or browser-based checkout flow was exercised, and no ordinary account was credited for verification.

Recovery artifacts are under `.local-recovery/patient-preflight-20261121/`: original source hashes and HEAD/status, verified before/after source/document ZIPs and final verification. These are source recovery artifacts, not database/media backups. Existing staged/unstaged/untracked work must be preserved.

No migrations, normal account mutations or financial schema activation are part of this task. Existing doctor approvals, TMC pricing/quotas and settlement behaviour remain unchanged. The current patient confirmation still debits the existing wallet; direct per-consultation gateway checkout is not enabled by this UI fix.
