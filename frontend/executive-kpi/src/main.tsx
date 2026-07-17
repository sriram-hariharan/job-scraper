import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { AnalyticsDashboard } from "./AnalyticsDashboard";
import type { ExecutiveKpiState } from "./AnalyticsDashboard";
import "./styles.css";

const KPI_EVENT_NAME = "applylens:executive-kpi-state";
const DEFAULT_STATE: ExecutiveKpiState = { status: "loading" };

declare global {
  interface Window {
    __APPLYLENS_EXECUTIVE_KPI_STATE__?: ExecutiveKpiState;
  }
}

function ExecutiveKpiIsland() {
  const [state, setState] = useState<ExecutiveKpiState>(
    () => window.__APPLYLENS_EXECUTIVE_KPI_STATE__ || DEFAULT_STATE,
  );

  useEffect(() => {
    const handleState = (event: Event) => {
      const nextState = (event as CustomEvent<ExecutiveKpiState>).detail;
      if (nextState?.status) setState(nextState);
    };

    window.addEventListener(KPI_EVENT_NAME, handleState);
    return () => window.removeEventListener(KPI_EVENT_NAME, handleState);
  }, []);

  return <AnalyticsDashboard state={state} />;
}

const mount = document.getElementById("executiveKpiRoot");
if (mount) {
  createRoot(mount).render(
    <StrictMode>
      <ExecutiveKpiIsland />
    </StrictMode>,
  );
}
