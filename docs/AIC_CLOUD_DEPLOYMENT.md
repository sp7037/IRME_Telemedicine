# AIC Cloud deployment

Prepared 2026-11-21 for **telemedicine.irme.in**. Source preparation is separate from a successful live deployment. Start with synthetic accounts and no real medical records.

## Required services

- AIC Docker app hosting. Hobby is adequate for initial testing but sleeps after 30 minutes of inactivity; use always-on hosting before live consultations. Provider correspondence confirms no persistent disk or console on these app plans.
- External PostgreSQL, using SSL. Neon is one option for initial testing. Choose a region near the app server; verify hosting location, backups, connection limits and recovery terms. Use a direct or session-pooled endpoint, not transaction pooling, because release migrations use a session lock.
- A **private S3-compatible bucket** with TLS, persistent objects and credentials limited to the chosen bucket. Block public bucket access. Enable appropriate encryption, versioning/backups and recovery. Do not use a public bucket for identity or medical documents.
- SMTP for account-verification emails; the existing external video provider when video testing begins.

Database and object-storage costs/limits are separate from app hosting. Do not paste connection strings or keys into chat, source files, build arguments or GitHub. Previously exposed secrets must be rotated at their providers; a new clean branch does not erase old public history.

## AIC settings

1. Connect repository **sp7037/IRME_Telemedicine** and select the dedicated **codex/aiccloud-staging-20261121** branch, using the verified commit shown by the development handoff. Do not deploy the old main branch. Confirm GitHub Deployment checks succeed for that commit.
2. Set project root to the repository root and builder to **Dockerfile**. Keep the supplied entrypoint; do not add AIC's automatic Python start command. The image binds to `$PORT`, default 8000.
3. Add runtime variables from `telemedicine_backend/.env.production.example` in the hosting dashboard. Examples contain placeholders, not working credentials. Required groups:
   - `SECRET_KEY`: a new randomly generated secret, at least 50 characters.
   - `DATABASE_URL`: provider PostgreSQL URL with `sslmode=require` (preserve/encode special characters correctly). Do not add a second question mark if the URL already has query parameters. DB_* alternatives are supported.
   - `UPLOAD_STORAGE=s3`, `S3_ENDPOINT_URL`, `S3_BUCKET_NAME`, `S3_REGION_NAME`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`; endpoint must use HTTPS. `S3_ADDRESSING_STYLE=path` by default; use `virtual` only if your provider requires it.
   - `DEPLOYMENT_STAGE=staging`, `ALLOWED_HOSTS=telemedicine.irme.in`, `FRONTEND_BASE_URL=https://telemedicine.irme.in`, matching CORS/CSRF origins.
   - SMTP settings and sender/notification addresses. Leave payment keys blank or use Razorpay **test** keys; staging refuses live keys. Video keys remain server-side.
   - `WEB_CONCURRENCY=1` initially. Measure memory and load before raising it.
4. For a new empty database only, temporarily set `BOOTSTRAP_ADMIN_ENABLED=true`, your `BOOTSTRAP_ADMIN_EMAIL` and a unique strong `BOOTSTRAP_ADMIN_PASSWORD` (at least 14 characters). No default admin password is shipped. Creation is skipped if any superuser exists; existing accounts/passwords are never overwritten. Remove all three variables after the first successful login and redeploy.
5. Configure the custom domain and DNS using AIC's displayed target, then enable TLS. The proxy must supply trustworthy `X-Forwarded-Proto: https`, overwriting any client value. Health checks must use the allowed host and forwarded HTTPS header. An HTTPS redirect loop indicates incorrect proxy headers; do not disable HTTPS to hide it. If using AIC's temporary domain first, add that exact hostname and HTTPS origin to server settings and rebuild the media-base build argument for it.
6. Deploy. Startup checks storage write/read/delete, then runs committed migrations under a PostgreSQL lock before starting Gunicorn. A failed check prevents startup. A concurrent release exits with a retry message. No normal local database is transferred automatically. Build-time collectstatic needs no real credentials or DB connection.

## URLs and verification

- App: `https://telemedicine.irme.in/`
- App admin: `https://telemedicine.irme.in/admin/patients`
- Django admin: `https://telemedicine.irme.in/api/admin/`
- Readiness: `https://telemedicine.irme.in/api/healthz/` must return `{"status":"ok"}`. Pending migrations/database failure return 503 without credentials.

Use the initial admin email/password at either login surface. Create ordinary synthetic doctor/patient/TMC accounts through existing onboarding; approve their profiles through admin. Test verification emails, inquiries, fees and authorised staff test funding without live gateway charges. The local-test-credit command is deliberately disabled in production settings. Label any staging manual credit as synthetic and do not reuse that database for live accounting.

Test doctor photo upload/moderation, private identity document and consultation attachment downloads, access denied to unrelated users, registration, booking, postpone accept/reject and once-only wallet returns, chat, video and prescriptions. Redeploy, then verify both records **and previously uploaded objects** survive. Browser video/SMTP/payment-provider integrations need real staging configuration and manual verification; unit tests cannot prove them.

Staging sends Content-Security-Policy in report-only mode so provider integration testing can identify required origins without silently blocking the interface. Review browser violations, configure the explicit CSP_* allowlists for the selected video/checkout providers, and verify them before selecting production mode, which enforces the policy. No wildcard script origin is enabled.

## Recovery and production gate

Back up PostgreSQL and bucket objects together, record versions and restore-test them in an isolated environment. A source Git commit contains neither account data nor uploads. For existing populated databases, approve/verify backups before deployment because startup applies pending committed migrations. Do not restore an old database over newer financial activity to roll back code. Prefer an additive forward fix; inspect migration compatibility before selecting an older image.

The published release contains source and synthetic tests only, with no local DB, uploads, environment files or old Git ancestry. Rotate any credentials exposed on older public branches separately; access revocation must occur at each credential provider.

Before live launch: verify external storage privacy/persistence/restore, PostgreSQL backups and restore, SMTP, proxy TLS, error monitoring without tokens or medical payloads, always-on hosting and full patient/doctor/TMC acceptance tests. Resolve the known open video room on completion and review outstanding financial roadmap gaps. The current patient flow is wallet-backed full-fee review; planned per-consultation gateway checkout and the new financial engine are not delivered by this deployment change.

## References

- [Django 5.2 migrations](https://docs.djangoproject.com/en/5.2/topics/migrations/)
- [django-storages S3 options](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html)
- [Neon connection strings](https://neon.com/docs/connect/connect-from-any-app)
- [Neon regions](https://neon.com/docs/introduction/regions)
