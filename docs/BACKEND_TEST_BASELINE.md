# Backend test baseline maintenance

Date: 2026-11-20. Scope: correct the two test issues recorded during Phase 1 and establish a fresh isolated PostgreSQL test baseline. This is test maintenance, not financial feature implementation.

## Changes

### Recharge-request regression

In `consultations/tests/test_stabilization_phase.py`, replace the obsolete expectation that patient wallet POST is unsupported with the current pending-recharge contract. The renamed test verifies:

- HTTP 201 creates the patient's own request with the correct requester and INR amount.
- Request status is PENDING, not an approved credit.
- Wallet balance, credited/debited totals and entry count remain unchanged.
- Patient access to the staff operations report is denied.
- Authorised staff report and CSV export still work.

This preserves and strengthens the original financial safety intent. No endpoint or crediting behaviour changed; existing recharge endpoint tests already expect the pending-request workflow.

### Razorpay fixture isolation

In `consultations/tests/test_finance_endpoints.py`, patch `consultations.finance.urlopen` only within the existing valid-signature test. Supply a context-managed mock order response, then exercise the original order-creation and signature-verification endpoint code.

The test checks one outgoing order request, POST URL, INR 350 represented as 35000 paise, currency, returned order ID, payment still PENDING before verification, and PAID/payment ID after the genuine HMAC verification path. It no longer attempts to contact Razorpay with fake keys or fails with an uninformative missing-order KeyError. Signature verification itself is not mocked.

## Verification

| Check | Result |
| --- | --- |
| Two corrected tests on isolated PostgreSQL | PASS: 2/2, 18.341 seconds. |
| Full existing backend suite | PASS: 60/60, 495.516 seconds; no failures, errors or skipped tests. Test database destroyed afterward. |
| Application/runtime source preservation | PASS: only the two intended test files changed; 226 other source files/assets unchanged. No runtime code changes. |
| Source syntax / whitespace | PASS: both modified test modules compile; scoped git whitespace check passed. |
| Documentation links / original staged state and HEAD | Verified; final preservation evidence stored with the recovery archive. |

The full suite still contains 60 tests; this step changes existing tests rather than skipping failures or changing application logic. This is the new passing backend test baseline. It does not imply that the future F/Q/S financial scenarios are implemented or that migration drift has been resolved. Existing migrations applied successfully during fresh test-database setup; model-vs-migration drift is a separate check.

## Database and integration isolation

- Reused only the dedicated PostgreSQL 18.4 cluster at `.local-validation/postgres-phase1-isolated/`, bound to `127.0.0.1:55439`.
- The guarded runner checks the server's exact data-directory path and test user, and refuses to reuse an already existing `test_phase1_20261120` database.
- Django creates/migrates/destroys only that dedicated test database. Ordinary development/production database settings are not the test target.
- Test media and in-memory email are isolated. Provider credentials are disabled by local validation settings; the signature test uses fake keys and mocked external order creation. External-host socket connections are blocked by the harness.
- The existing password hasher and application code remain unchanged, matching the earlier baseline conditions.
- After the successful run, test database destruction was independently verified and the isolated PostgreSQL server was stopped. No ordinary application database was migrated or modified.

No live payment, consultation, email, database migration or production deployment is performed by this maintenance task. Test-database migrations are run automatically by Django during isolated test setup.

## Reproduction and evidence

From repository root, while the exact dedicated cluster is deliberately running:

```powershell
& telemedicine_backend/venv/Scripts/python.exe .local-validation/run_backend_baseline.py consultations.tests.test_finance_endpoints.FinanceEndpointTests.test_razorpay_verify_marks_payment_paid_with_valid_signature consultations.tests.test_stabilization_phase.StabilizationPhaseTests.test_staff_reports_and_patient_recharge_request_does_not_credit_wallet
& telemedicine_backend/venv/Scripts/python.exe .local-validation/run_backend_baseline.py
```

The local wrapper changes into the canonical backend directory and loads isolated settings before running Django's test command. It is retained on this device under the ignored `.local-validation/` folder; do not substitute an unqualified test command using normal database settings. See [Phase 1 report](PHASE1_BASELINE.md) for isolation/recovery details. Recreate the same guarded settings deliberately on another machine.

Raw logs: `.local-validation/backend-fixed-targeted.log` and `.local-validation/backend-clean-baseline.log`. Keep raw logs private. The original 58/60 Phase 1 result remains historical evidence, not the current pass count after this task.

## Recovery and scope boundaries

Before edits, a ZIP of the original two tests and project documentation was integrity-checked at `.local-recovery/backend-test-baseline-20261120/files-before.zip`. The successful tests and final documents are preserved in the verified `files-after.zip` alongside verification evidence. Original source hashes, staged status and HEAD are recorded there. Restore individual files for review; do not reset the entire working tree or overwrite unrelated user work. These are local ignored source/document snapshots, not database/media backups.

Known separate work remains: marketing index-name drift, server-side price authority, financial admin/deletion hardening, reviewed open policies and all new-engine implementation gates. Frontend files were not changed and its build/tests were not rerun for backend test-only maintenance. This task does not alter architecture or accepted commercial rules.
