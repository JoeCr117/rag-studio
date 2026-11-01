import type { AssignmentStatus } from "@/lib/api";
import { STATUS_HINTS, STATUS_LABELS } from "@/lib/status";

import { Explained } from "./Explained";

export function StatusPill({ status, prefix }: { status: AssignmentStatus; prefix?: string }) {
  return (
    <Explained note="Sync status" detail={STATUS_HINTS[status]} asChild>
      <span className={`pill status-${status}`}>
        {prefix ? `${prefix}: ` : ""}
        {STATUS_LABELS[status]}
      </span>
    </Explained>
  );
}
