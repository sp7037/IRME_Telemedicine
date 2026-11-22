# Release state and development handoff

Date: 2026-11-21. Preserve Django/DRF, React and PostgreSQL. Read BUSINESS_RULES.md and the ADRs before changes. Planning documents do not claim implementation.

Completed before deployment preparation: server-controlled prices, TMC wallet ownership, restricted financial admin edits/deletion, patient full-fee review and guarded privileged local test funding, verified legacy pre-start wallet returns and persistent postponement outcomes. Original financial references must be retained; no mass historical correction is authorised.

Deployment preparation: supported Django 5.2 LTS and locked dependencies; one Docker image with React and Gunicorn; same-origin /api/ and /api/admin/ routes; HTTPS/SSL fail-closed settings; protected private S3 uploads; serialised startup migrations; optional first-admin creation without password reset. No financial tables or migration sources were added/rewritten.

Verification: see AIC_CLOUD_DEPLOYMENT.md and GitHub Deployment checks for this exact commit. Local release verification and public CI results are separate. The ordinary local database, running environments and Git staging were preserved. Recovery copies and case-specific financial evidence remain private and are not shipped in this public release.

Pending: external database/bucket provisioning, live DNS/TLS/proxy configuration, SMTP/video/payment integration tests, database and upload restore tests, full staged user acceptance, and production sign-off. Direct patient gateway checkout, monthly quotas, commission/payable/settlement redesign, journal activation and the patient video room remaining open after completion are separate unfinished work. The first dormant G1A table remains a reviewed proposal, not an implementation.

Next: configure external services and verify the staging deployment without real medical records. Follow AIC_CLOUD_DEPLOYMENT.md. Do not start additional financial phases incidentally.
