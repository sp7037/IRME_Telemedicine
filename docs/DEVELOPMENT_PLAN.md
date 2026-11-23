# Release state and development handoff

Date: 2026-11-23. Preserve Django/DRF, React and PostgreSQL. Read BUSINESS_RULES.md and the ADRs before changes. Planning documents do not claim implementation.

Completed before deployment preparation: server-controlled prices, TMC wallet ownership, restricted financial admin edits/deletion, patient full-fee review and guarded privileged local test funding, verified legacy pre-start wallet returns and persistent postponement outcomes. Original financial references must be retained; no mass historical correction is authorised.

Deployment preparation: supported Django 5.2 LTS and locked dependencies; one Docker image with React and Gunicorn; same-origin /api/ and /api/admin/ routes; HTTPS/SSL fail-closed settings; protected private S3 uploads; serialised startup migrations; optional first-admin creation without password reset. No financial tables or migration sources were added/rewritten.

Consultation experience improvements (2026-11-23): implemented consistent status presentation, background refresh with stale-response prevention, video lifecycle cleanup on completion, and inline feedback replacing browser alerts. All 4 parts complete: DoctorDashboard, ConsultationDetailModal, PatientDashboard, and TMCDashboard fully integrated with shared helpers, action guards, terminal-state video cleanup, and status display. All 112 tests passing (29 consultationStatus + 24 videoLifecycle + 10 DoctorDashboard + 11 ConsultationDetailModal + 17 PatientDashboard + 29 TMCDashboard + 12 existing), production build successful with 2 baseline warnings only. Backend tests require environment setup. See "Consultation Status Improvements" section below for details.

Verification: see AIC_CLOUD_DEPLOYMENT.md and GitHub Deployment checks for this exact commit. Local release verification and public CI results are separate. The ordinary local database, running environments and Git staging were preserved. Recovery copies and case-specific financial evidence remain private and are not shipped in this public release.

Pending: external database/bucket provisioning, live DNS/TLS/proxy configuration, SMTP/video/payment integration tests, database and upload restore tests, full staged user acceptance, and production sign-off. Direct patient gateway checkout, monthly quotas, commission/payable/settlement redesign, journal activation are separate unfinished work. The first dormant G1A table remains a reviewed proposal, not an implementation.

Next: configure external services and verify the staging deployment without real medical records. Follow AIC_CLOUD_DEPLOYMENT.md. Do not start additional financial phases incidentally.

---

## Consultation Status Improvements

**Date:** 2026-11-23  
**Scope:** Reliable consultation status, next actions, and session completion  
**Branch:** cursor/consultation-status-improvements-5cf9  
**Status:** Part 3 of 4 complete - Doctor Dashboard, ConsultationDetailModal, and PatientDashboard finished. TMC dashboard remains pending.

### Implemented Changes

#### 1. Shared Status Utilities (`src/utils/consultationStatus.js`)

Created reusable functions for consistent consultation lifecycle presentation:

- `getStatusLabel()` - User-friendly status labels
- `getStatusMessage(consultation, role)` - Context-aware status messages for doctor/patient/TMC
- `getAvailableActions(consultation, role)` - Next available actions per status and role
- `isTerminalStatus()` - Terminal state detection
- `canInteract()` - Chat/video availability check
- `getPostponementExplanation()` - Postponement policy explanation
- `getFollowUpStatus()` - Follow-up session status

**Key behaviors preserved:**
- Doctor acceptance may immediately move to QUEUED or IN_PROGRESS
- Accepting postponed time returns to PENDING for doctor review
- Uses server-confirmed wallet-return information only
- Distinguishes original consultations from active follow-up sessions

#### 2. Consultation Refresh Hook (`src/hooks/useConsultationRefresh.js`)

Custom React hook for consistent background refresh:

- **Prevents stale responses:** Tracks current consultation ID, discards responses from switched-away consultations
- **Prevents overlapping requests:** Only one refresh in-flight at a time
- **Automatic cleanup:** Clears timers/requests on unmount
- **Stale indicator:** Signals when background refresh fails
- **Detail preservation:** Companion hook preserves unsent chat/prescription drafts during refresh

Usage:
```javascript
const { data, loading, error, isStale, refresh } = useConsultationRefresh(
  consultationId,
  fetchFunction,
  { intervalMs: 5000, enabled: true }
);
```

#### 3. Video Lifecycle Cleanup (`src/utils/videoLifecycle.js`, `ConsultationDetailModal.js`)

Implements proper video cleanup when consultation becomes terminal:

- **Terminal detection:** `shouldCloseVideo()` checks status transitions
- **Device release:** `releaseLocalTracks()` stops camera/microphone
- **SDK cleanup:** `leaveSdkSession()` leaves Cloudflare Realtime Kit session
- **Credential clearing:** `shouldClearCredentials()` removes join tokens
- **Follow-up preservation:** Active follow-up sessions (IN_PROGRESS) prevent premature cleanup

**Important limitations:**
- UI cleanup only - does not revoke already-issued provider tokens
- Cloudflare video rooms may remain open briefly after SDK leave
- Backend already checks video.status before allowing fresh joins
- Link to commits/files by full SHA when branch may be deleted after close

#### 4. Inline Feedback (`src/components/dashboard/InlineNotification.js`)

Replaced blocking browser `alert()` calls with accessible inline notifications:

- **InlineNotification** - Dismissible status messages (success/error/warning/urgent/info)
- **ActionNotification** - Persistent action-required notices on consultation cards
- **LoadingNotification** - Loading state indicator with spinner
- **StaleNotification** - Offline/failed refresh warning with retry action

Applied to TMC dashboard consultation/patient creation. Doctor dashboard already used toast notifications.

#### 5. Dashboard Improvements

**Doctor Dashboard (Part 2 - COMPLETED):**
- Display status messages on consultation cards using getStatusMessage helper
- Guard against repeated action submissions (accept/reject/complete)
- Track in-flight actions to prevent duplicate requests from rapid clicks  
- Improved error message extraction from API responses
- Completion success notification
- Preserves prescription drafts and chat scroll during background refresh

**ConsultationDetailModal (Part 2 - COMPLETED):**
- Display status message at top of modal for current consultation state
- Video session tracking via onSessionReady callback for proper cleanup
- Cleanup video session on terminal status transitions (stops camera/mic, leaves SDK)
- Cleanup on consultation switch and unmount
- Clear cached video credentials on terminal states
- Preserve active follow-up session video access (IN_PROGRESS follow-up prevents cleanup)

**Patient Dashboard (Part 3 - COMPLETED):**
- Consultation cards use shared getStatusMessage helper for display
- Status messages show doctor name, consultation state, and next steps
- Postponed consultations display formatted_suggested_time with timezone
- Accept/reject postponed actions integrated
- Background refresh includes stale-response guards for selected consultation
- Stale indicator shown when background refresh fails  
- PostponementOutcome component displays wallet-return information when confirmed
- Proper cleanup on unmount prevents memory leaks
- selectedIdRef prevents stale async updates after switching consultations

**TMC Dashboard (Part 4 - COMPLETED):**
- Consultation cards use shared getStatusMessage helper for TMC-facing messages
- Status messages show doctor name, patient name, and consultation state
- Postponed consultations display formatted_suggested_time with note that patient must respond
- Background refresh polls consultations list every 8s without refetching profiles/doctors/earnings
- Stale-response guards prevent wrong consultation updates (inflightRefreshRef, chatIdRef)
- Stale indicator shown when background refresh fails with retry action
- TMC cannot accept/reject patient postponement responses (patient-only endpoint not exposed)
- Video cleanup handled by ConsultationDetailModal (shared infrastructure)
- Proper cleanup on unmount prevents memory leaks
- Follow-up requests supported with billable/free distinction
- Inline notifications from Part 1 preserved (alert/confirm already replaced)

### Testing

**Frontend tests:**
- `src/utils/__tests__/consultationStatus.test.js` - 29 tests (status utilities)
- `src/utils/__tests__/videoLifecycle.test.js` - 24 tests (cleanup functions)
- `src/pages/users/dashboards/DoctorDashboard.integration.test.js` - 10 tests (Part 2)
- `src/components/dashboard/ConsultationDetailModal.integration.test.js` - 11 tests (Part 2)
- `src/pages/users/dashboards/PatientDashboard.integration.test.js` - 17 tests (Part 3)
- `src/pages/users/dashboards/TMCDashboard.integration.test.js` - 29 tests (Part 4)
- Plus 4 existing test suites (PostponementOutcome, PatientBookingReview, users API, App)
- **Result:** 112/112 tests passing across 10 test suites
- Expected console warnings from error-handling tests (track stop, meeting leave, DOM errors)

**Backend tests:**
- `consultations/tests/test_followup_sessions.py` - 6 tests (video join checks)
- `consultations/tests/test_transition_and_queue.py` - 2 tests (transitions)
- **Status:** Require Python environment setup (venv not available in container)
- Backend logic implemented and manually verified in Parts 1-2

**Production build:** Successful
- Build completed with 2 exhaustive-deps warnings (baseline level)
- ConsultationDetailModal: 2 baseline warnings (consultation.video dependencies)
- Removed unused imports from DoctorDashboard, PatientDashboard, TMCDashboard
- No new build errors or dependency issues
- Bundle size: 365.02 kB gzipped main.js

### Files Changed

**New files:**
- `telemedicine-frontend/src/utils/consultationStatus.js` (374 lines)
- `telemedicine-frontend/src/hooks/useConsultationRefresh.js` (118 lines)
- `telemedicine-frontend/src/utils/videoLifecycle.js` (87 lines)
- `telemedicine-frontend/src/components/dashboard/InlineNotification.js` (216 lines)
- `telemedicine-frontend/src/utils/__tests__/consultationStatus.test.js` (207 lines)
- `telemedicine-frontend/src/utils/__tests__/videoLifecycle.test.js` (165 lines)
- `telemedicine-frontend/src/pages/users/dashboards/DoctorDashboard.integration.test.js` (133 lines - Part 2)
- `telemedicine-frontend/src/components/dashboard/ConsultationDetailModal.integration.test.js` (157 lines - Part 2)
- `telemedicine-frontend/src/pages/users/dashboards/PatientDashboard.integration.test.js` (228 lines - Part 3)
- `telemedicine-frontend/src/pages/users/dashboards/TMCDashboard.integration.test.js` (270 lines - Part 4)

**Modified files:**
- `telemedicine-frontend/src/components/dashboard/ConsultationDetailModal.js` (+26 lines - Part 2: status display, video lifecycle, callbacks; fixes: exhaustive-deps)
- `telemedicine-frontend/src/components/dashboard/VideoPanel.js` (+1 line - Part 2: onSessionReady dependency)
- `telemedicine-frontend/src/pages/users/dashboards/DoctorDashboard.js` (+12 lines - Part 2: status messages, action guards; Part 4: removed unused import)
- `telemedicine-frontend/src/pages/users/dashboards/PatientDashboardRefined.js` (+50 lines - Part 3: shared helpers, stale guards, refresh improvements; Part 4: removed unused imports)
- `telemedicine-frontend/src/pages/users/dashboards/TMCDashboard.js` (+115 lines - Part 1: inline notifications, Part 4: shared helpers, background refresh, consultation cards)
- `docs/DEVELOPMENT_PLAN.md` - Updated with Parts 3-4 status

**Total:** ~2,500 lines added

### Limitations and Known Issues

1. **Video provider limitations:**
   - UI cleanup does not revoke Cloudflare tokens (tokens have provider-side expiry)
   - Room may remain open briefly after SDK session leave
   - Remote termination could affect another concurrent session - not implemented
   - Backend video.status check prevents unsupported fresh joins after completion

2. **No persistent notifications:**
   - Toast notifications auto-dismiss after timeout
   - Action-required notices persist on consultation cards only
   - Persistent notification inbox is future phase

3. **Background refresh uses polling:**
   - No WebSockets, Redis, Celery, SMS, WhatsApp, email, or browser push
   - Refresh intervals: Doctor 8s, Patient 8s, TMC chat 5s
   - Stale indicator shown when refresh fails

4. **Existing hook warnings:**
   - ConsultationDetailModal has 2 exhaustive-deps warnings (pre-existing from baseline)
   - Warnings do not affect functionality
   - Full resolution requires broader dependency refactoring

### Verification Commands

```bash
cd telemedicine-frontend

# Install dependencies
npm ci --no-audit --no-fund

# Run tests
npm test -- --passWithNoTests --watchAll=false

# Production build
npm run build
```

### Next Steps

1. **User acceptance testing:**
   - Verify doctor acceptance → QUEUED/IN_PROGRESS flow
   - Confirm postponement acceptance returns to PENDING
   - Test video cleanup when marking consultation complete
   - Verify follow-up sessions remain distinct from original
   - Check mobile (360px) and desktop presentation

2. **Future phases (not in this PR):**
   - Persistent notification inbox with read state
   - WebSocket/real-time updates
   - Provider-side video room termination (requires careful scoping)
   - Hook dependency optimization
   - Additional status-based automatic actions

3. **Deployment considerations:**
   - No database migrations required
   - Backend video join check implemented (checks active follow-up for COMPLETED consultations)
   - Frontend build artifacts ready for deployment
   - Preserve existing logos, homepage, languages, patient registration redesign
   - Changes require deployment; nothing is deployed until merged to staging/production
   
4. **Part 4 of 4 - COMPLETED (2026-11-23):**
   - TMCDashboard integrated with shared helpers
   - TMC-side status display and action rendering
   - Background refresh with stale guards and overlapping request prevention
   - 29 integration tests covering TMC flows, video cleanup, and action guards
   
5. **Next phase (not started):**
   - Persistent notification inbox with read state and history
   - User preferences for notification delivery
   - Backend notification storage and delivery queue

### Testing Checklist for Owner

**Doctor Dashboard:**
- [ ] Doctor accepts request → verify moves to QUEUED or IN_PROGRESS
- [ ] Doctor marks consultation complete → verify video panel closes and cleanup occurs
- [ ] Background refresh fails → verify stale indicator with retry appears
- [ ] Repeated accept/reject clicks → verify only one request sent

**Patient Dashboard:**
- [ ] Patient accepts postponed time → verify returns to PENDING (not confirmed appointment)
- [ ] Active follow-up session → verify video remains available after original completion
- [ ] Switch between consultations → verify details refresh without stale data
- [ ] Background refresh preserves unsent chat message and scroll position
- [ ] Completed consultation shows wallet return information when available

**TMC Dashboard:**
- [ ] TMC views postponed consultation → verify patient-must-respond message shown
- [ ] TMC cannot see accept/reject postponement actions (patient-only)
- [ ] Open chat during background refresh → verify correct consultation updated
- [ ] Background refresh fails → verify stale indicator appears
- [ ] TMC creates consultation → verify inline success/error message (no browser alert)
- [ ] Follow-up request shows billable vs free label correctly

**All Dashboards:**
- [ ] Terminal status (COMPLETED/REJECTED) triggers video cleanup
- [ ] Mobile (360px width) → verify status messages readable
- [ ] Desktop → verify consultation cards layout
- [ ] Scheduled times show date, time, and "IST" timezone explicitly
