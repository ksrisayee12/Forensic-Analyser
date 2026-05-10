import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { Sparkles, AlertTriangle, ShieldCheck, Clock } from "lucide-react";
import { evidenceMeta } from "@/components/ui/EvidenceTag";

export const Route = createFileRoute("/case/$caseId/")({
  component: CaseOverview,
});

const parentRouteApi = getRouteApi("/case/$caseId");

function CaseOverview() {
  const { caseData } = parentRouteApi.useLoaderData();

  return (
    <div className="px-6 py-8 max-w-5xl mx-auto space-y-6">
      {/* AI Intelligence Summary */}
      <div className="rounded-xl border border-white/8 p-6" style={{ background: "#0f0f14" }}>
        <div className="flex items-center gap-2 text-primary mb-4">
          <Sparkles className="h-4 w-4" />
          <p className="text-xs font-semibold uppercase tracking-[0.18em]">AI Intelligence Summary</p>
        </div>
        <p className="text-[15px] leading-relaxed text-foreground/90">
          Forensic and behavioural signals indicate a high-suspicion event window. Autopsy findings (94% confidence)
          align with witness statements and CCTV gait patterns. Mobile metadata shows an{" "}
          <span className="text-[#991b1b] font-semibold">anomalous deletion cluster</span> immediately preceding the
          incident, warranting elevated review.
        </p>
        <ul className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
          <Insight label="Cause of death" value={`${caseData.forensics?.causeOfDeath ?? "Pending analysis"} (87% confidence)`} />
          <Insight label="CCTV anomaly" value="Rear-entry breach detected (78%)" />
          <Insight label="Phone activity" value="Cluster of late-night calls (88%)" warn />
          <Insight label="Witness corroboration" value="Two independent accounts" />
        </ul>
      </div>

      <div className="flex flex-col gap-5">
        {/* Key Findings */}
        <Card title="Key Findings">
          <div className="flex flex-col sm:flex-row gap-8">
            <div className="flex-1 space-y-5">
              <Meter label="Autopsy confidence" value={94} />
              <Meter label="Evidence reliability" value={81} />
              <Meter label="Timeline coverage" value={67} warn />
            </div>
            <div className="flex-1 space-y-4">
              <p className="text-[15px] text-foreground/80 leading-relaxed">{caseData.description ?? caseData.summary}</p>
              <div className="flex flex-wrap gap-6 text-sm border-t border-white/5 pt-4 mt-2">
                <MetaField label="Officer" value={`${caseData.investigator} (${caseData.unit})`} />
                <MetaField label="Status" value={caseData.status} />
                <MetaField label="Last Updated" value={new Date(caseData.lastUpdated).toLocaleString()} />
              </div>
            </div>
          </div>
        </Card>

        {/* Forensic Details */}
        <Card title="Forensic Details">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <Field label="Cause of death" value={caseData.forensics?.causeOfDeath ?? "—"} />
            <Field label="Time of death" value={caseData.forensics?.timeOfDeath ?? "—"} />
            <Field label="Manner of death" value={caseData.forensics?.mannerOfDeath ?? "—"} />
          </div>
          <div className="mt-5 pt-5 border-t border-white/5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground mb-3">Injuries</p>
            <ul className="flex flex-wrap gap-2">
              {(caseData.forensics?.injuries ?? []).map((i) => (
                <li key={i} className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[13px] text-foreground/85">{i}</li>
              ))}
              {!caseData.forensics?.injuries?.length && <li className="text-[14px] text-muted-foreground">No data</li>}
            </ul>
          </div>
        </Card>
      </div>

      {/* Evidence Modules */}
      <div>
        <h3 className="text-[12px] font-semibold uppercase tracking-[0.15em] text-muted-foreground mb-4">Evidence Modules</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {caseData.evidenceModules.map((m) => {
            const meta = evidenceMeta[m];
            const Icon = meta.icon;
            const target =
              m === "autopsy" ? `/case/${caseData.id}/autopsy` :
              `/case/${caseData.id}/timeline`;
            return (
              <Link
                key={m}
                to={target}
                className="group flex items-center gap-3 rounded-xl border border-white/8 bg-white/[0.03] p-4 hover:bg-white/[0.06] hover:border-primary/30 transition-all duration-200"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:text-primary transition-colors">
                  <Icon className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[14px] font-semibold text-foreground/90 group-hover:text-foreground transition-colors">{meta.label}</p>
                  <p className="text-[12px] text-muted-foreground mt-0.5">View module</p>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/8 p-6 space-y-5" style={{ background: "#0f0f14" }}>
      <h3 className="text-[12px] font-semibold uppercase tracking-[0.18em] text-muted-foreground flex items-center gap-2">
        <ShieldCheck className="h-4 w-4 text-primary/70" />
        {title}
      </h3>
      <div>{children}</div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">{label}</p>
      <p className="mt-1.5 text-[15px] font-medium text-foreground/90">{value}</p>
    </div>
  );
}

function MetaField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-[14px] font-semibold text-foreground/85">{value}</p>
    </div>
  );
}

function Meter({ label, value, warn }: { label: string; value: number; warn?: boolean }) {
  return (
    <div>
      <div className="flex justify-between text-[13px] font-medium mb-2">
        <span className="text-foreground/75">{label}</span>
        <span className={warn ? "text-[#b45309]" : "text-primary"}>{value}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/8 overflow-hidden">
        <div
          className={`h-full rounded-full ${warn ? "bg-[#b45309]" : "bg-primary"}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function Insight({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <li className="rounded-lg border border-white/8 bg-white/[0.03] p-4">
      <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">{label}</p>
      <p className={`mt-1.5 text-[14px] font-medium ${warn ? "text-[#ff6b6b]" : "text-foreground/85"}`}>
        {warn && <AlertTriangle className="inline h-3.5 w-3.5 mr-1.5 mb-0.5" />}{value}
      </p>
    </li>
  );
}
