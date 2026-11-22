import React from "react";
import { useTranslation } from "react-i18next";
import theme from "../../theme/tokens";

const StatusBadge = ({ status }) => {
  const { t } = useTranslation();
  const safe = (status || "").toUpperCase().replace(/_/g, "");
  
  const statusMap = {
    PENDING: "pending",
    ACCEPTED: "accepted",
    QUEUED: "queued",
    INPROGRESS: "inProgress",
    COMPLETED: "completed",
    REJECTED: "rejected",
    REJECTEDBYPATIENT: "rejected",
    POSTPONED: "postponed",
    CANCELED: "canceled",
  };

  const statusKey = statusMap[safe] || "pending";
  const color = theme.colors.status[statusKey] || theme.colors.status.pending;
  const label = t(`consultation.status.${statusKey}`, { defaultValue: status });

  return (
    <span
      style={{
        display: "inline-block",
        padding: `${theme.spacing[1]} ${theme.spacing[3]}`,
        borderRadius: theme.radii.full,
        fontSize: theme.typography.fontSize.xs,
        fontWeight: theme.typography.fontWeight.bold,
        backgroundColor: color.bg,
        color: color.fg,
      }}
    >
      {label}
    </span>
  );
};

export default StatusBadge;
