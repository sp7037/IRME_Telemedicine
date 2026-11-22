# TMC wallet ownership safeguard

Completed 2026-11-20 as a bounded G0 security fix, authorised by the owner. Existing commission arithmetic, quotas, doctor earnings and settlement design are unchanged.

## Enforced behaviour

- Generic patient booking rejects TMC-funded requests with HTTP 403. Direct booking rejects an attached TMC ID with HTTP 400. An attending patient cannot authorise a centre's wallet debit.
- The dedicated `/consultations/tmc/book-consultation/` endpoint resolves the centre from the authenticated, active TMC operator. A different submitted centre ID returns 403. Patients are scoped to that centre, including a locked ownership recheck before charging; a foreign patient returns 404.
- Paid TMC follow-ups require the owning operator, with a second check at the charge helper. Patients can still request eligible free or zero-charge follow-ups without a centre debit.
- TMC consultation payment order/verification requires the owning operator or the existing staff permission. Direct consultation payment remains scoped to its patient or existing staff permission. Merely being the patient of a TMC consultation does not authorise its payment actions.
- Wallet/recharge profile resolution requires the operator role and a profile belonging to that user. Negative tests cover foreign recharge order, verification and cancellation, and non-staff attempts to use staff funding/approval routes. Existing authorised staff operations remain unchanged.

The current patient interface already books DIRECT, and the TMC interface already uses the dedicated endpoint. Clients relying on the formerly unsafe generic TMC path must use the owning operator endpoint. Public/participant consultation history access was not broadened or removed.

## Files changed

- `telemedicine_backend/consultations/permissions.py`: shared owning-operator resolution.
- `telemedicine_backend/consultations/serializers.py`: generic booking validation and creation defence.
- `telemedicine_backend/consultations/views.py`: scoped booking, payment and follow-up permissions.
- `telemedicine_backend/consultations/tests/test_consultation_booking.py`: existing TMC fee/free/earning regressions now use the legitimate owning-operator endpoint; submitted-price spoofing also verifies rejection.
- `telemedicine_backend/consultations/tests/test_tmc_wallet_ownership.py`: 15 ownership regressions, including unchanged balances and absence of new financial/consultation records on denied actions.

Six existing TMC booking tests were moved to their legitimate endpoint rather than deleting their financial coverage. An insufficient-balance response assertion now matches that endpoint's response; no money rule changed. No migration was added or edited.

## Verification actually run

Command: canonical backend virtualenv Python running `.local-validation/run_backend_baseline.py --fast-password-hashing`. Final log: `.local-validation/tmc-ownership-final-tests.log`.

- Full `users consultations marketing` backend suite: **84/84 passed in 59.024 seconds**, no failures, errors or skips. A preliminary 83-test run found an endpoint-specific response assertion; the corrected final run supersedes it.
- PostgreSQL 18.4 in the guarded disposable cluster at loopback port 55439; dedicated database `test_phase1_20261120`, distinct from the normal app database. Fresh existing migrations applied by test setup; test database destruction and disposable cluster shutdown verified.
- Optional fast password hashing applies only to the regression runner. Application hashing is unchanged. External services are mocked/blocked; test media and email are isolated.
- Syntax checks and scoped whitespace checks passed. `makemigrations --check --dry-run` under isolated settings returned `No changes detected`.
- Previously pending doctor-photo verification is now closed: 3 backend moderation/upload regressions are included in the 84; frontend tests passed 6/6, and the production build passed with the two previously recorded hook warnings in `ConsultationDetailModal.js`. No frontend source changed for this ownership fix. The owner separately confirmed successful photo upload and approval.
- Only the verified owned backend process was restarted. Backend 8100 and frontend 3800 both return HTTP 200, with CORS allowing the frontend. The separate app on 3700 was untouched. This is readiness verification, not a live payment/video test.

## Preservation and limits

Before changes, `.local-recovery/tmc-wallet-ownership-20261120/` captured the original HEAD/status, 230 source hashes and a verified `files-before.zip`. Final source/docs are preserved in `files-after.zip`, with preservation evidence in `verification.json`. These are source recovery artifacts, not database/media backups. Recover individual files after reviewing later work; never reset the workspace over unrelated changes.

No ordinary database records, wallet balances, doctor activation/profile flags or approval decisions were changed by this task. All financial regression writes used the separate test database. User testing of doctor activation can continue independently.

Next separate task: audit direct financial admin writes and deletion authority. New commission policies, monthly quota lifecycle, refunds and settlements remain planned behind the existing G0 and policy gates. This fix does not establish the new ledger's concurrency or settlement correctness.
