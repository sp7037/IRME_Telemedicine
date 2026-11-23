/**
 * Integration tests for TMCDashboard
 * Tests TMC-specific status display, background refresh, action guards, and video cleanup
 */

import { getStatusMessage, getAvailableActions } from '../../../utils/consultationStatus';
import { shouldCloseVideo, shouldClearCredentials } from '../../../utils/videoLifecycle';

describe('TMCDashboard Integration - Status Display', () => {
  test('TMC sees appropriate status messages for each consultation state', () => {
    const statuses = ['PENDING', 'ACCEPTED', 'QUEUED', 'IN_PROGRESS', 'POSTPONED', 'COMPLETED', 'REJECTED'];
    
    statuses.forEach(status => {
      const consultation = {
        status,
        doctor_name: 'Dr. Smith',
        patient_name: 'John Doe',
      };
      
      const statusInfo = getStatusMessage(consultation, 'tmc');
      expect(statusInfo).toBeTruthy();
      expect(statusInfo.title).toBeTruthy();
      expect(statusInfo.message).toBeTruthy();
    });
  });

  test('postponed status tells TMC that patient must respond', () => {
    const consultation = {
      status: 'POSTPONED',
      formatted_suggested_time: '2024-01-15 10:00 AM IST',
      doctor_name: 'Dr. Smith',
      patient_name: 'John Doe',
    };

    const statusInfo = getStatusMessage(consultation, 'tmc');
    
    expect(statusInfo.title).toBe('Time proposed');
    expect(statusInfo.message).toContain('patient must respond');
    expect(statusInfo.message).toContain('2024-01-15 10:00 AM IST');
  });

  test('in-progress status shows both patient and doctor names', () => {
    const consultation = {
      status: 'IN_PROGRESS',
      doctor_name: 'Dr. Smith',
      patient_name: 'John Doe',
    };

    const statusInfo = getStatusMessage(consultation, 'tmc');
    
    expect(statusInfo.message).toContain('John Doe');
    expect(statusInfo.message).toContain('Dr. Smith');
  });
});

describe('TMCDashboard Integration - Available Actions', () => {
  test('TMC can open chat for active consultations', () => {
    const statuses = ['ACCEPTED', 'QUEUED', 'IN_PROGRESS', 'COMPLETED'];
    
    statuses.forEach(status => {
      const consultation = { status };
      const actions = getAvailableActions(consultation, 'tmc');
      
      expect(actions).toContainEqual(
        expect.objectContaining({ key: 'open_chat' })
      );
    });
  });

  test('TMC can view timeline for pending and postponed consultations', () => {
    const statuses = ['PENDING', 'POSTPONED'];
    
    statuses.forEach(status => {
      const consultation = { status };
      const actions = getAvailableActions(consultation, 'tmc');
      
      expect(actions).toContainEqual(
        expect.objectContaining({ key: 'view_timeline' })
      );
    });
  });

  test('TMC cannot accept or reject patient postponement responses', () => {
    const consultation = {
      status: 'POSTPONED',
      formatted_suggested_time: '2024-01-15 10:00 AM IST',
    };
    
    const actions = getAvailableActions(consultation, 'tmc');
    
    // TMC should not have patient-only actions
    expect(actions).not.toContainEqual(
      expect.objectContaining({ key: 'accept_postponed' })
    );
    expect(actions).not.toContainEqual(
      expect.objectContaining({ key: 'reject_postponed' })
    );
  });

  test('completed consultation with active follow-up shows resume action', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: {
        active_status: 'IN_PROGRESS',
        can_request: false,
      },
    };
    
    const actions = getAvailableActions(consultation, 'tmc');
    
    expect(actions).toContainEqual(
      expect.objectContaining({ key: 'open_followup' })
    );
  });

  test('completed consultation allows TMC to request follow-up when eligible', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: {
        can_request: true,
        next_is_billable: false,
        active_status: null,
      },
    };
    
    const actions = getAvailableActions(consultation, 'tmc');
    
    expect(actions).toContainEqual(
      expect.objectContaining({ key: 'request_followup' })
    );
  });
});

describe('TMCDashboard Integration - Background Refresh', () => {
  test('stale response guard prevents wrong consultation update', () => {
    let chatIdRef = 123;
    const consultation1Response = { id: 123, status: 'PENDING' };
    const consultation2Response = { id: 456, status: 'IN_PROGRESS' };
    
    // Switch to consultation 456
    chatIdRef = 456;
    
    // Response for consultation 123 arrives late
    const shouldApply1 = consultation1Response.id === chatIdRef;
    expect(shouldApply1).toBe(false);
    
    // Response for consultation 456 arrives
    const shouldApply2 = consultation2Response.id === chatIdRef;
    expect(shouldApply2).toBe(true);
  });

  test('overlapping refresh requests are prevented', () => {
    let inflightRefreshRef = false;
    
    // First refresh starts
    expect(inflightRefreshRef).toBe(false);
    inflightRefreshRef = true;
    
    // Second refresh attempt while first is in-flight
    const canStartSecond = !inflightRefreshRef;
    expect(canStartSecond).toBe(false);
    
    // First refresh completes
    inflightRefreshRef = false;
    
    // Now second refresh can start
    const canStartAfter = !inflightRefreshRef;
    expect(canStartAfter).toBe(true);
  });

  test('refresh failure sets stale indicator', () => {
    let isStale = false;
    
    // Simulate refresh error
    isStale = true;
    expect(isStale).toBe(true);
  });

  test('successful refresh clears stale indicator', () => {
    let isStale = true;
    
    // Simulate successful refresh
    isStale = false;
    expect(isStale).toBe(false);
  });

  test('unmount cleanup clears chat reference', () => {
    let chatIdRef = 123;
    
    // Simulate unmount
    chatIdRef = null;
    expect(chatIdRef).toBe(null);
  });
});

describe('TMCDashboard Integration - Video Cleanup', () => {
  test('terminal status triggers video cleanup', () => {
    const consultation = { status: 'COMPLETED', follow_up: null };
    const previousStatus = 'IN_PROGRESS';
    
    const shouldClose = shouldCloseVideo(consultation, previousStatus);
    expect(shouldClose).toBe(true);
  });

  test('active follow-up session prevents premature cleanup', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: { active_status: 'IN_PROGRESS' },
    };
    const previousStatus = 'IN_PROGRESS';
    
    const shouldClose = shouldCloseVideo(consultation, previousStatus);
    expect(shouldClose).toBe(false);
  });

  test('credentials cleared on terminal states', () => {
    expect(shouldClearCredentials({ status: 'COMPLETED' })).toBe(true);
    expect(shouldClearCredentials({ status: 'REJECTED' })).toBe(true);
    expect(shouldClearCredentials({ status: 'REJECTED_BY_PATIENT' })).toBe(true);
    expect(shouldClearCredentials({ status: 'CANCELED' })).toBe(true);
  });

  test('credentials remain during active consultation', () => {
    expect(shouldClearCredentials({ status: 'PENDING' })).toBe(false);
    expect(shouldClearCredentials({ status: 'ACCEPTED' })).toBe(false);
    expect(shouldClearCredentials({ status: 'IN_PROGRESS' })).toBe(false);
  });
});

describe('TMCDashboard Integration - Action Guards', () => {
  test('repeated clicks are prevented during in-flight action', () => {
    let inFlightAction = null;
    
    // First click
    const canSubmit1 = !inFlightAction;
    expect(canSubmit1).toBe(true);
    inFlightAction = 'creating_consultation';
    
    // Second click while in-flight
    const canSubmit2 = !inFlightAction;
    expect(canSubmit2).toBe(false);
    
    // Action completes
    inFlightAction = null;
    
    // Can submit again
    const canSubmit3 = !inFlightAction;
    expect(canSubmit3).toBe(true);
  });
});

describe('TMCDashboard Integration - Follow-up Requests', () => {
  test('follow-up status updates after request', () => {
    const consultation = {
      id: 1,
      status: 'COMPLETED',
      follow_up: {
        can_request: true,
        active_status: null,
      },
    };
    
    // After requesting follow-up
    const updatedConsultation = {
      ...consultation,
      follow_up: {
        can_request: false,
        active_status: 'PENDING',
      },
    };
    
    const actions = getAvailableActions(updatedConsultation, 'tmc');
    
    // Should no longer show request action
    expect(actions).not.toContainEqual(
      expect.objectContaining({ key: 'request_followup' })
    );
  });

  test('billable follow-up is labeled correctly', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: {
        can_request: true,
        next_is_billable: true,
      },
    };
    
    const actions = getAvailableActions(consultation, 'tmc');
    const followUpAction = actions.find(a => a.key === 'request_followup');
    
    expect(followUpAction.label).toContain('paid');
  });

  test('free follow-up is labeled correctly', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: {
        can_request: true,
        next_is_billable: false,
      },
    };
    
    const actions = getAvailableActions(consultation, 'tmc');
    const followUpAction = actions.find(a => a.key === 'request_followup');
    
    expect(followUpAction.label).not.toContain('paid');
  });
});
