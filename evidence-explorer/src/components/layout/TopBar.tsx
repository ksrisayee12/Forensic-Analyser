import { useRouterState } from "@tanstack/react-router";
import { useOfficer } from "@/contexts/OfficerContext";

const titleMap: { pattern: RegExp; title: string }[] = [
  { pattern: /^\/$/, title: "My Investigation Workspace" },
  { pattern: /^\/cases$/, title: "Investigation Registry" },
  { pattern: /^\/case\/[^/]+\/autopsy$/, title: "Autopsy Extraction" },
  { pattern: /^\/case\/[^/]+\/timeline$/, title: "Evidence Timeline" },
  { pattern: /^\/case\/[^/]+\/correlation$/, title: "Correlation Graph" },
  { pattern: /^\/case\/[^/]+$/, title: "Case Overview" },
];

export function TopBar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { currentOfficer } = useOfficer();
  const title = titleMap.find((t) => t.pattern.test(pathname))?.title ?? "AIVENTRA";

  return (
    <header className="header-gradient sticky top-0 z-30 h-14 flex items-center justify-between gap-4 border-b border-white/8 px-6">
      <h1 className="text-[15px] font-semibold tracking-[0.06em] uppercase text-foreground/90">{title}</h1>
      <div className="flex items-center gap-4">
        <div className="text-right hidden sm:block">
          <p className="text-[14px] font-semibold text-foreground/90">{currentOfficer.name}</p>
          <p className="text-[12px] text-muted-foreground mt-0.5">{currentOfficer.unit}</p>
        </div>
        <div className="h-9 w-9 rounded-lg border border-primary/30 bg-primary/10 text-primary flex items-center justify-center text-[13px] font-bold">
          {currentOfficer.name.split(" ").map((s) => s[0]).join("").slice(0, 2)}
        </div>
      </div>
    </header>
  );
}
