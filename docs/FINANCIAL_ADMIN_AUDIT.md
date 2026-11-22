# Financial admin and deletion audit

Date: 2026-11-20. Scope: existing Django admin and financial staff write APIs, before new financial tables. Decision: [ADR 0004](adr/0004-financial-admin-boundaries.md).

## Findings and changes

| Surface reviewed | Finding / resulting protection |
| --- | --- |
| Patient/TMC/platform wallets and entries | Default admin could manufacture balances or change ledger evidence. All fields now view-only; no generic add/change/single or bulk delete, even for superusers. |
| Payments, finance, earnings and events | Amount/status/identity/history edits could bypass posting or fabricate settlement. Same view-only boundary; reports retain access. |
| Consultation and follow-up admin | Direct participant/source/free/status/charge edits could diverge from finance. Records and finance inline are view-only; doctor/patient/TMC workflow endpoints remain authoritative. |
| User/profile deletion | Cascades and SET_NULL could erase finances or their owners. Admin deletion disabled, including bulk actions. Deactivate instead. Existing profile user links cannot be reassigned through admin forms. |
| TMC usage counters | Editable in Django admin, React admin and staff offer PATCH. Counters are read-only; PATCH containing either counter returns 400 without partial changes. React retains usage displays and removes counter inputs/payload fields. Quota/discount settings remain editable with validation and audit. |
| Recharge admin status edits | Generic save invoked reconciliation without a dedicated decision. Requests now view-only; explicit approve/reject actions process pending manual requests with locked finance services, actor/time and an admin log. Repeats do not credit twice; rejection cannot later be approved. |
| Recharge services/reconciliation | Manual processing could act on gateway requests; reconciliation could credit them again using a different description. Manual service rejects gateway requests/evidence and missing/inactive/unauthorised staff. Legacy reconciliation is limited to MANUAL requests without gateway metadata. No historical automatic repair or reversal. |
| Staff funding/configuration APIs | `is_staff` alone previously authorised all writes. Financial writes now require the mapped model permission as well as active staff status. Input validation precedes configuration mutations; failed fee creation cannot leave all old settings inactive. |
| User admin authority | A delegated user editor could grant administrative flags/permissions or change another admin. Non-superusers cannot edit staff/superuser/groups/permissions fields or modify another privileged account. Superusers keep authority to assign permissions. |
| REST deletion routes | No user/profile/wallet/payment/earning/consultation destroy endpoint found in canonical routes/views. Existing doctor-schedule and qualification-document deletion remain role-scoped and unchanged. This is a local source audit, not a deployed penetration test. |

## Staff financial write permission map

Require authenticated, active `is_staff` plus the permission below. Active superusers satisfy Django permissions. A Django model view permission alone grants no corresponding write, through admin or API. Existing read/report permissions are unchanged.

| Action | Required Django permission |
| --- | --- |
| Patient manual top-up | `consultations.change_patientwallet` |
| TMC manual top-up | `consultations.change_tmcaccount` |
| Platform account manual top-up | `consultations.change_adminplatformaccount` |
| Patient manual recharge approval/rejection | `consultations.change_patientwalletrechargerequest` |
| TMC manual recharge approval/rejection | `consultations.change_tmcrechargerequest` |
| TMC offer configuration PATCH | `users.change_tmcprofile` |
| Create fee setting through staff API | `consultations.add_consultationfeesetting` |

Grant only needed permissions in Django admin through a superuser. No existing local user/permission was changed automatically. Doctor activation/verification/profile-change approval controls remain available as before. A recharge change permission authorises explicit processing actions; it does not unlock generic request edits.

Manual top-up entry descriptions retain the staff user ID. Recharge decisions retain request references, `processed_by` and `processed_at`; admin actions also log their decision transactionally. Offer API changes log changed fields and actor; fee settings retain their creator, with immutable creator attribution in the admin form. These legacy audit links are not the new financial journal.

## Implementation files

- `telemedicine_backend/consultations/admin_safety.py`: reusable read-only, no-delete and owner-link admin boundaries.
- `telemedicine_backend/consultations/admin.py`: protected registrations, inline, fee creator attribution and explicit recharge actions.
- `telemedicine_backend/users/admin.py`: protected owner deletion/reassignment, usage counters and delegated administrative authority.
- `telemedicine_backend/consultations/permissions.py`: active staff and per-view financial write permission checks.
- `telemedicine_backend/consultations/finance.py`: manual actor/permission/provider checks and reconciliation filtering.
- `telemedicine_backend/consultations/staff_api.py`: mapped permissions, counter rejection, validated configuration, atomic fee activation and audit references.
- `telemedicine-frontend/src/pages/users/dashboards/AdminDashboard.js`: removes usage-counter edits while retaining usage reporting.
- `telemedicine_backend/consultations/tests/test_financial_admin_safety.py`: admin/API regressions.
- `telemedicine_backend/consultations/tests/test_finance_endpoints.py`: grants explicit model permissions to legitimate staff fixtures; legacy reconciliation fixture now represents MANUAL funding. The former RAZORPAY fixture expected unverified credit; that expectation is deliberately replaced by gateway-denial regressions under ADR 0004.

## Verification and recovery

Final verification results are recorded in the executed maintenance entry of [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md). Tests run only against guarded disposable PostgreSQL, with mocked/blocked external services, isolated email/media and optional test-only fast password hashing. No ordinary database permission changes, financial writes or doctor activation changes.

- Full backend command: canonical virtualenv Python `.local-validation/run_backend_baseline.py --fast-password-hashing`; **103/103 passed in 74.575 seconds**, including 19 new admin/API methods. Log: `.local-validation/financial-admin-final-tests.log`. No skips, failures or errors. Test database `test_phase1_20261120` on the verified isolated cluster at loopback 55439 was destroyed, and the disposable server stopped.
- Migration dry-run: canonical virtualenv Python `.local-validation/check_migration_state.py`, isolated settings; `No changes detected`. All 45 existing migration sources remain byte-identical.
- Frontend command: `npm test -- --watchAll=false --runInBand --cacheDirectory=G:/Telemedicine_UsersApp/.local-validation/jest-cache`; **6/6 passed**, 2 suites, 48.575 seconds. These existing tests are smoke/profile regressions; the counter-edit security boundary is covered by the new backend tests.
- `CI=false npm run build` passed with the existing two hook warnings at `ConsultationDetailModal.js` lines 18/30. An earlier `CI=true` build rejected those same warnings; strict warning-free CI remains unresolved baseline maintenance. No modal source changed. Build log: `.local-validation/financial-admin-frontend-build-final.log`.
- Syntax and changed-line whitespace checks passed. Source/hash preservation, staged/HEAD comparison and document links verified; evidence in `.local-recovery/financial-admin-20261120/verification.json`.
- Restarted only the verified owned backend. Backend 8100 and frontend 3800 return HTTP 200, with the expected frontend CORS origin. The unrelated app 3700 was untouched. No live payment, consultation or medical record was created for verification.

Before changes, `.local-recovery/financial-admin-20261120/` captured 231 source hashes, original HEAD/status and a verified source/document ZIP. After verification, final source/docs and hashes are preserved in the same folder. Source archives are not database/media backups; recover individual files after reviewing later work, without resetting unrelated changes.

## Remaining scope and next step

Legacy ORM/raw SQL updates/deletes are not constrained by admin permissions. Existing FK cascade/SET_NULL definitions and description-based reconciliation remain recorded risks for the financial schema/posting work. Future models must explicitly protect evidence and use immutable references, not rely only on admin forms. No new tables or migrations were added in this maintenance slice; there is no backfill or account cutover.

Next bounded step: review a first dormant financial-schema slice and its constraint/legacy compatibility tests before implementation. Resolve any policy choices that affect that slice. New pricing policies, quotas, refunds and doctor settlements remain behind their documented gates; this audit does not activate them.
