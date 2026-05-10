import { createFileRoute, Outlet } from "@tanstack/react-router";
import { getCaseById } from "@/services/api";
import { CaseHeader } from "@/components/CaseHeader";

export const Route = createFileRoute("/case/$caseId")({
  loader: async ({ params }) => {
    const caseData = await getCaseById(params.caseId);
    if (!caseData) throw new Error("Case not found");
    return { caseData };
  },
  pendingComponent: () => <div className="p-8 text-sm text-muted-foreground">Loading case…</div>,
  errorComponent: ({ error }) => (
    <div className="p-8 text-sm text-destructive">
      <p className="font-bold">Error loading case route:</p>
      <p className="mt-2 font-mono bg-destructive/10 p-4 rounded text-xs">{(error as Error).message || "Unknown error"}</p>
    </div>
  ),
  component: CaseLayout,
});

function CaseLayout() {
  const { caseData } = Route.useLoaderData();

  return (
    <>
      <CaseHeader caseData={caseData} />
      <Outlet />
    </>
  );
}
