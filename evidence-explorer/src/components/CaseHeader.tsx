import { Link, useRouterState } from "@tanstack/react-router";
import type { Case } from "@/types";
import { StatusBadge, PriorityBadge } from "@/components/ui/StatusBadges";

interface Props {
  caseData: Case;
}

const tabs = [
  { key: "overview", label: "Overview", to: (id: string) => `/case/${id}` },
  { key: "autopsy", label: "Autopsy Analysis", to: (id: string) => `/case/${id}/autopsy` },
  { key: "timeline", label: "Evidence Timeline", to: (id: string) => `/case/${id}/timeline` },
  { key: "correlation", label: "Correlation Graph", to: (id: string) => `/case/${id}/correlation` },
];

export function CaseHeader({ caseData }: Props) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="border-b border-white/8 bg-card">
      <div className="px-6 pt-6 pb-0">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">{caseData.id}</p>
            <h2 className="mt-1.5 text-2xl font-semibold tracking-tight text-foreground">{caseData.victim}</h2>
            <p className="mt-1 text-[13px] text-muted-foreground font-medium">
              {caseData.location ?? "Location withheld"} &nbsp;·&nbsp; {caseData.date}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="flex gap-2">
              <StatusBadge status={caseData.status} />
              <PriorityBadge priority={caseData.priority} />
            </div>
            <p className="text-[12px] text-muted-foreground font-medium">
              {caseData.investigator} &nbsp;·&nbsp; {caseData.unit}
            </p>
          </div>
        </div>

        <nav className="mt-5 flex flex-wrap gap-0">
          {tabs.map((t) => {
            const to = t.to(caseData.id);
            const active = pathname === to;
            return (
              <Link
                key={t.key}
                to={to}
                className={`relative px-4 py-3 text-[13px] font-medium tracking-wide transition-colors border-b-2 ${
                  active
                    ? "border-primary text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                {t.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
