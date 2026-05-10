import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { getCases } from "@/services/api";
import type { Case, CaseStatus, CasePriority } from "@/types";
import { Input } from "@/components/ui/input";
import { Search, MapPin, Clock } from "lucide-react";
import { StatusBadge, PriorityBadge } from "@/components/ui/StatusBadges";
import { EvidenceTag } from "@/components/ui/EvidenceTag";
import { InitializeCaseDialog } from "@/components/InitializeCaseDialog";

export const Route = createFileRoute("/cases")({
  head: () => ({
    meta: [
      { title: "Cases — AIVENTRA" },
      { name: "description", content: "Investigation registry: filter, search, and open active cases." },
    ],
  }),
  component: CasesPage,
});

function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<"All" | CaseStatus>("All");
  const [priority, setPriority] = useState<"All" | CasePriority>("All");
  const [query, setQuery] = useState("");

  useEffect(() => { getCases().then((c) => { setCases(c); setLoading(false); }); }, []);

  const filtered = useMemo(() => {
    return cases.filter((c) => {
      if (status !== "All" && c.status !== status) return false;
      if (priority !== "All" && c.priority !== priority) return false;
      if (query) {
        const q = query.toLowerCase();
        if (!c.id.toLowerCase().includes(q) && !c.victim.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [cases, status, priority, query]);

  return (
    <div className="px-6 py-8 max-w-5xl mx-auto space-y-7">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground/40">Registry</p>
          <h1 className="mt-1 text-2xl font-light tracking-tight text-foreground/90">All Investigations</h1>
        </div>
        <InitializeCaseDialog />
      </div>

      {/* Filters */}
      <div
        className="rounded-xl border border-white/5 p-4 flex flex-wrap items-center gap-3"
        style={{ background: "linear-gradient(180deg, #111113 0%, #0e0e10 100%)" }}
      >
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/40" />
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by ID or victim…" className="pl-9 text-[13px] bg-transparent border-white/8 focus:border-primary/40 placeholder:text-muted-foreground/30" />
        </div>
        <Select label="Status" value={status} onChange={(v) => setStatus(v as never)} options={["All", "Active", "Under Review", "Closed"]} />
        <Select label="Priority" value={priority} onChange={(v) => setPriority(v as never)} options={["All", "Standard", "Elevated", "Critical Review"]} />
      </div>

      {/* Registry Count */}
      {!loading && (
        <p className="text-[11px] text-muted-foreground/40 data-mono">
          {filtered.length} record{filtered.length !== 1 ? "s" : ""} found
        </p>
      )}

      {/* Cases List */}
      {loading ? (
        <p className="text-[13px] text-muted-foreground/40">Loading registry…</p>
      ) : (
        <div className="flex flex-col gap-px border border-white/5 rounded-xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.25)]">
          {filtered.map((c, idx) => (
            <Link
              key={c.id}
              to="/case/$caseId"
              params={{ caseId: c.id }}
              className={`group flex flex-col md:flex-row md:items-center justify-between gap-4 px-5 py-4 transition-all duration-150
                hover:bg-white/[0.03] border-b border-white/5 last:border-b-0
                ${idx === 0 ? "rounded-t-xl" : ""} ${idx === filtered.length - 1 ? "rounded-b-xl" : ""}
              `}
              style={{ background: "#0e0e11" }}
            >
              {/* ID + Name */}
              <div className="md:w-1/4 shrink-0">
                <p className="data-mono text-[10px] tracking-[0.15em] text-muted-foreground/40 uppercase">{c.id}</p>
                <h3 className="mt-0.5 text-[14px] font-medium text-foreground/80 group-hover:text-foreground transition-colors truncate">{c.victim}</h3>
              </div>

              {/* Meta */}
              <div className="md:w-1/4 text-[12px] text-muted-foreground/40 space-y-1 shrink-0">
                <div className="flex items-center gap-1.5"><MapPin className="h-3 w-3 shrink-0" /> <span className="truncate">{c.location}</span></div>
                <div className="flex items-center gap-1.5"><Clock className="h-3 w-3 shrink-0" /> {c.date}</div>
              </div>

              {/* Evidence Tags */}
              <div className="flex-1 flex flex-wrap gap-1.5 min-w-[100px]">
                {c.evidenceModules.slice(0, 3).map((m) => <EvidenceTag key={m} module={m} />)}
                {c.evidenceModules.length > 3 && (
                  <span className="text-[10px] text-muted-foreground/30 self-center data-mono">+{c.evidenceModules.length - 3}</span>
                )}
              </div>

              {/* Status */}
              <div className="md:w-1/5 flex flex-wrap md:flex-col items-start md:items-end justify-end gap-2 shrink-0">
                <div className="flex gap-2">
                  <StatusBadge status={c.status} />
                  <PriorityBadge priority={c.priority} />
                </div>
                <span className="text-[11px] text-muted-foreground/35 font-medium">{c.investigator}</span>
              </div>
            </Link>
          ))}
          {filtered.length === 0 && (
            <p className="py-10 text-center text-[13px] text-muted-foreground/30">No cases match the current filters.</p>
          )}
        </div>
      )}
    </div>
  );
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <label className="flex items-center gap-2 text-[12px] text-muted-foreground/50">
      {label}:
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-white/8 bg-transparent px-2 py-1.5 text-[12px] text-foreground/70 focus:outline-none focus:border-primary/40 transition-colors"
      >
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}
