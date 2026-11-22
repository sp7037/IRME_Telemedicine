# Marketing index-name alignment

Date: 2026-11-20. Scope: remove existing model/migration state drift without changing the applied migration, index columns, records or business behaviour.

## Diagnosis and change

`MarketingLandingPage.Meta.indexes` declared an unnamed index on `page_type`, `is_active`, `state`, `city`. Django generated the name `marketing_m_page_ty_b6f352_idx` from that model declaration, while the existing `marketing/migrations/0001_initial.py` explicitly records `marketing_m_page_t_8dc654_idx` for the same columns.

The only source correction is to explicitly name the model index `marketing_m_page_t_8dc654_idx`, matching the initial migration. No index rename is necessary for a database created from that migration. No migration file was generated, edited or applied to the ordinary application database, and no production database was inspected.

This is model metadata alignment. Inquiry forms, stored leads, landing-page fields, consultation/payment logic and frontend behaviour are unchanged.

## Actual verification

| Check | Result |
| --- | --- |
| `makemigrations --check --dry-run` using isolated settings | PASS: `No changes detected`, exit 0. |
| Fresh PostgreSQL migrations and actual index introspection | PASS: index `marketing_m_page_t_8dc654_idx` exists with ordered columns `page_type`, `is_active`, `state`, `city`. |
| Full existing backend suite | PASS: 60/60 in 527.687 seconds; no failures, errors or skipped tests. Test database destroyed and disposable server stopped. |
| Migration preservation | PASS: all 45 existing migration files unchanged by hash; no new migration files. |
| Source preservation | PASS: only `telemedicine_backend/marketing/models.py` changed; 227 other source files/assets unchanged. |

The migration dry-run checks the whole installed project, not only marketing. The ordinary application database is not queried or migrated by this check. Existing migrations run only on Django's fresh isolated test database for verification.

## Test environment and commands

Use the existing guarded local PostgreSQL harness: exact data directory `.local-validation/postgres-phase1-isolated/`, loopback `127.0.0.1:55439`, dedicated test database `test_phase1_20261120`. The wrapper verifies cluster identity and refuses an existing test database. External integrations are blocked/mocked, email and media isolated.

```powershell
# From repository root, while deliberately running only the dedicated test cluster:
& telemedicine_backend/venv/Scripts/python.exe .local-validation/check_migration_state.py
& telemedicine_backend/venv/Scripts/python.exe .local-validation/run_backend_baseline.py users consultations marketing --testrunner=marketing_index_validation.IndexCheckingRunner
```

The local test runner uses the existing Django discovery/migration lifecycle and adds a read-only index assertion immediately after test setup. It verifies PostgreSQL vendor/test-database identity and checks the created index's name, index flag and exact ordered columns. No extra permanent test mirrors the model declaration; the useful check is against the database produced by the unchanged migration.

Local logs: `.local-validation/marketing-index-drift.log`, `marketing-index-full-tests.log`; final shutdown and source/backup evidence are retained with this task's recovery records. The harness is local/ignored, not a portable test configuration in a normal clone; recreate deliberately on a new machine rather than running tests against ordinary app settings.

## Preservation and recovery

Before edits, original source/document files were ZIP integrity-checked at `.local-recovery/marketing-index-fix-20261120/files-before.zip`. Current hashes of 228 application source/assets, all 45 migration files, original staged status and HEAD are stored alongside it. Previous test corrections and all unrelated existing modifications remain protected.

After successful verification, final source/documents and exact hashes are preserved in verified `files-after.zip` and `verification.json` in that same ignored folder. This is local source/document recovery, not a full database/media backup. Restore individual files for review; do not reset unrelated work or restore a schema merely to rename an index.

## Limits and next task

Fresh migration/introspection does not inspect an already deployed server. If a live database has been manually altered or migrations were faked, inspect that server's migration/index state separately before deployment; do not rename/drop live indexes blindly.

The financial schema, quota/refund changes and other Phase 2 designs remain unimplemented. Next bounded work is trusted server pricing: prevent ordinary booking amounts from overriding configured fees, with regression coverage and a separate recovery checkpoint. Remaining G0 admin/deletion checks and policy/UI decisions are still required before financial activation.
