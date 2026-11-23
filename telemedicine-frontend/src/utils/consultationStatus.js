/**
 * Shared consultation status utilities for consistent presentation
 * across doctor, patient, and TMC dashboards.
 */

/**
 * Get user-friendly status label
 */
export const getStatusLabel = (status) => {
  const labels = {
    PENDING: "Pending",
    ACCEPTED: "Accepted",
    QUEUED: "In Queue",
    IN_PROGRESS: "In Progress",
    POSTPONED: "Postponed",
    COMPLETED: "Completed",
    REJECTED: "Rejected",
    REJECTED_BY_PATIENT: "Rejected by Patient",
    CANCELED: "Canceled",
  };
  return labels[status] || status || "Unknown";
};

/**
 * Get consultation status message for the given role
 * @param {Object} consultation - Consultation object with status, doctor_name, etc.
 * @param {string} role - 'doctor' | 'patient' | 'tmc'
 * @returns {Object|null} - {title, message, severity} or null
 */
export const getStatusMessage = (consultation, role = "patient") => {
  if (!consultation || !consultation.status) return null;

  const status = consultation.status;
  const doctorName = consultation.doctor_name || "the doctor";
  const patientName = consultation.patient_name || "the patient";
  const queueNumber = consultation.queue_number;

  if (role === "doctor") {
    if (status === "PENDING") {
      return {
        title: "New request waiting",
        message: `${patientName} is waiting for your decision. Accept, reject, or suggest another time.`,
        severity: "urgent",
      };
    }
    if (status === "ACCEPTED" || status === "QUEUED") {
      return {
        title: "Accepted",
        message: queueNumber
          ? `${patientName} is in your queue at position ${queueNumber}.`
          : `${patientName} is accepted. Start the consultation when ready.`,
        severity: "info",
      };
    }
    if (status === "IN_PROGRESS") {
      return {
        title: "Consultation active",
        message: `Session with ${patientName} is live. Chat and video are available.`,
        severity: "success",
      };
    }
    if (status === "POSTPONED") {
      return {
        title: "New time suggested",
        message: `You proposed ${consultation.formatted_suggested_time || "a new time"}. Waiting for ${patientName} to accept or reject.`,
        severity: "info",
      };
    }
    if (status === "COMPLETED") {
      return {
        title: "Completed",
        message: `Consultation with ${patientName} is marked complete. Prescription and history remain available.`,
        severity: "success",
      };
    }
    if (status === "REJECTED" || status === "REJECTED_BY_PATIENT") {
      return {
        title: "Request rejected",
        message: status === "REJECTED_BY_PATIENT"
          ? `${patientName} rejected the proposed time.`
          : `You rejected ${patientName}'s request.`,
        severity: "warning",
      };
    }
  }

  if (role === "patient") {
    if (status === "PENDING") {
      return {
        title: "Request sent",
        message: `Your consultation request was sent to ${doctorName}. Waiting for acceptance, rejection, or a suggested alternate time.`,
        severity: "info",
      };
    }
    if (status === "ACCEPTED") {
      return {
        title: "Request accepted",
        message: `${doctorName} accepted your request. Please stay ready while the doctor starts the session.`,
        severity: "success",
      };
    }
    if (status === "QUEUED") {
      return {
        title: "In queue",
        message: queueNumber
          ? `${doctorName} accepted your request. You are at queue position ${queueNumber}.`
          : `${doctorName} accepted your request. You are in the consultation queue.`,
        severity: "success",
      };
    }
    if (status === "IN_PROGRESS") {
      return {
        title: "Consultation started",
        message: `${doctorName} started the consultation. Open the chat/details panel to continue.`,
        severity: "success",
      };
    }
    if (status === "POSTPONED") {
      return {
        title: "New time suggested",
        message: `${doctorName} proposed ${consultation.formatted_suggested_time || "a new time"}. Please accept or reject this proposed schedule.`,
        severity: "warning",
      };
    }
    if (status === "COMPLETED") {
      return {
        title: "Consultation completed",
        message: `${doctorName} marked this consultation as completed. View prescription and history, or request a follow-up if needed.`,
        severity: "success",
      };
    }
    if (status === "REJECTED") {
      return {
        title: "Request rejected",
        message: `${doctorName} could not accept this consultation. You may request another available doctor.`,
        severity: "error",
      };
    }
    if (status === "REJECTED_BY_PATIENT") {
      return {
        title: "Proposed time rejected",
        message: `You rejected the time proposed by ${doctorName}. The consultation request is now closed.`,
        severity: "warning",
      };
    }
  }

  if (role === "tmc") {
    if (status === "PENDING") {
      return {
        title: "Request sent",
        message: `TMC consultation request sent to ${doctorName}. Waiting for doctor response.`,
        severity: "info",
      };
    }
    if (status === "ACCEPTED" || status === "QUEUED") {
      return {
        title: "Accepted",
        message: queueNumber
          ? `${doctorName} accepted. Queue position ${queueNumber}.`
          : `${doctorName} accepted the request.`,
        severity: "success",
      };
    }
    if (status === "IN_PROGRESS") {
      return {
        title: "In progress",
        message: `Consultation with ${doctorName} and ${patientName} is live.`,
        severity: "success",
      };
    }
    if (status === "POSTPONED") {
      return {
        title: "Time proposed",
        message: `${doctorName} suggested ${consultation.formatted_suggested_time || "a new time"}. The patient must respond.`,
        severity: "info",
      };
    }
    if (status === "COMPLETED") {
      return {
        title: "Completed",
        message: `Consultation between ${patientName} and ${doctorName} is complete.`,
        severity: "success",
      };
    }
    if (status === "REJECTED" || status === "REJECTED_BY_PATIENT") {
      return {
        title: "Rejected",
        message: status === "REJECTED_BY_PATIENT"
          ? `${patientName} rejected the proposed time.`
          : `${doctorName} rejected the request.`,
        severity: "warning",
      };
    }
  }

  return null;
};

/**
 * Get next actions available for the consultation
 * @param {Object} consultation
 * @param {string} role - 'doctor' | 'patient' | 'tmc'
 * @returns {Array<{key, label, variant}>}
 */
export const getAvailableActions = (consultation, role = "patient") => {
  if (!consultation) return [];

  const status = consultation.status;
  const actions = [];

  if (role === "doctor") {
    if (status === "PENDING") {
      actions.push(
        { key: "accept", label: "Accept request", variant: "primary" },
        { key: "reject", label: "Reject request", variant: "secondary" },
        { key: "postpone", label: "Suggest another time", variant: "warn" }
      );
    }
    if (status === "ACCEPTED" || status === "QUEUED") {
      actions.push({ key: "start", label: "Start consultation", variant: "primary" });
    }
    if (status === "IN_PROGRESS") {
      actions.push(
        { key: "open", label: "Open consultation", variant: "primary" },
        { key: "complete", label: "Mark completed", variant: "complete" }
      );
    }
    if (status === "COMPLETED") {
      actions.push({ key: "view_history", label: "View history", variant: "secondary" });
    }
    if (status === "POSTPONED") {
      actions.push({ key: "view_details", label: "View details", variant: "secondary" });
    }
  }

  if (role === "patient") {
    if (status === "POSTPONED") {
      actions.push(
        { key: "accept_postponed", label: "Accept new time", variant: "primary" },
        { key: "reject_postponed", label: "Reject new time", variant: "warn" }
      );
    }
    if (status === "ACCEPTED" || status === "QUEUED" || status === "IN_PROGRESS") {
      actions.push({ key: "open", label: "Open chat / details", variant: "primary" });
    }
    if (status === "COMPLETED") {
      const canFollowUp = consultation.follow_up?.can_request;
      const followUpActive = consultation.follow_up?.active_status === "IN_PROGRESS";
      actions.push({ key: "view_history", label: "Open history", variant: "secondary" });
      if (followUpActive) {
        actions.push({ key: "open_followup", label: "Resume chat", variant: "primary" });
      } else if (canFollowUp) {
        actions.push({
          key: "request_followup",
          label: consultation.follow_up?.next_is_billable ? "Request paid follow-up" : "Request follow-up",
          variant: "primary",
        });
      }
    }
    if (status === "PENDING") {
      actions.push({ key: "view_details", label: "View details", variant: "secondary" });
    }
  }

  if (role === "tmc") {
    if (status === "ACCEPTED" || status === "QUEUED" || status === "IN_PROGRESS" || status === "COMPLETED") {
      actions.push({ key: "open_chat", label: "Open chat", variant: "primary" });
    }
    if (status === "COMPLETED") {
      const canFollowUp = consultation.follow_up?.can_request;
      const followUpActive = consultation.follow_up?.active_status === "IN_PROGRESS";
      if (followUpActive) {
        actions.push({ key: "open_followup", label: "Resume follow-up", variant: "primary" });
      } else if (canFollowUp) {
        actions.push({
          key: "request_followup",
          label: consultation.follow_up?.next_is_billable ? "Request paid follow-up" : "Request follow-up",
          variant: "primary",
        });
      }
    }
    if (status === "PENDING" || status === "POSTPONED") {
      actions.push({ key: "view_timeline", label: "View timeline", variant: "secondary" });
    }
  }

  return actions;
};

/**
 * Check if consultation is in a terminal state
 */
export const isTerminalStatus = (status) => {
  return ["COMPLETED", "REJECTED", "REJECTED_BY_PATIENT", "CANCELED"].includes(status);
};

/**
 * Check if video/chat should be allowed
 */
export const canInteract = (status) => {
  return ["ACCEPTED", "QUEUED", "IN_PROGRESS"].includes(status);
};

/**
 * Get postponement explanation for patient or TMC
 */
export const getPostponementExplanation = (consultation) => {
  if (!consultation || consultation.status !== "POSTPONED") return null;

  return {
    title: "New time proposed",
    body: `The doctor suggested ${
      consultation.formatted_suggested_time || "a new time"
    }. Accepting this time returns the request to pending for the doctor's final acceptance. No second consultation charge will be taken. Rejecting closes the request with a full return of the consultation charge to the original payer.`,
  };
};

/**
 * Get follow-up status text
 */
export const getFollowUpStatus = (consultation) => {
  if (!consultation?.follow_up) return null;

  const status = consultation.follow_up.active_status;
  if (status === "PENDING") {
    return "Follow-up request sent. Waiting for doctor acceptance.";
  }
  if (status === "IN_PROGRESS") {
    return "Follow-up accepted. Chat is available.";
  }
  if (status === "REJECTED") {
    return "Follow-up request was rejected by the doctor.";
  }
  if (status === "COMPLETED") {
    return "Follow-up session completed.";
  }
  return null;
};
