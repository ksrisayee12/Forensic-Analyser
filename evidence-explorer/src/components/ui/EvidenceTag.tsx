import type { EvidenceModule } from "@/types";
import { Microscope, Video, Smartphone, MapPin, Users, Mic, Image as ImageIcon, FileText } from "lucide-react";

const meta: Record<EvidenceModule, { label: string; icon: typeof Microscope }> = {
  autopsy: { label: "Autopsy", icon: Microscope },
  cctv: { label: "CCTV", icon: Video },
  mobile: { label: "Mobile", icon: Smartphone },
  gps: { label: "GPS", icon: MapPin },
  witness: { label: "Witness", icon: Users },
  audio: { label: "Audio", icon: Mic },
  images: { label: "Images", icon: ImageIcon },
  documents: { label: "Documents", icon: FileText },
};

export function EvidenceTag({ module }: { module: EvidenceModule }) {
  const m = meta[module];
  const Icon = m.icon;
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground">
      <Icon className="h-3 w-3" />
      {m.label}
    </span>
  );
}

export const evidenceMeta = meta;
