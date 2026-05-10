import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Briefcase, FileSearch, ShieldCheck, Boxes } from "lucide-react";
import { useOfficer } from "@/contexts/OfficerContext";
import { getCases } from "@/services/api";
import type { Case } from "@/types";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge, PriorityBadge } from "@/components/ui/StatusBadges";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — AIVENTRA" },
      { name: "description", content: "Officer workspace: active investigations, recent activity, and case insights." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const { currentOfficer } = useOfficer();
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCases().then((c) => { setCases(c); setLoading(false); });
  }, []);

  const mine = cases.filter((c) => c.officer === currentOfficer.id);
  const stats = {
    active: mine.filter((c) => c.status === "Active").length,
    review: mine.filter((c) => c.status === "Under Review").length,
    closed: mine.filter((c) => c.status === "Closed").length,
    modules: mine.reduce((acc, c) => acc + c.evidenceModules.length, 0),
  };
  const recent = [...mine].sort((a, b) => +new Date(b.lastUpdated) - +new Date(a.lastUpdated)).slice(0, 4);

  return (
    <div className="px-6 py-8 max-w-7xl mx-auto space-y-8">
      <section>
        <p className="text-xs uppercase tracking-widest text-muted-foreground">Officer Workspace</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">Welcome back, {currentOfficer.name.split(" ")[0]}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {currentOfficer.unit} • Badge {currentOfficer.badge}
        </p>
      </section>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Briefcase} title="Active Investigations" value={loading ? "…" : stats.active} accent="primary" />
        <StatCard icon={FileSearch} title="Under Review" value={loading ? "…" : stats.review} accent="warning" />
        <StatCard icon={Boxes} title="Evidence Modules" value={loading ? "…" : stats.modules} accent="info" />
        <StatCard icon={ShieldCheck} title="Resolved Cases" value={loading ? "…" : stats.closed} accent="success" />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-lg border border-border bg-card">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <h2 className="text-sm font-semibold">Recent Cases</h2>
            <Link to="/cases" className="text-xs text-primary hover:underline">View all</Link>
          </div>
          <div className="divide-y divide-border">
            {loading && <div className="p-5 text-sm text-muted-foreground">Loading…</div>}
            {!loading && recent.length === 0 && (
              <div className="p-5 text-sm text-muted-foreground">No cases assigned.</div>
            )}
            {recent.map((c) => (
              <Link key={c.id} to="/case/$caseId" params={{ caseId: c.id }} className="grid grid-cols-12 items-center gap-3 px-5 py-3 hover:bg-accent/50 transition-colors">
                <div className="col-span-3 text-xs font-mono text-muted-foreground">{c.id}</div>
                <div className="col-span-4">
                  <p className="text-sm font-medium">{c.victim}</p>
                  <p className="text-xs text-muted-foreground">{c.location}</p>
                </div>
                <div className="col-span-2 text-xs text-muted-foreground">{c.date}</div>
                <div className="col-span-3 flex flex-wrap justify-end gap-1.5">
                  <PriorityBadge priority={c.priority} />
                  <StatusBadge status={c.status} />
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-sm font-semibold">Recent Activity</h2>
          </div>
          <ul className="px-5 py-4 space-y-4 text-sm">
            <ActivityItem label="Autopsy report extracted" detail="AIV-0041 • 12 min ago" />
            <ActivityItem label="CCTV anomaly flagged" detail="AIV-0044 • 1 h ago" />
            <ActivityItem label="Mobile metadata processed" detail="AIV-0046 • 3 h ago" />
            <ActivityItem label="Case correlation updated" detail="AIV-0048 • 5 h ago" />
          </ul>
        </div>
      </section>
    </div>
  );
}

function ActivityItem({ label, detail }: { label: string; detail: string }) {
  return (
    <li className="flex items-start gap-3">
      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
      <div>
        <p className="font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{detail}</p>
      </div>
    </li>
  );
}
