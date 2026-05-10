import { createFileRoute, useParams } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { getAutopsyData } from "@/services/api";
import type { AutopsyExtraction } from "@/types";
import { Skull, AlertTriangle, FlaskConical } from "lucide-react";

export const Route = createFileRoute("/case/$caseId/autopsy")({
  component: AutopsyPage,
});

function AutopsyPage() {
  const { caseId } = useParams({ from: "/case/$caseId/autopsy" });
  const [data, setData] = useState<AutopsyExtraction | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { getAutopsyData(caseId).then((d) => { setData(d); setLoading(false); }); }, [caseId]);

  if (loading) return <div className="p-8 text-sm text-muted-foreground">Loading autopsy report…</div>;
  if (!data) return <div className="p-8 text-sm text-muted-foreground">No autopsy data available for this case.</div>;

  const susColor =
    data.suspicionLevel === "HIGH" ? "text-destructive bg-destructive/10 border-destructive/30" :
    data.suspicionLevel === "MEDIUM" ? "text-warning bg-warning/10 border-warning/30" :
    "text-success bg-success/10 border-success/30";

  return (
    <div className="px-6 py-8 max-w-6xl mx-auto space-y-6">
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-muted-foreground">Cause of Death</p>
            <h2 className="mt-2 text-2xl font-semibold flex items-center gap-2"><Skull className="h-6 w-6 text-primary" />{data.causeOfDeath}</h2>
          </div>
          <span className={`rounded-md border px-3 py-1.5 text-xs font-semibold ${susColor}`}>
            Suspicion: {data.suspicionLevel}
          </span>
        </div>
        <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <Pair label="Estimated Trauma Time" value={data.estimatedTraumaTime} />
          <Pair label="Toxicology" value={data.toxicology} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="text-sm font-semibold mb-3">Documented Injuries</h3>
          <ul className="space-y-2 text-sm">
            {data.injuries.map((i) => (
              <li key={i} className="flex gap-2"><span className="text-destructive">•</span>{i}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="text-sm font-semibold mb-3 inline-flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-warning" />Abnormal Observations</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">{data.abnormalObservations}</p>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h3 className="text-sm font-semibold inline-flex items-center gap-2"><FlaskConical className="h-4 w-4 text-primary" />Raw Examiner Report</h3>
        </div>
        <pre className="px-5 py-4 text-xs leading-relaxed font-mono whitespace-pre-wrap text-muted-foreground max-h-96 overflow-auto">
{data.rawReport}
        </pre>
      </div>
    </div>
  );
}

function Pair({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-widest text-muted-foreground">{label}</p>
      <p className="mt-1">{value}</p>
    </div>
  );
}
