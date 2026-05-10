import type { EvidenceEvent } from "@/types";

export const mockTimeline: Record<string, EvidenceEvent[]> = {
  "AIV-0041": [
    { id: "evt-001", time: "2024-11-12T20:14:00", source: "CCTV", description: "Subject arrives at residence via main entrance. Alone.", confidence: 96 },
    { id: "evt-002", time: "2024-11-12T21:02:00", source: "MOBILE", description: "Outgoing call placed to unknown international number, duration 12 min.", confidence: 88, linkedEvents: ["evt-005"] },
    { id: "evt-003", time: "2024-11-12T22:18:00", source: "CCTV", description: "Unidentified individual approaches rear utility door.", confidence: 71, isAnomaly: true },
    { id: "evt-004", time: "2024-11-12T22:31:00", source: "GPS", description: "Subject's mobile device reports stationary in master bedroom.", confidence: 92 },
    { id: "evt-005", time: "2024-11-12T22:45:00", source: "WITNESS", description: "Neighbour reports raised voices and a heavy thud from the property.", confidence: 64, isAnomaly: true, linkedEvents: ["evt-002"] },
    { id: "evt-006", time: "2024-11-12T23:02:00", source: "CCTV", description: "Rear utility door opens; figure exits carrying object.", confidence: 78, isAnomaly: true },
    { id: "evt-007", time: "2024-11-13T07:14:00", source: "WITNESS", description: "Housekeeping staff discovers victim and contacts authorities.", confidence: 99 },
    { id: "evt-008", time: "2024-11-13T09:00:00", source: "AUTOPSY", description: "Forensic examination confirms blunt force trauma as primary cause.", confidence: 94 },
  ],
  "AIV-0044": [
    { id: "evt-101", time: "2024-11-04T19:30:00", source: "MOBILE", description: "Subject sends final outgoing message.", confidence: 95 },
    { id: "evt-102", time: "2024-11-04T20:15:00", source: "CCTV", description: "Vehicle of interest enters block.", confidence: 80 },
    { id: "evt-103", time: "2024-11-04T20:42:00", source: "AUTOPSY", description: "Estimated time of fatal discharge.", confidence: 91, isAnomaly: true },
    { id: "evt-104", time: "2024-11-04T20:43:00", source: "WITNESS", description: "Smart-device audio captures single sharp report.", confidence: 86 },
    { id: "evt-105", time: "2024-11-04T20:47:00", source: "CCTV", description: "Vehicle of interest departs at high speed.", confidence: 83, isAnomaly: true },
  ],
};
