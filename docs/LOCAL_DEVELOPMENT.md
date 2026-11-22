# Local development on separate ports

Date: 2026-11-20. These ports were selected to avoid the user's existing app at `http://127.0.0.4:3700/`. No process on port 3700 was stopped or reconfigured.

| Service | Address | Configuration |
| --- | --- | --- |
| React frontend | `http://127.0.0.1:3800/` | Loopback only; API/media point to backend 8100 |
| Django backend | `http://127.0.0.1:8100/` | Normal project settings and existing configured local database |
| Backend info check | `http://127.0.0.1:8100/api/info/` | HTTP 200 and frontend CORS origin verified |

Readiness verified: frontend root returns HTTP 200 with its React root element; backend `/api/info/` returns HTTP 200 and allows origin `http://127.0.0.1:3800`. The served frontend JavaScript contains the configured backend URL on port 8100. Both listeners bind only to `127.0.0.1`. Servers are intentionally left running. Startup/readiness is not an end-to-end consultation/video/payment test.

## Current processes and evidence

Servers were launched as hidden local processes. Current parent process IDs/URLs are retained in ignored `.local-validation/dev-processes.json`. Logs are private `.local-validation/dev-backend.stdout.log`, `dev-backend.stderr.log`, `dev-frontend.stdout.log`, `dev-frontend.stderr.log`; readiness results are in `dev-server-health.json`.

The backend currently uses `--noreload`; restart this app's backend after Python edits. React's development server handles frontend edits and compiled with the two previously recorded video-modal hook dependency warnings. Do not kill all Python/Node processes: another app is running. For manually launched foreground servers, stop only their own terminal with Ctrl+C. For current background servers, identify this workspace's exact parent/child command lines before stopping their process tree; never use old PID records without checking ownership.

After the server-price fix, the backend alone was restarted and both URLs checked again. Its latest logs are `.local-validation/dev-backend-pricing.stdout.log` / `dev-backend-pricing.stderr.log`. Owner-requested non-admin demo users for doctor/patient/TMC are ready; passwords were provided privately in chat and are not recorded here. See [demo setup and limits](SERVER_PRICING_HARDENING.md).

## Start in two PowerShell terminals

These environment variables apply only to that terminal and its children. Do not replace global `.env` files or another project's settings. Confirm the intended ports are free before launching; if this task's servers already occupy them, use the existing servers instead of starting duplicates.

Backend terminal:

```powershell
Set-Location 'G:/Telemedicine_UsersApp/telemedicine_backend'
$env:DJANGO_SETTINGS_MODULE='telemedicine_project.settings'
$env:DEBUG='True'
$env:ALLOWED_HOSTS='127.0.0.1,localhost'
$env:FRONTEND_BASE_URL='http://127.0.0.1:3800'
$env:CORS_ALLOWED_ORIGINS='http://127.0.0.1:3800,http://localhost:3800'
$env:CSRF_TRUSTED_ORIGINS='http://127.0.0.1:3800,http://localhost:3800'
& ./venv/Scripts/python.exe manage.py runserver 127.0.0.1:8100 --noreload
```

Frontend terminal:

```powershell
Set-Location 'G:/Telemedicine_UsersApp/telemedicine-frontend'
$env:HOST='127.0.0.1'
$env:PORT='3800'
$env:HTTPS='false'
$env:BROWSER='none'
$env:REACT_APP_API_BASE_URL='http://127.0.0.1:8100'
$env:REACT_APP_MEDIA_BASE_URL='http://127.0.0.1:8100'
npm start
```

Backend `DEBUG=True` and the React development server are local development settings, not hosting configuration. No service was intentionally exposed beyond loopback.

## Local marketing database migration (resolved)

Startup originally reported one unapplied existing marketing migration. After explicit owner approval, a verified private database backup was created and only `marketing.0001_initial` was applied. The configured local database now has no pending migrations; both marketing tables and the expected index were verified. This is distinct from the earlier model/index naming correction, which required no new migration.

Landing-page list and inquiry metadata endpoints now return HTTP 200. The new tables are empty: no landing content or inquiry was fabricated, and no real inquiry/email was submitted as a test. See [migration/backup evidence](LOCAL_MARKETING_MIGRATION.md). Never use the isolated regression-test database as the app's normal data source or silently apply all project migrations. Older startup-log warnings predate this approved operation.

## Next development task

2026-11-21 update: for testing consultations without real payment, use permission-checked admin patient/TMC top-ups or the guarded `local_test_credit` command described in [PATIENT_PAYMENT_TESTING.md](PATIENT_PAYMENT_TESTING.md). Do not edit wallet balances directly or bypass gateway signatures. The earlier next-task description below is historical; current checkpoints live in DEVELOPMENT_PLAN.

The marketing index correction passes project-wide migration dry-run and 60/60 PostgreSQL tests. Next financial-development work is server-controlled pricing: ordinary booking inputs must not override configured fees. Keep that code change separate from local server startup and any owner-approved database migration.
