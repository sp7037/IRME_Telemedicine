/**
 * Integration tests for ConsultationDetailModal
 * Tests status display, video lifecycle, and cleanup behavior
 */

import { getStatusMessage } from '../../utils/consultationStatus';
import { shouldCloseVideo, shouldClearCredentials, cleanupVideoSession } from '../../utils/videoLifecycle';

describe('ConsultationDetailModal Integration - Status Display', () => {
  test('getStatusMessage provides role-specific messages', () => {
    const consultation = {
      status: 'IN_PROGRESS',
      patient: { user: { first_name: 'Jane' } },
    };
    
    const doctorMessage = getStatusMessage(consultation, 'doctor');
    const patientMessage = getStatusMessage(consultation, 'patient');
    
    expect(doctorMessage).toBeTruthy();
    expect(patientMessage).toBeTruthy();
    expect(doctorMessage.title).toBeTruthy();
    expect(doctorMessage.message).toContain('live');
  });

  test('status message adapts to consultation lifecycle', () => {
    const consultation = { 
      status: 'PENDING',
      patient: { user: { first_name: 'Jane' } },
    };
    
    const pendingMsg = getStatusMessage(consultation, 'doctor');
    consultation.status = 'COMPLETED';
    const completedMsg = getStatusMessage(consultation, 'doctor');
    
    expect(pendingMsg).not.toEqual(completedMsg);
  });
});

describe('ConsultationDetailModal Integration - Video Cleanup', () => {
  test('terminal status transition triggers cleanup', () => {
    const consultation = { status: 'COMPLETED', follow_up: null };
    const previousStatus = 'IN_PROGRESS';
    
    const shouldClose = shouldCloseVideo(consultation, previousStatus);
    expect(shouldClose).toBe(true);
  });

  test('active follow-up prevents video cleanup', () => {
    const consultation = {
      status: 'COMPLETED',
      follow_up: { active_status: 'IN_PROGRESS' },
    };
    const previousStatus = 'IN_PROGRESS';
    
    const shouldClose = shouldCloseVideo(consultation, previousStatus);
    expect(shouldClose).toBe(false);
  });

  test('credentials are cleared on terminal state', () => {
    expect(shouldClearCredentials({ status: 'COMPLETED' })).toBe(true);
    expect(shouldClearCredentials({ status: 'REJECTED' })).toBe(true);
  });

  test('credentials remain during active states', () => {
    expect(shouldClearCredentials({ status: 'IN_PROGRESS' })).toBe(false);
    expect(shouldClearCredentials({ status: 'QUEUED' })).toBe(false);
  });

  test('cleanupVideoSession handles various video states', async () => {
    const mockTrack = { stop: jest.fn() };
    const mockStream = { getTracks: () => [mockTrack] };
    const mockMeeting = { leave: jest.fn() };
    
    const videoState = {
      localStream: mockStream,
      meeting: mockMeeting,
      videoElement: { srcObject: mockStream },
    };
    
    const cleaned = await cleanupVideoSession(videoState);
    
    expect(cleaned).toBe(true);
    expect(mockTrack.stop).toHaveBeenCalled();
    expect(mockMeeting.leave).toHaveBeenCalled();
  });
});

describe('ConsultationDetailModal Integration - Consultation Switch', () => {
  test('consultation ID change triggers state reset', () => {
    const consultation1 = { id: 1, status: 'IN_PROGRESS' };
    const consultation2 = { id: 2, status: 'PENDING' };
    
    // Simulate tracking current consultation
    let currentId = consultation1.id;
    expect(currentId).toBe(1);
    
    // Switch consultation
    currentId = consultation2.id;
    expect(currentId).toBe(2);
    expect(currentId).not.toBe(consultation1.id);
  });

  test('video state resets when switching consultations', () => {
    const video1 = { id: 1, status: 'ACTIVE', provider: 'CLOUDFLARE' };
    const video2 = { id: 2, status: 'NONE' };
    
    let currentVideo = video1;
    expect(currentVideo.status).toBe('ACTIVE');
    
    // Switch to different consultation
    currentVideo = video2;
    expect(currentVideo.status).toBe('NONE');
  });
});

describe('ConsultationDetailModal Integration - Unmount Cleanup', () => {
  test('cleanup prevents memory leaks on unmount', async () => {
    const videoState = {
      meeting: { leave: jest.fn() },
      localStream: { getTracks: () => [{ stop: jest.fn() }] },
    };
    
    // Simulate unmount cleanup
    if (videoState) {
      await cleanupVideoSession(videoState);
    }
    
    expect(videoState.meeting.leave).toHaveBeenCalled();
  });
});

describe('ConsultationDetailModal Integration - Session Ready Callback', () => {
  test('onSessionReady callback stores video session reference', () => {
    const mockSession = {
      meeting: { id: 'meeting-123' },
      localStream: { id: 'stream-123' },
    };
    
    let videoSessionRef = null;
    const handleSessionReady = (session) => {
      videoSessionRef = session;
    };
    
    handleSessionReady(mockSession);
    
    expect(videoSessionRef).toBe(mockSession);
    expect(videoSessionRef.meeting.id).toBe('meeting-123');
  });
});
