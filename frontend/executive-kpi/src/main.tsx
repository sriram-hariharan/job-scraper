import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { AnalyticsDashboard } from "./AnalyticsDashboard";
import type { ExecutiveKpiState } from "./AnalyticsDashboard";
import {
  DEFAULT_QUEUE_STATE,
  ExecutiveQueue,
  QUEUE_STATE_EVENT,
  type ExecutiveQueueState,
} from "./ExecutiveQueue";
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

function ExecutiveQueueIsland() {
  const [state, setState] = useState<ExecutiveQueueState>(
    () => window.__APPLYLENS_EXECUTIVE_QUEUE_STATE__ || DEFAULT_QUEUE_STATE,
  );

  useEffect(() => {
    const handleState = (event: Event) => {
      const nextState = (event as CustomEvent<ExecutiveQueueState>).detail;
      if (nextState?.status) setState(nextState);
    };

    window.addEventListener(QUEUE_STATE_EVENT, handleState);
    return () => window.removeEventListener(QUEUE_STATE_EVENT, handleState);
  }, []);

  return <ExecutiveQueue state={state} />;
}

const mount = document.getElementById("executiveKpiRoot");
if (mount) {
  createRoot(mount).render(
    <StrictMode>
      <ExecutiveKpiIsland />
    </StrictMode>,
  );
}

const queueMount = document.getElementById("executiveQueueRoot");
if (queueMount) {
  createRoot(queueMount).render(
    <StrictMode>
      <ExecutiveQueueIsland />
    </StrictMode>,
  );
}
