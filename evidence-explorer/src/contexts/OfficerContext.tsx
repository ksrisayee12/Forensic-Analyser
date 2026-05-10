import { createContext, useContext, useState, type ReactNode } from "react";
import { officers } from "@/data/officers";
import type { Officer } from "@/types";

interface OfficerContextType {
  currentOfficer: Officer;
  availableOfficers: Officer[];
  switchOfficer: (id: string) => void;
}

const OfficerContext = createContext<OfficerContextType | null>(null);

export function OfficerProvider({ children }: { children: ReactNode }) {
  const [currentOfficer, setCurrentOfficer] = useState<Officer>(officers[0]);

  const switchOfficer = (id: string) => {
    const found = officers.find((o) => o.id === id);
    if (found) setCurrentOfficer(found);
  };

  return (
    <OfficerContext.Provider value={{ currentOfficer, availableOfficers: officers, switchOfficer }}>
      {children}
    </OfficerContext.Provider>
  );
}

export function useOfficer() {
  const ctx = useContext(OfficerContext);
  if (!ctx) throw new Error("useOfficer must be used within OfficerProvider");
  return ctx;
}
