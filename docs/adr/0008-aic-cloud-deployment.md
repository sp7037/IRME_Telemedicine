# ADR 0008: AIC Cloud deployment boundary

Date: 2026-11-21. Status: deployment implementation, subject to verification and host configuration.

## Context and decision

The owner chose telemedicine.irme.in and authorised a separate Git deployment commit. AIC confirmed Dockerfile builds, PORT binding, external PostgreSQL over SSL, no persistent app disk and no console. Hobby sleeps after 30 minutes without visitors; Starter is always on. These capabilities are provider correspondence, not a completed live deployment.

Keep Django/DRF, React and PostgreSQL. Build React with Node 22, install the locked backend with Python 3.12, and run one non-root Gunicorn container. Serve the SPA and static assets on the same origin, API under /api/, Django admin under /api/admin/. Frontend /admin/ routes remain distinct. Use supported Django 5.2 LTS and audited dependency pins; do not update the running local environment incidentally.

Use an external PostgreSQL connection with SSL. Container startup verifies private object storage, obtains a dedicated PostgreSQL session advisory lock, applies committed migrations, then starts the server. A concurrent release exits and must retry. Never run makemigrations at startup. Existing applied migrations are unchanged. Use a direct or session-pooled database endpoint: transaction pooling cannot safely hold this session advisory lock. Take and restore-test backups before deployment to an existing populated database; code rollback does not undo migrations.

Uploads use private S3-compatible storage through django-storages. No public bucket URLs are emitted. Application URLs preserve existing field names, check record ownership/staff access, and stream authorised objects. Authenticated JSON responses supply short-lived, user/path-bound capabilities; approved public doctor photos remain public through the app. No upload persistence is claimed for the app filesystem. Bucket access policy, region, encryption, retention and restore tests remain operator responsibilities.

With no console, explicit temporary bootstrap environment variables may create the first administrator. The command validates credentials, creates only when no superuser exists, never promotes an existing account or resets a password, and prints no credentials. Remove bootstrap variables after the first successful login. All ordinary financial writes retain existing explicit permissions and audit services.

Use staging mode and Razorpay test keys only until verified. No local database, media, .env, backup or real user fixture is exported. An isolated, allowlisted source release avoids publishing local recovery material and old Git ancestry. It does not remove secrets from already-public branches or rotate external credentials.

## Limits

This does not implement the planned financial schema, patient gateway checkout, monthly quotas, settlements or video-completion fix. It does not activate unauthenticated websocket consumers. Existing HTTP/polling and external video providers remain. Live SMTP, payment/video credentials, DNS/TLS, S3 persistence/restore, database restore and end-to-end host behaviour must be verified before real consultations.

See [deployment procedure](../AIC_CLOUD_DEPLOYMENT.md) and [development plan](../DEVELOPMENT_PLAN.md) for actual verification status.
