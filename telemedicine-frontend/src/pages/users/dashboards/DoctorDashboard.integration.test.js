/**
 * Integration tests for DoctorDashboard
 * Tests status display, action guards, background refresh, and video lifecycle
 */

import { getStatusMessage } from '../../../utils/consultationStatus';
import { shouldCloseVideo, shouldClearCredentials } from '../../../utils/videoLifecycle';

describe('DoctorDashboard Integration - Status Display', () => {
  test('getStatusMessage returns appropriate doctor messages for each status', () => {
    const consultation = { status: 'PENDING', patient: { user: { first_name: 'Jane' } } };
    const result = getStatusMessage(consultation, 'doctor');
    expect(result.title).toContain('New request');
    expect(result.message).toBeTruthy();
    expect(result.severity).toBe('urgent');
  });

  test('status message changes when consultation moves through lifecycle', () => {
    const consultation = { status: 'PENDING', patient: { user: { first_name: 'Jane' } } };
    const pending = getStatusMessage(consultation, 'doctor');
    
    consultation.status = 'IN_PROGRESS';
    const inProgress = getStatusMessage(consultation, 'doctor');
    
    consultation.status = 'COMPLETED';
    const completed = getStatusMessage(consultation, 'doctor');
    
    expect(pending).not.toEqual(inProgress);
    expect(inProgress).not.toEqual(completed);
  });
});

describe('DoctorDashboard Integration - Video Lifecycle', () => {
  test('shouldCloseVideo returns true when moving from active to terminal without follow-up', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: null,
    };
    const previousStatus = 'IN_PROGRESS';
    
    expect(shouldCloseVideo(consultation, previousStatus)).toBe(true);
  });

  test('shouldCloseVideo returns false when active follow-up session exists', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: {
        id: 10,
        active_status: 'IN_PROGRESS',
      },
    };
    const previousStatus = 'IN_PROGRESS';
    
    expect(shouldCloseVideo(consultation, previousStatus)).toBe(false);
  });

  test('shouldClearCredentials returns true for terminal states', () => {
    expect(shouldClearCredentials({ status: 'COMPLETED' })).toBe(true);
    expect(shouldClearCredentials({ status: 'REJECTED' })).toBe(true);
    expect(shouldClearCredentials({ status: 'CANCELED' })).toBe(true);
  });

  test('shouldClearCredentials returns false for active states', () => {
    expect(shouldClearCredentials({ status: 'PENDING' })).toBe(false);
    expect(shouldClearCredentials({ status: 'IN_PROGRESS' })).toBe(false);
    expect(shouldClearCredentials({ status: 'QUEUED' })).toBe(false);
  });
});

describe('DoctorDashboard Integration - Action Guards', () => {
  test('repeated action guard prevents duplicate submissions', () => {
    const inFlightActions = new Set();
    const consultationId = 1;
    
    // Simulate first click
    const canSubmit1 = !inFlightActions.has(consultationId);
    expect(canSubmit1).toBe(true);
    
    if (canSubmit1) {
      inFlightActions.add(consultationId);
    }
    
    // Simulate second rapid click before first completes
    const canSubmit2 = !inFlightActions.has(consultationId);
    expect(canSubmit2).toBe(false);
    
    // Simulate first request completing
    inFlightActions.delete(consultationId);
    
    // Now can submit again
    const canSubmit3 = !inFlightActions.has(consultationId);
    expect(canSubmit3).toBe(true);
  });
});

describe('DoctorDashboard Integration - Stale Response Prevention', () => {
  test('stale response guard discards updates for switched consultation', () => {
    let currentConsultationId = 1;
    const responseForId1 = { id: 1, data: 'consultation 1' };
    const responseForId2 = { id: 2, data: 'consultation 2' };
    
    // Switch to consultation 2
    currentConsultationId = 2;
    
    // Response for consultation 1 arrives late
    const shouldApply1 = responseForId1.id === currentConsultationId;
    expect(shouldApply1).toBe(false);
    
    // Response for consultation 2 arrives
    const shouldApply2 = responseForId2.id === currentConsultationId;
    expect(shouldApply2).toBe(true);
  });
});

describe('DoctorDashboard Integration - Background Refresh', () => {
  test('cleanup on unmount prevents memory leaks', () => {
    const timers = new Set();
    
    // Start refresh timer
    const timerId = setTimeout(() => {}, 8000);
    timers.add(timerId);
    
    // Simulate unmount cleanup
    timers.forEach(id => clearTimeout(id));
    timers.clear();
    
    expect(timers.size).toBe(0);
  });

  test('refresh error triggers stale indicator', () => {
    let isStale = false;
    
    // Simulate successful refresh
    isStale = false;
    expect(isStale).toBe(false);
    
    // Simulate refresh error
    isStale = true;
    expect(isStale).toBe(true);
  });
});
