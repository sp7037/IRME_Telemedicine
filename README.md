# IRME Telemedicine

Django/DRF, React and PostgreSQL for direct and TMC-assisted consultations.

This branch is an isolated source release for AIC Cloud staging at telemedicine.irme.in. It contains no local database, uploads, credentials, recovery archives or old Git ancestry. Existing local operational records are retained privately. Older public branches must be reviewed separately for exposed credentials.

- [Deployment procedure](docs/AIC_CLOUD_DEPLOYMENT.md)
- [Current implementation](docs/CURRENT_STATE.md)
- [Development plan and verification](docs/DEVELOPMENT_PLAN.md)
- [Business rules](docs/BUSINESS_RULES.md)
- [Acceptance scenarios](docs/ACCEPTANCE_SCENARIOS.md)
- [Deployment architecture](docs/adr/0008-aic-cloud-deployment.md)
- [Agent instructions](AGENTS.md)

Canonical backend: telemedicine_backend/. Canonical frontend: telemedicine-frontend/. Deploy the root Dockerfile; external PostgreSQL with SSL and private S3 storage are required. See the environment examples for placeholder variable names. Never commit populated environment files.

Registration, moderation, booking, queues, postponement, chat/video, prescriptions, legacy wallets, reporting and inquiries are preserved. Server prices, wallet ownership and financial admin boundaries are hardened. Patient gateway checkout, monthly quota/commission/payable redesign and the new journal remain planned. The known video-room completion issue remains open. This release is not evidence of a completed live deployment or production acceptance.
