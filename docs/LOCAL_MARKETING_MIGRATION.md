# Owner-approved local marketing database migration

Date: 2026-11-20. Owner explicitly approved: back up the configured local database and apply the existing pending marketing migration. This is an environment/data-schema task, not new financial feature implementation.

## Completed operation

1. Verified PostgreSQL target is local and is not the disposable test cluster. Reviewed the migration plan: exactly `marketing.0001_initial`, forward only, containing two `CreateModel` operations. Confirmed neither marketing table already existed; no faking, overwrite or unrelated migrations allowed.
2. Created a full custom-format database dump **before** applying the migration. Backup is 241,475 bytes; SHA-256 stored privately in the verification record.
3. Verified archive listing, then read/decompressed the complete archive with `pg_restore` directed to the Windows null device. Rechecked the backup hash after migration. This validates archive readability; a complete restore into a separate database was **not** performed and this is not a restore-tested production backup.
4. Applied only the existing `marketing.0001_initial` migration. Created `marketing_callbackrequest` and `marketing_marketinglandingpage`, their existing declared fields/indexes and the normal migration-recorder entry. Original tables remain present; no consultation/wallet/doctor payment update or test data creation was part of this operation.
5. Verified both new tables are empty and the ordered index `marketing_m_page_t_8dc654_idx` exists on `page_type`, `is_active`, `state`, `city`.

No migration source was edited/generated. No fixture/landing-page seed was loaded. This applied the existing pending migration, not a new index rename or the proposed financial schema.

## Running-app verification

| Check | Result |
| --- | --- |
| Project migration state in configured local database | No pending migrations |
| Backend `GET /marketing/landing-pages/` | HTTP 200, empty list (no pages seeded) |
| Backend `OPTIONS /marketing/callback/` | HTTP 200, POST supported |
| Frontend `http://127.0.0.1:3800/` | HTTP 200 |
| Backup hash and expected new tables/index | Verified |

The frontend/backend were left running on 3800/8100. No inquiry was submitted, so no artificial lead or email was created. POST persistence/email delivery is not claimed to have been tested by the metadata check. Real landing-page content must be entered separately; an empty list is expected for newly created tables.

The earlier 60/60 isolated PostgreSQL regression result already exercised this exact initial migration. No application code changed in this environment task, so the full suite was not repeated.

## Private backup and evidence

Ignored local directory: `.local-recovery/marketing-database-20261120/`.

- `database-before.dump`: contains real local application data. Keep private; do not commit, publish or attach it to shared documentation.
- `verification.json`: backup integrity, migration and read-only runtime results; no password stored.
- `archive-contents.list`, `reviewed-migration.sql`, `migration-output.log`: local review/evidence files.
- `documents-before.zip` / `documents-after.zip`: documentation checkpoints, separate from the database dump.

Operational logs are under ignored `.local-validation/`. Credentials were read from existing configuration for the backup/migration and were not copied into documentation or command output. Uploaded media remains in its original folder; the dump is database-only and does not include uploaded files or server roles. It is not a full operational recovery package.

If restoration is needed, first restore to an isolated database and verify the intended recovery point. Do not overwrite a running database, undo other users' newer work, or reverse marketing migration after real inquiries have arrived without a separate recovery plan. No restoration or reverse migration was performed.

Next financial-development task remains server-controlled pricing, as recorded in [the development plan](DEVELOPMENT_PLAN.md). This operation introduced no new financial business rules.
