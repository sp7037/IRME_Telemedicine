import React from "react";
import StatusBadge from "./StatusBadge";
import ConsultationTimeline from "./ConsultationTimeline";

const ConsultationDetailModal = ({ consultation, events, onClose, children }) => {
  if (!consultation) return null;
  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <h3 style={{ margin: 0, color: "#123a6f" }}>Consultation #{consultation.id}</h3>
          <button onClick={onClose} style={styles.close}>✕</button>
        </div>
        <div style={styles.infoGrid}>
          <p><strong>Doctor:</strong> {consultation.doctor_name}</p>
          <p><strong>Patient:</strong> {consultation.patient_name}</p>
          <p><strong>Type:</strong> {consultation.consultation_type}</p>
          <p><strong>Status:</strong> <StatusBadge status={consultation.status} /></p>
          {consultation.tmc_name ? <p><strong>TMC:</strong> {consultation.tmc_name}</p> : null}
        </div>
        {children}
        <h4 style={{ color: "#123a6f", marginBottom: 8 }}>Event Timeline</h4>
        <ConsultationTimeline events={events} />
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: "fixed", inset: 0, backgroundColor: "rgba(0,0,0,0.45)", zIndex: 1000,
    display: "grid", placeItems: "center",
  },
  modal: {
    width: "min(900px, 94vw)", maxHeight: "90vh", overflowY: "auto",
    background: "#fff", borderRadius: 16, padding: 20, border: "1px solid #d7e5f5",
    boxShadow: "0 10px 24px rgba(16, 36, 62, 0.2)",
  },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 },
  close: { border: "none", background: "transparent", fontSize: 18, cursor: "pointer" },
  infoGrid: {
    display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 8, marginBottom: 16,
    background: "#fbfdff", border: "1px solid #d7e5f5", borderRadius: 12, padding: 12,
  },
};

export default ConsultationDetailModal;
