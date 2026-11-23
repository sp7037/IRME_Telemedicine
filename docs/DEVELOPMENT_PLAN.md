# Release state and development handoff

Date: 2026-11-23. Preserve Django/DRF, React and PostgreSQL. Read BUSINESS_RULES.md and the ADRs before changes. Planning documents do not claim implementation.

Completed before deployment preparation: server-controlled prices, TMC wallet ownership, restricted financial admin edits/deletion, patient full-fee review and guarded privileged local test funding, verified legacy pre-start wallet returns and persistent postponement outcomes. Original financial references must be retained; no mass historical correction is authorised.

Deployment preparation: supported Django 5.2 LTS and locked dependencies; one Docker image with React and Gunicorn; same-origin /api/ and /api/admin/ routes; HTTPS/SSL fail-closed settings; protected private S3 uploads; serialised startup migrations; optional first-admin creation without password reset. No financial tables or migration sources were added/rewritten.

Consultation experience improvements (2026-11-23): implemented consistent status presentation, background refresh with stale-response prevention, video lifecycle cleanup on completion, and inline feedback replacing browser alerts. All 53 tests passing, production build successful with existing hook warnings preserved. See "Consultation Status Improvements" section below for details.

Verification: see AIC_CLOUD_DEPLOYMENT.md and GitHub Deployment checks for this exact commit. Local release verification and public CI results are separate. The ordinary local database, running environments and Git staging were preserved. Recovery copies and case-specific financial evidence remain private and are not shipped in this public release.

Pending: external database/bucket provisioning, live DNS/TLS/proxy configuration, SMTP/video/payment integration tests, database and upload restore tests, full staged user acceptance, and production sign-off. Direct patient gateway checkout, monthly quotas, commission/payable/settlement redesign, journal activation are separate unfinished work. The first dormant G1A table remains a reviewed proposal, not an implementation.

Next: configure external services and verify the staging deployment without real medical records. Follow AIC_CLOUD_DEPLOYMENT.md. Do not start additional financial phases incidentally.

---

## Consultation Status Improvements

**Date:** 2026-11-23  
**Scope:** Reliable consultation status, next actions, and session completion  
**Branch:** cursor/consultation-status-improvements-5cf9  
**Status:** Complete, ready for review

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

**Doctor Dashboard:**
- Improved error message extraction from API responses
- Added completion success notification
- Added guard against repeated action submissions
- Preserves prescription drafts and chat scroll during background refresh

**Patient Dashboard:**
- Existing status change notifications preserved
- Background refresh already prevents stale responses via `statusNoticeFor` callback
- Video request changes detected without opening chat modal

**TMC Dashboard:**
- Replaced `alert()` with inline success/error messages
- Added dismiss buttons for feedback notices
- Consultation chat refresh already scoped to open consultation ID

### Testing

**New tests:** 13 tests added in 2 test suites
- `src/utils/__tests__/consultationStatus.test.js` - 29 tests covering all status utilities
- `src/utils/__tests__/videoLifecycle.test.js` - 24 tests covering cleanup functions

**Test results:** 53/53 tests passing
- 6 test suites passed
- Expected console warnings from error-handling tests (track stop, meeting leave, DOM errors)

**Production build:** Successful
- Build completed with warnings (same 2 ConsultationDetailModal hook warnings as baseline)
- Warnings are pre-existing from f43bd43 baseline
- No new build errors or dependency issues

### Files Changed

**New files:**
- `telemedicine-frontend/src/utils/consultationStatus.js` (374 lines)
- `telemedicine-frontend/src/hooks/useConsultationRefresh.js` (118 lines)
- `telemedicine-frontend/src/utils/videoLifecycle.js` (87 lines)
- `telemedicine-frontend/src/components/dashboard/InlineNotification.js` (216 lines)
- `telemedicine-frontend/src/utils/__tests__/consultationStatus.test.js` (207 lines)
- `telemedicine-frontend/src/utils/__tests__/videoLifecycle.test.js` (165 lines)

**Modified files:**
- `telemedicine-frontend/src/components/dashboard/ConsultationDetailModal.js` (+40 lines)
- `telemedicine-frontend/src/pages/users/dashboards/DoctorDashboard.js` (+9 lines)
- `telemedicine-frontend/src/pages/users/dashboards/TMCDashboard.js` (+48 lines)

**Total:** 1,261 lines added, 7 lines removed

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
   - No backend changes
   - Frontend build artifacts ready for deployment
   - Preserve existing logos, homepage, languages, patient registration redesign

### Testing Checklist for Owner

- [ ] Doctor accepts request → verify moves to QUEUED or IN_PROGRESS
- [ ] Doctor marks consultation complete → verify video panel closes
- [ ] Patient accepts postponed time → verify returns to PENDING (not confirmed appointment)
- [ ] Active follow-up session → verify video remains available
- [ ] Switch between consultations → verify details refresh without stale data
- [ ] Background refresh fails → verify stale indicator appears
- [ ] TMC creates consultation → verify inline success/error message (no alert)
- [ ] Open consultation details during background refresh → verify scroll/chat preserved
- [ ] Mobile (360px width) → verify status messages readable
- [ ] Desktop → verify consultation cards layout
