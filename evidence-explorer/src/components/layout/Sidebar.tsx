import { Link, useRouterState } from "@tanstack/react-router";
import { Home, Briefcase, Microscope, Timer, Share2, Shield } from "lucide-react";
import { useOfficer } from "@/contexts/OfficerContext";

export function Sidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { currentOfficer } = useOfficer();

  const caseMatch = pathname.match(/^\/case\/([^/]+)/);
  const caseId = caseMatch?.[1];

  const main = [
    { to: "/", label: "Dashboard", icon: Home, exact: true },
    { to: "/cases", label: "Cases", icon: Briefcase, exact: false },
  ];

  const caseLinks = caseId
    ? [
        { to: `/case/${caseId}/autopsy`, label: "Autopsy Analysis", icon: Microscope },
        { to: `/case/${caseId}/timeline`, label: "Evidence Timeline", icon: Timer },
        { to: `/case/${caseId}/correlation`, label: "Correlation Graph", icon: Share2 },
      ]
    : [];

  const isActive = (to: string, exact: boolean) =>
    exact ? pathname === to : pathname === to || pathname.startsWith(to);

  return (
    <aside
      className="hidden md:flex w-60 shrink-0 flex-col border-r border-white/8"
      style={{ background: "linear-gradient(180deg, #08080a 0%, #0c0c10 100%)" }}
    >
      {/* Brand */}
      <div className="flex items-center gap-3 px-4 h-14 border-b border-white/8">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary border border-primary/20">
          <Shield className="h-4 w-4" />
        </div>
        <div className="leading-tight">
          <p className="text-[15px] font-bold tracking-[0.06em] text-foreground">AIVENTRA</p>
          <p className="text-[10px] uppercase text-muted-foreground tracking-[0.18em] mt-0.5">Forensic Intelligence</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-5 space-y-6">
        <div>
          <p className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Workspace</p>
          <ul className="space-y-0.5">
            {main.map(({ to, label, icon: Icon, exact }) => {
              const active = isActive(to, exact);
              return (
                <li key={to}>
                  <Link
                    to={to}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-medium transition-all duration-150 ${
                      active
                        ? "bg-sidebar-accent text-foreground"
                        : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground"
                    }`}
                  >
                    <Icon className={`h-4 w-4 shrink-0 ${active ? "text-primary" : ""}`} />
                    <span>{label}</span>
                    {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>

        {caseLinks.length > 0 && (
          <div>
            <p className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Case {caseId}
            </p>
            <ul className="space-y-0.5">
              {caseLinks.map(({ to, label, icon: Icon }) => {
                const active = pathname === to;
                return (
                  <li key={to}>
                    <Link
                      to={to}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-medium transition-all duration-150 ${
                        active
                          ? "bg-sidebar-accent text-foreground"
                          : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground"
                      }`}
                    >
                      <Icon className={`h-4 w-4 shrink-0 ${active ? "text-primary" : ""}`} />
                      <span>{label}</span>
                      {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </nav>

      {/* Officer Footer */}
      <div className="border-t border-white/8 p-4">
        <p className="text-[14px] font-semibold text-foreground/90 tracking-tight">{currentOfficer.name}</p>
        <p className="text-[12px] text-muted-foreground mt-0.5">{currentOfficer.unit}</p>
        <p className="mt-2 text-[11px] text-muted-foreground/50 font-mono">
          Badge {currentOfficer.badge} · v1.0
        </p>
      </div>
    </aside>
  );
}
