import type { CaseStatus, CasePriority } from "@/types";

export function StatusBadge({ status }: { status: CaseStatus }) {
  const map: Record<CaseStatus, string> = {
    Active: "text-[#3b82f6] border-[#3b82f6]/20 bg-[#3b82f6]/5",
    "Under Review": "text-[#b45309] border-[#b45309]/20 bg-[#b45309]/5",
    Closed: "text-foreground/30 border-white/5 bg-white/2",
  };
  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-medium tracking-wide uppercase ${map[status]}`}>
      {status}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: CasePriority }) {
  const map: Record<CasePriority, string> = {
    Standard: "text-foreground/30 border-white/5 bg-transparent",
    Elevated: "text-[#b45309] border-[#b45309]/20 bg-[#b45309]/5",
    "Critical Review": "text-[#991b1b] border-[#991b1b]/20 bg-[#991b1b]/5",
  };
  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-medium tracking-wide uppercase ${map[priority]}`}>
      {priority}
    </span>
  );
}
