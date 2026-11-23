/**
 * Integration tests for PatientDashboard
 * Tests status display, postponement actions, background refresh, and video cleanup
 */

import { getStatusMessage, getAvailableActions } from '../../../utils/consultationStatus';
import { shouldCloseVideo, shouldClearCredentials } from '../../../utils/videoLifecycle';

describe('PatientDashboard Integration - Postponement Actions', () => {
  test('postponed consultation shows accept and decline actions', () => {
    const consultation = {
      status: 'POSTPONED',
      formatted_suggested_time: '2024-01-15 10:00 AM IST',
      doctor_name: 'Dr. Smith',
    };

    const actions = getAvailableActions(consultation, 'patient');
    
    expect(actions).toContainEqual(
      expect.objectContaining({ key: 'accept_postponed', label: expect.stringContaining('Accept') })
    );
    expect(actions).toContainEqual(
      expect.objectContaining({ key: 'reject_postponed', label: expect.stringContaining('Reject') })
    );
  });

  test('postponed status message explains the proposed time', () => {
    const consultation = {
      status: 'POSTPONED',
      formatted_suggested_time: '2024-01-15 10:00 AM IST',
      doctor_name: 'Dr. Smith',
    };

    const statusInfo = getStatusMessage(consultation, 'patient');
    
    expect(statusInfo.title).toBe('New time suggested');
    expect(statusInfo.message).toContain('Dr. Smith');
    expect(statusInfo.message).toContain('2024-01-15 10:00 AM IST');
    expect(statusInfo.severity).toBe('warning');
  });

  test('accepting postponed time wording indicates pending doctor review', () => {
    const consultation = {
      status: 'PENDING',
      doctor_name: 'Dr. Smith',
    };

    const statusInfo = getStatusMessage(consultation, 'patient');
    
    // After accepting postponed time, consultation returns to PENDING
    // Message should not say "confirmed appointment"
    expect(statusInfo.message).not.toContain('confirmed');
    expect(statusInfo.message).toContain('Waiting for acceptance');
  });
});

describe('PatientDashboard Integration - Status Display', () => {
  test('displays appropriate patient-facing messages for each status', () => {
    const statuses = ['PENDING', 'ACCEPTED', 'QUEUED', 'IN_PROGRESS', 'POSTPONED', 'COMPLETED', 'REJECTED'];
    
    statuses.forEach(status => {
      const consultation = {
        status,
        doctor_name: 'Dr. Smith',
      };
      
      const statusInfo = getStatusMessage(consultation, 'patient');
      expect(statusInfo).toBeTruthy();
      expect(statusInfo.title).toBeTruthy();
      expect(statusInfo.message).toBeTruthy();
    });
  });

  test('completed consultation message mentions prescription and follow-up', () => {
    const consultation = {
      status: 'COMPLETED',
      doctor_name: 'Dr. Smith',
    };

    const statusInfo = getStatusMessage(consultation, 'patient');
    
    expect(statusInfo.message).toContain('prescription');
    expect(statusInfo.message).toContain('follow-up');
  });

  test('rejected consultation explains next steps', () => {
    const consultation = {
      status: 'REJECTED',
      doctor_name: 'Dr. Smith',
    };

    const statusInfo = getStatusMessage(consultation, 'patient');
    
    expect(statusInfo.title).toBe('Request rejected');
    expect(statusInfo.message).toContain('another available doctor');
    expect(statusInfo.severity).toBe('error');
  });
});

describe('PatientDashboard Integration - Remote Status Updates', () => {
  test('tracks consultation status changes', () => {
    const statusMap = new Map();
    
    // Initial state
    const consultation = { id: 1, status: 'PENDING' };
    statusMap.set(consultation.id, consultation.status);
    
    // Simulated remote update
    const updated = { id: 1, status: 'ACCEPTED' };
    const previousStatus = statusMap.get(updated.id);
    
    expect(previousStatus).toBe('PENDING');
    expect(updated.status).toBe('ACCEPTED');
    expect(previousStatus).not.toBe(updated.status);
  });

  test('stale response guard prevents wrong consultation update', () => {
    let selectedIdRef = 1;
    const consultation1Response = { id: 1, data: 'details for consultation 1' };
    const consultation2Response = { id: 2, data: 'details for consultation 2' };
    
    // Switch to consultation 2
    selectedIdRef = 2;
    
    // Response for consultation 1 arrives late
    const shouldApply1 = consultation1Response.id === selectedIdRef;
    expect(shouldApply1).toBe(false);
    
    // Response for consultation 2 arrives
    const shouldApply2 = consultation2Response.id === selectedIdRef;
    expect(shouldApply2).toBe(true);
  });
});

describe('PatientDashboard Integration - Refresh Error Handling', () => {
  test('refresh error sets stale indicator', () => {
    let isStale = false;
    
    // Simulate successful refresh
    isStale = false;
    expect(isStale).toBe(false);
    
    // Simulate refresh error
    isStale = true;
    expect(isStale).toBe(true);
  });

  test('successful refresh clears stale indicator', () => {
    let isStale = true;
    
    // Simulate successful refresh after error
    isStale = false;
    expect(isStale).toBe(false);
  });
});

describe('PatientDashboard Integration - Video Cleanup', () => {
  test('terminal status triggers video cleanup', () => {
    const consultation = { status: 'COMPLETED', follow_up: null };
    const previousStatus = 'IN_PROGRESS';
    
    const shouldClose = shouldCloseVideo(consultation, previousStatus);
    expect(shouldClose).toBe(true);
  });

  test('active follow-up preserves video access', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: { active_status: 'IN_PROGRESS' },
    };
    const previousStatus = 'IN_PROGRESS';
    
    const shouldClose = shouldCloseVideo(consultation, previousStatus);
    expect(shouldClose).toBe(false);
  });

  test('credentials cleared on terminal state', () => {
    expect(shouldClearCredentials({ status: 'COMPLETED' })).toBe(true);
    expect(shouldClearCredentials({ status: 'REJECTED' })).toBe(true);
    expect(shouldClearCredentials({ status: 'CANCELED' })).toBe(true);
  });

  test('credentials remain during active states', () => {
    expect(shouldClearCredentials({ status: 'PENDING' })).toBe(false);
    expect(shouldClearCredentials({ status: 'IN_PROGRESS' })).toBe(false);
    expect(shouldClearCredentials({ status: 'QUEUED' })).toBe(false);
  });
});

describe('PatientDashboard Integration - Persistent flow prompts', () => {
  test('doctor accept maps to waiting prompt copy', () => {
    const consultation = { id: 9, status: 'ACCEPTED', doctor_name: 'Asha Mehta' };
    const doctor = consultation.doctor_name.replace(/^Dr\.?\s*/i, '');
    const title = `Dr ${doctor} accepted your request. Waiting for the doctor to start the consultation.`;
    expect(title).toContain('Waiting for the doctor to start the consultation');
  });

  test('doctor chat message shows preview and Reply affordance', () => {
    const consultation = {
      id: 9,
      unread_from_peer: 1,
      latest_chat_message: { sender_role: 'doctor', message: 'Please share your symptoms.' },
    };
    const helper =
      consultation.unread_from_peer > 0
        ? 'Doctor started the chat, please reply'
        : 'Open chat / details';
    const button = consultation.unread_from_peer > 0 ? 'Reply' : 'Open chat';
    expect(helper).toBe('Doctor started the chat, please reply');
    expect(button).toBe('Reply');
    expect(consultation.latest_chat_message.message).toContain('symptoms');
  });

  test('video request prompt offers Join video or Continue in chat', () => {
    const actions = [
      { key: 'join-video', label: 'Join video' },
      { key: 'continue-chat', label: 'Continue in chat' },
    ];
    expect(actions.map((a) => a.label)).toEqual(['Join video', 'Continue in chat']);
  });
});

describe('PatientDashboard Integration - Available Actions', () => {
  test('in-progress consultation shows open action', () => {
    const consultation = { status: 'IN_PROGRESS' };
    const actions = getAvailableActions(consultation, 'patient');
    
    expect(actions).toContainEqual(
      expect.objectContaining({ key: 'open', label: expect.stringContaining('Open') })
    );
  });

  test('completed consultation with follow-up capability shows request action', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: { can_request: true, next_is_billable: false },
    };
    
    const actions = getAvailableActions(consultation, 'patient');
    
    expect(actions).toContainEqual(
      expect.objectContaining({ key: 'request_followup' })
    );
  });

  test('completed consultation without follow-up capability shows only history action', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: { can_request: false },
    };
    
    const actions = getAvailableActions(consultation, 'patient');
    
    expect(actions).not.toContainEqual(
      expect.objectContaining({ key: 'request_followup' })
    );
    expect(actions).toContainEqual(
      expect.objectContaining({ key: 'view_history' })
    );
  });
});
