import { mockCases } from "@/data/mockCases";
import { mockAutopsy } from "@/data/mockAutopsy";
import { mockTimeline } from "@/data/mockTimeline";
import { mockGraph } from "@/data/mockGraph";
import type { Case } from "@/types";

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function getCases(): Promise<Case[]> {
  await delay(300);
  return mockCases;
}

export async function getCaseById(id: string) {
  await delay(200);
  return mockCases.find((c) => c.id === id) ?? null;
}

export async function getAutopsyData(caseId: string) {
  await delay(200);
  return mockAutopsy[caseId] ?? null;
}

export async function getTimelineEvents(caseId: string) {
  await delay(200);
  return mockTimeline[caseId] ?? [];
}

export async function getCorrelationGraph(caseId: string) {
  await delay(200);
  return mockGraph[caseId] ?? { nodes: [], edges: [] };
}
