# Phase 1: recoverable baseline and controlled cleanup

Date: 2026-11-20. Scope: preserve current work, verify the existing application, and remove confirmed duplicate/historical material from active source locations. No financial rule changes or production deployment.

This report preserves the original Phase 1 results. Subsequent test-only corrections and the refreshed test baseline are tracked separately in [BACKEND_TEST_BASELINE.md](BACKEND_TEST_BASELINE.md).

## Recovery baseline

Private local recovery folder: `.local-recovery/phase1-20261120-verified/` (ignored by git).

- `working-source.zip`: 277 current source/document/artifact files, including untracked work. ZIP integrity and every recorded SHA-256 hash verified.
- `files.json`: original file sizes and integrity hashes.
- `head.txt`: original HEAD (`3537f12`, full hash stored locally).
- `status-before.z`: initial staged/unstaged/untracked status.
- `staged.patch`: original HEAD-to-index binary patch, including already staged archive deletions.
- `unstaged.patch`: original index-to-working-tree binary patch for included paths.
- `retired-files/`: exact original paths of archived material, with verified hashes.
- `cleanup-manifest.json`: recovery copy of the public manifest.

The snapshot intentionally excludes live `.env` files, uploads/media, database files, environments/dependencies, generated build/cache folders, private notes/history and logs. The two historical notes are preserved separately in the private archive, not in the source ZIP. This is source recovery, not a full operational backup. Original environment files and media were left in place. No git reset, index rewrite, commit or stash was performed.

An earlier `.local-recovery/phase1-20261120/` snapshot also exists. Use the `-verified` snapshot above: its staged patch additionally accounts for paths already deleted from the index before Phase 1.

## Cleanup performed

**48 files archived**, with original directory structure and per-file SHA-256 verification. See [the exact manifest](PHASE1_CLEANUP_MANIFEST.json).

| Group | Action and rationale |
| --- | --- |
| Root `models.py`, `serializer.py`, `views.py` | Archived old standalone onboarding implementations. Canonical application imports resolve under `telemedicine_backend/`. Unique source retained; no attempted merge into the active app. |
| Root `consultations/` and `telemedicine_project/` | Archived empty namespace stubs and the alternate ASGI draft; removed only emptied directories. Canonical WSGI/ASGI imports checked before and after. |
| Eight historical root guides | Archived with original paths; old conclusions/test claims are not treated as current. New README/plan is the documentation entry point. |
| Two dated backend deployment snapshot folders | Archived source copies. Four files differ from canonical source, so all original content is retained, not treated as byte-for-byte duplicates. |
| Three `frontend-build-video-*.zip` files | Checked ZIP integrity and member names: built frontend assets, source maps and public artwork. Archived as historical rollback artifacts, not deleted. |
| `AIDER_Deepseak_details.txt`, `misc.txt` | Archived privately; one note matches a credential-like pattern. Contents were not printed or copied into shared documentation. Added root ignore rules to discourage re-adding restored notes. |

The archived credential-like note was already tracked in git. Removing it from the working tree/next commit does not remove past git history or invalidate any key. If the value is live, its owner should rotate it; no credential rotation was performed during cleanup.

Kept: actual backend/frontend source, migrations, tests, lockfiles, active assets, uploads, `.env`, local environments, existing hidden agent history/cache, and `deploy/telemedicine` / `deploy/Backend Path.docx`. The latter deployment materials remain references pending verification against the actual hosting server. This phase did not inspect a live server.

Comparison after cleanup: **228 active backend/frontend source files unchanged** from the recovery snapshot. All pre-existing application modifications remain present. Root guide/code removals are new unstaged cleanup changes; previously staged/unstaged deletions remain untouched.

## Environment and test isolation

- Windows / PowerShell; Python 3.13.1; Django 5.1.6; psycopg2 2.9.10.
- Node 24.19.0; npm 11.17.0; React 19 declared by the existing package.
- A new PostgreSQL 18.4 cluster was created only at `.local-validation/postgres-phase1-isolated/`, bound to `127.0.0.1:55439`.
- Before tests, the runner verified the exact PostgreSQL data-directory path, local port, `phase1_test` user and dedicated test database name `test_phase1_20261120`. It refused to reuse an already existing test database.
- Test migrations were executed only by Django's test runner on this disposable database. No migrations were applied to the configured development/production database.
- After the full suite and focused diagnostics, database destruction was verified and the isolated PostgreSQL server was stopped. The first sandboxed initialisation eventually also completed; that separate cluster was never started.
- Validation settings use an isolated media folder, in-memory email, disabled provider credentials, and a socket guard rejecting external hosts. Existing signature-verification tests can use their own fake keys.
- Sandboxed localhost connections/initialisation were restricted. Approved execution outside that sandbox was used only for the disposable PostgreSQL cluster/test checks. An attempted maintenance connection under the sandbox failed before connecting; the ordinary app database was not used for tests.

## Actual verification results

| Check | Result |
| --- | --- |
| Canonical `manage.py check`, before and after cleanup | PASS: no issues. |
| Canonical modules and WSGI/ASGI callable imports, before and after | PASS: settings, users, consultations and marketing resolve under `telemedicine_backend/`. Import success does not certify websocket authentication or deployment configuration. |
| Existing Django suite (`users`, `consultations`, `marketing`) on disposable PostgreSQL | 58/60 passed; one failure and one error, detailed below. 60 tests ran in 293.907 seconds. Dedicated test database destroyed afterward. |
| Existing frontend Jest test, before and after | PASS: one application-shell export smoke test. Initial default-cache attempts failed on sandbox cache rename permission; workspace cache retry passed. |
| Production frontend build, before and after | PASS with the same existing two React hook dependency warnings in `ConsultationDetailModal.js` at lines 18 and 30. JS/CSS/chunk filenames and reported gzip sizes match. |
| `makemigrations --check --dry-run`, isolated settings | FAIL: existing marketing index-name drift; see below. No migration file written. |
| Active application source hash comparison | PASS: 228 files identical to the recovery snapshot. |
| All archived files | PASS: 48 moved files retain matching SHA-256 values. |

Existing build notices also include stale Browserslist data and a Node deprecation warning. Dependencies were not upgraded as part of cleanup.

## Known migration drift and coverage limits

Two existing suite problems were recorded without editing tests or changing application behaviour:

1. `test_staff_report_and_patient_wallet_post_blocked` expects HTTP 405, but the current endpoint returns 201 for a pending recharge request. The existing finance tests already expect this request workflow. The failing test exits before checking the staff reports. Creating a request is different from crediting the wallet; focused diagnostics check that distinction and the previously unreached reports.
2. `test_razorpay_verify_marks_payment_paid_with_valid_signature` enables Razorpay using fake keys and creates an order without mocking the gateway call. With external calls blocked, order creation does not return `gateway_order_id`, leading to `KeyError`. A focused diagnostic supplies a mocked order response and invokes the unchanged signature test. This is not evidence of a tested live gateway integration.

Supplemental diagnostics: **2/2 passed** in 7.391 seconds. A patient recharge request stayed pending, wallet balance and entries were unchanged, and staff report/CSV access passed. The unchanged payment-signature test passed with an explicit mocked gateway order. These results remain separate from the unmodified 58/60 baseline result; original test issues still need maintenance.

The model/migration dry-run requests only a marketing index rename:

```text
marketinglandingpage:
marketing_m_page_t_8dc654_idx -> marketing_m_page_ty_b6f352_idx
```

This is a pre-existing mismatch between the model's generated index name and its migration. Record and resolve it in a separate additive migration/explicit-index-name decision before rollout. Do not rewrite the applied initial migration or claim the drift check passed. Fresh disposable test migrations can still succeed despite this state mismatch.

The existing test suite exercises legacy pricing, not the new financial model. Passing it does not mean monthly quotas, independent doctor pay, the INR 100 gate, settlements or refunds are implemented. There are no dedicated marketing tests in the discovered suite. No browser-based visual review, live gateway/video/email integration test, real consultation, patient-data verification or production restore test was performed.

## Reproduction and local evidence

Local logs and harnesses are under `.local-validation/`, ignored by git because raw diagnostic output/private paths do not belong in shared source. Retain this folder for current-device follow-up; it is not included in a normal clone.

```powershell
# From repository root, uses canonical manage.py and existing virtualenv:
& telemedicine_backend/venv/Scripts/python.exe telemedicine_backend/manage.py check
& telemedicine_backend/venv/Scripts/python.exe .local-validation/check_entrypoints.py

# Only while the dedicated disposable PostgreSQL cluster is running:
& telemedicine_backend/venv/Scripts/python.exe .local-validation/run_backend_baseline.py
& telemedicine_backend/venv/Scripts/python.exe .local-validation/check_migration_state.py

# From telemedicine-frontend/; workspace cache avoids sandbox temp-directory rename errors:
$env:CI='true'
npm test -- --watchAll=false --runInBand --cacheDirectory=G:/Telemedicine_UsersApp/.local-validation/jest-cache
Remove-Item Env:CI
npm run build
```

The local test harness explicitly loads `phase1_settings`, verifies the isolated cluster identity and lets Django create/destroy `test_phase1_20261120`. Do not replace it with an unqualified `manage.py test` while ordinary database settings are loaded. The test server is stopped after Phase 1; deliberately restart only this exact local cluster for a rerun and stop it afterward. Recreate the isolated harness/cluster deliberately if moving to another machine.

Logs: `backend-tests-before.log`, `backend-diagnostics.log`, `backend-check-before.log`, `backend-check-after.log`, `entrypoints-before.log`, `entrypoints-after.log`, `frontend-tests-before-workspace-cache.log`, `frontend-tests-after.log`, `frontend-build-before.log`, `frontend-build-after.log`, `migration-state.log`. Failed sandbox/cache attempt logs are retained separately.

## Recovery instructions

1. Read `PHASE1_CLEANUP_MANIFEST.json` and identify the exact original path and matching private archive file.
2. Verify its hash before restoring. Copy to a separate review folder first; never overwrite new work blindly.
3. Prefer restoring useful content to the correct canonical module/document rather than recreating shadow backend namespaces.
4. For baseline source, inspect `working-source.zip`/`files.json`. The patches and original git objects preserve tracked differences and earlier deletions; use a separate checkout for patch recovery.
5. Never publish the private recovery directory: archived source, source maps, historical notes and patches can contain sensitive material.

Next step: Phase 2 policy/schema review. Resolve cancellation/refund and monthly quota timing rules before changing financial behaviour; preserve the confirmed TMC discount and wallet eligibility decisions.
