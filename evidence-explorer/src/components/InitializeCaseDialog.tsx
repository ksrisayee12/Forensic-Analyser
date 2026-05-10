import { useState, useRef } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Check } from "lucide-react";
import { evidenceMeta } from "@/components/ui/EvidenceTag";
import type { EvidenceModule, CasePriority } from "@/types";
import { useOfficer } from "@/contexts/OfficerContext";
import { toast } from "sonner";

const allModules: EvidenceModule[] = ["autopsy", "cctv", "mobile", "gps", "witness", "audio", "images", "documents"];

export function InitializeCaseDialog() {
  const { currentOfficer } = useOfficer();
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(1);
  const [caseId] = useState(() => `AIV-${Math.floor(1000 + Math.random() * 9000)}`);
  const [victim, setVictim] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [location, setLocation] = useState("");
  const [priority, setPriority] = useState<CasePriority>("Standard");
  const [description, setDescription] = useState("");
  const [selected, setSelected] = useState<EvidenceModule[]>([]);
  const [moduleIndex, setModuleIndex] = useState(0);
  const [descriptions, setDescriptions] = useState<Record<string, string>>({});
  const [selectedFiles, setSelectedFiles] = useState<Record<string, File[]>>({});

  const reset = () => {
    setStep(1); setVictim(""); setDate(new Date().toISOString().slice(0, 10));
    setLocation(""); setPriority("Standard"); setDescription(""); setSelected([]);
    setModuleIndex(0); setDescriptions({}); setSelectedFiles({});
  };

  const toggle = (m: EvidenceModule) =>
    setSelected((s) => (s.includes(m) ? s.filter((x) => x !== m) : [...s, m]));

  const canStep1 = victim.trim() && location.trim() && description.trim();
  const canStep2 = selected.length > 0;
  const currentModule = selected[moduleIndex];
  const canStep3 = currentModule ? (descriptions[currentModule] ?? "").trim().length > 0 : false;

  const submit = () => {
    toast.success(`Case ${caseId} initialised`, { description: `${selected.length} evidence module(s) registered.` });
    setOpen(false);
    setTimeout(reset, 200);
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-2" /> Initialize Case
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Initialize Investigation — Step {step} of 3</DialogTitle>
        </DialogHeader>

        {step === 1 && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs text-muted-foreground">Case ID</Label>
                <Input value={caseId} disabled className="mt-1" />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Date of Incident</Label>
                <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="mt-1" />
              </div>
              <div className="col-span-2">
                <Label className="text-xs text-muted-foreground">Victim Name</Label>
                <Input value={victim} onChange={(e) => setVictim(e.target.value)} className="mt-1" placeholder="Full name" />
              </div>
              <div className="col-span-2">
                <Label className="text-xs text-muted-foreground">Location</Label>
                <Input value={location} onChange={(e) => setLocation(e.target.value)} className="mt-1" placeholder="e.g. Bandra West, Mumbai" />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Officer</Label>
                <Input value={currentOfficer.name} disabled className="mt-1" />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Unit</Label>
                <Input value={currentOfficer.unit} disabled className="mt-1" />
              </div>
              <div className="col-span-2">
                <Label className="text-xs text-muted-foreground">Priority</Label>
                <div className="mt-2 flex gap-2">
                  {(["Standard", "Elevated", "Critical Review"] as CasePriority[]).map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setPriority(p)}
                      className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
                        priority === p ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              <div className="col-span-2">
                <Label className="text-xs text-muted-foreground">Case Description</Label>
                <Textarea value={description} onChange={(e) => setDescription(e.target.value)} className="mt-1" rows={3} placeholder="Brief overview of the incident…" />
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <Button disabled={!canStep1} onClick={() => setStep(2)}>Next</Button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">Select all evidence modules to attach to this case.</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {allModules.map((m) => {
                const meta = evidenceMeta[m];
                const Icon = meta.icon;
                const active = selected.includes(m);
                return (
                  <button
                    key={m}
                    type="button"
                    onClick={() => toggle(m)}
                    className={`relative rounded-lg border p-3 text-left transition-colors ${
                      active ? "border-primary bg-primary/10" : "border-border hover:bg-accent"
                    }`}
                  >
                    <Icon className="h-4 w-4 mb-2 text-primary" />
                    <p className="text-sm font-medium">{meta.label}</p>
                    {active && <Check className="absolute top-2 right-2 h-3.5 w-3.5 text-primary" />}
                  </button>
                );
              })}
            </div>
            <div className="flex justify-between pt-2">
              <Button variant="ghost" onClick={() => setStep(1)}>Back</Button>
              <Button disabled={!canStep2} onClick={() => { setModuleIndex(0); setStep(3); }}>Next</Button>
            </div>
          </div>
        )}

        {step === 3 && currentModule && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  Module {moduleIndex + 1} of {selected.length}
                </p>
                <h3 className="text-lg font-semibold">{evidenceMeta[currentModule].label}</h3>
              </div>
            </div>

            <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground cursor-pointer" onClick={() => inputRef.current?.click()}>
              Drag &amp; drop evidence files here, or click to browse.
              <p className="mt-1 text-xs">Max 1MB per file. (Mock upload zone)</p>
            </div>

            <input type="file" multiple ref={inputRef} style={{ display: 'none' }} onChange={(e) => { const files = Array.from(e.target.files || []); setSelectedFiles(prev => ({ ...prev, [currentModule]: files })); if (files.length > 0) { toast.success(`Selected ${files.length} file(s) for ${evidenceMeta[currentModule].label}`); } }} />

            {selectedFiles[currentModule] && selectedFiles[currentModule].length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium text-muted-foreground">Attached Files:</p>
                <ul className="mt-2 space-y-1">
                  {selectedFiles[currentModule].map((file, i) => (
                    <li key={i} className="text-sm text-foreground flex items-center gap-2">
                      <span className="w-2 h-2 bg-primary rounded-full"></span>
                      {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <Label className="text-xs text-muted-foreground">Evidence Description (required)</Label>
              <Textarea
                value={descriptions[currentModule] ?? ""}
                onChange={(e) => setDescriptions({ ...descriptions, [currentModule]: e.target.value })}
                rows={3}
                className="mt-1"
                placeholder="Describe this evidence…"
              />
            </div>

            {currentModule === "cctv" && (
              <div className="rounded-md border border-border bg-muted/40 p-3 space-y-2">
                <p className="text-xs font-medium">Person Tracking Details</p>
                <Input placeholder="Person description" />
                <Input placeholder="Clothing details" />
                <Input placeholder="Distinguishing features" />
                <Input placeholder="Approximate time" />
              </div>
            )}

            <div className="flex justify-between pt-2">
              <Button
                variant="ghost"
                onClick={() => (moduleIndex === 0 ? setStep(2) : setModuleIndex(moduleIndex - 1))}
              >
                Previous
              </Button>
              {moduleIndex < selected.length - 1 ? (
                <Button disabled={!canStep3} onClick={() => setModuleIndex(moduleIndex + 1)}>Next Module</Button>
              ) : (
                <Button disabled={!canStep3} onClick={submit}>Submit Case</Button>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
