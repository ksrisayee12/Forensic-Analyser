export type EvidenceModule =
  | "autopsy"
  | "cctv"
  | "mobile"
  | "gps"
  | "witness"
  | "audio"
  | "images"
  | "documents";

export type CaseStatus = "Active" | "Under Review" | "Closed";
export type CasePriority = "Standard" | "Elevated" | "Critical Review";

export interface Case {
  id: string;
  victim: string;
  date: string;
  status: CaseStatus;
  investigator: string;
  officer: string;
  unit: string;
  location?: string;
  priority: CasePriority;
  evidenceModules: EvidenceModule[];
  lastUpdated: string;
  summary: string;
  description?: string;
  forensics?: {
    causeOfDeath: string;
    timeOfDeath: string;
    mannerOfDeath: string;
    injuries: string[];
  };
}

export interface Officer {
  id: string;
  name: string;
  unit: string;
  badge: string;
}

export interface AutopsyExtraction {
  causeOfDeath: string;
  injuries: string[];
  toxicology: string;
  suspicionLevel: "LOW" | "MEDIUM" | "HIGH";
  estimatedTraumaTime: string;
  abnormalObservations: string;
  rawReport: string;
}

export type EvidenceSource = "CCTV" | "GPS" | "MOBILE" | "WITNESS" | "AUTOPSY";

export interface EvidenceEvent {
  id: string;
  time: string;
  source: EvidenceSource;
  description: string;
  confidence: number;
  isAnomaly?: boolean;
  linkedEvents?: string[];
}

export type GraphNodeType = "person" | "location" | "device" | "event";

export interface GraphNode {
  id: string;
  label: string;
  type: GraphNodeType;
  reliability?: string;
  evidenceType?: "cctv" | "autopsy" | "mobile" | "witness" | "gps";
  evidenceData?: {
    timestamp?: string;
    location?: string;
    confidence?: number;
    preview?: string;
    details?: string;
  };
}

export interface GraphEdge {
  source: string;
  target: string;
  label?: string;
  confidence?: number;
}
