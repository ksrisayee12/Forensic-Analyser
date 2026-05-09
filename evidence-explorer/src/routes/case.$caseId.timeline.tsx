import { createFileRoute, useParams } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { getTimelineEvents } from "@/services/api";
import type { EvidenceEvent, EvidenceSource } from "@/types";
import { Video, MapPin, Smartphone, Users, Microscope, AlertTriangle } from "lucide-react";

const sourceMeta: Record<EvidenceSource, { icon: typeof Video; color: string }> = {
  CCTV: { icon: Video, color: "text-info" },
  GPS: { icon: MapPin, color: "text-success" },
  MOBILE: { icon: Smartphone, color: "text-warning" },
  WITNESS: { icon: Users, color: "text-primary" },
  AUTOPSY: { icon: Microscope, color: "text-destructive" },
};

export const Route = createFileRoute("/case/$caseId/timeline")({
  component: TimelinePage,
});

function TimelinePage() {
  const { caseId } = useParams({ from: "/case/$caseId/timeline" });
  const [events, setEvents] = useState<EvidenceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"All" | EvidenceSource>("All");

  useEffect(() => { getTimelineEvents(caseId).then((e) => { setEvents(e); setLoading(false); }); }, [caseId]);

  const sorted = useMemo(
    () => [...events].sort((a, b) => +new Date(a.time) - +new Date(b.time))
      .filter((e) => filter === "All" || e.source === filter),
    [events, filter]
  );

  return (
    <div className="px-6 py-8 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        {(["All", "CCTV", "GPS", "MOBILE", "WITNESS", "AUTOPSY"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
              filter === f ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:text-foreground"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-muted-foreground">Loading timeline…</p>}
      {!loading && sorted.length === 0 && <p className="text-sm text-muted-foreground">No events available.</p>}

      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />
        <ul className="space-y-4">
          {sorted.map((evt) => {
            const meta = sourceMeta[evt.source];
            const Icon = meta.icon;
            return (
              <li key={evt.id} className="relative pl-12">
                <span className={`absolute left-0 top-3 flex h-8 w-8 items-center justify-center rounded-full border border-border bg-card ${meta.color}`}>
                  <Icon className="h-4 w-4" />
                </span>
                <div className={`rounded-lg border bg-card p-4 transition-colors ${evt.isAnomaly ? "border-destructive/40" : "border-border"}`}>
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-mono text-muted-foreground">{new Date(evt.time).toLocaleString()}</span>
                      <span className={`rounded border border-border px-1.5 py-0.5 ${meta.color}`}>{evt.source}</span>
                      {evt.isAnomaly && (
                        <span className="inline-flex items-center gap-1 rounded border border-destructive/30 bg-destructive/10 px-1.5 py-0.5 text-destructive">
                          <AlertTriangle className="h-3 w-3" /> anomaly
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">{evt.confidence}% confidence</span>
                  </div>
                  <p className="mt-2 text-sm">{evt.description}</p>
                  <div className="mt-2 h-1 rounded-full bg-muted overflow-hidden">
                    <div className={`h-full ${evt.isAnomaly ? "bg-destructive" : "bg-primary"}`} style={{ width: `${evt.confidence}%` }} />
                  </div>
                  {evt.linkedEvents && evt.linkedEvents.length > 0 && (
                    <p className="mt-2 text-[11px] text-muted-foreground">Linked: {evt.linkedEvents.join(", ")}</p>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
