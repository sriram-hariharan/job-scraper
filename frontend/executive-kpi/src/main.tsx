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
import { PipelineDashboard } from "./pipeline/PipelineDashboard";
import {
  DEFAULT_PLANNING_STATE,
  PLANNING_STATE_EVENT,
  PlanningFiltersToolbar,
  PlanningSummary,
  PlanningWorklist,
  type PlanningWorklistState,
} from "./PlanningWorklist";
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

function PlanningIsland({ view }: { view: "filters" | "summary" | "worklist" }) {
  const [state, setState] = useState<PlanningWorklistState>(
    () => window.__APPLYLENS_PLANNING_WORKLIST_STATE__ || DEFAULT_PLANNING_STATE,
  );

  useEffect(() => {
    const handleState = (event: Event) => {
      const nextState = (event as CustomEvent<PlanningWorklistState>).detail;
      if (nextState?.status) setState(nextState);
    };
    window.addEventListener(PLANNING_STATE_EVENT, handleState);
    return () => window.removeEventListener(PLANNING_STATE_EVENT, handleState);
  }, []);

  if (view === "filters") return <PlanningFiltersToolbar state={state} />;
  if (view === "summary") return <PlanningSummary state={state} />;
  return <PlanningWorklist state={state} />;
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

const pipelineMount = document.getElementById("pipelineDashboardRoot");
if (pipelineMount) {
  createRoot(pipelineMount).render(
    <StrictMode>
      <PipelineDashboard />
    </StrictMode>,
  );
}

const planningSummaryMount = document.getElementById("planningSummaryRoot");
if (planningSummaryMount) {
  createRoot(planningSummaryMount).render(
    <StrictMode><PlanningIsland view="summary" /></StrictMode>,
  );
}

const planningFiltersMount = document.getElementById("planningFiltersRoot");
if (planningFiltersMount) {
  createRoot(planningFiltersMount).render(
    <StrictMode><PlanningIsland view="filters" /></StrictMode>,
  );
}

const planningWorklistMount = document.getElementById("planningWorklistRoot");
if (planningWorklistMount) {
  createRoot(planningWorklistMount).render(
    <StrictMode><PlanningIsland view="worklist" /></StrictMode>,
  );
}
