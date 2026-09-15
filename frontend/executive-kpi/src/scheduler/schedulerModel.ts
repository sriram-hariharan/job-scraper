export type SchedulerRun = {
  run_id?: string;
  job_name?: string;
  status?: string;
  return_code?: number | string | null;
  started_at?: string;
  finished_at?: string;
  trigger_source?: string;
};

export type SchedulerContractHealth = {
  ok?: boolean;
  checks?: {
    seed_sql_matches_artifact?: boolean;
    init_sql_matches_artifact?: boolean;
  };
  all_checks_pass?: boolean;
};

export type SchedulerHistorySummary = {
  jsonl_path?: string;
  jsonl_row_count?: number;
  postgres_row_count?: number;
  count_matches?: boolean;
};

export type SchedulerPostgresSummary = {
  job_definition_count?: number;
  active_job_count?: number;
  run_history_count?: number;
  success_count?: number;
  failure_count?: number;
};

export type SchedulerAutomationControl = {
  paused: boolean;
  revision: number;
  updated_at: string | null;
  updated_by_user_id: string | null;
  paused_at: string | null;
  paused_by_user_id: string | null;
  affected_jobs: ["agent_discovery", "live_pipeline"];
  manual_admin_runs_allowed: true;
};

export type SchedulerRuntimeState =
  | "running"
  | "idle"
  | "unloaded"
  | "not_installed"
  | "unavailable";

export type SchedulerRuntimeJob = {
  job_name: string;
  description: string;
  cadence_seconds: number;
  installed: boolean | null;
  loaded: boolean | null;
  enabled: boolean | null;
  armed: boolean | null;
  running: boolean | null;
  runtime_state: SchedulerRuntimeState;
  last_run?: SchedulerRun | null;
  expected_next_run_at?: string | null;
  manual_run_active?: boolean;
  manual_run_started_at?: string | null;
};

export type SchedulerNextRunPresentation = {
  tone: "scheduled" | "running" | "awaiting" | "unavailable" | "unknown" | "overdue";
  label: string;
};

export type SchedulerSummaryPayload = {
  ok?: boolean;
  limit?: number;
  contract_health?: SchedulerContractHealth;
  automation_control?: SchedulerAutomationControl;
  history?: SchedulerHistorySummary;
  latest_runs_by_job?: SchedulerRun[];
  latest_scheduled_runs_by_job?: SchedulerRun[];
  recent_postgres_runs?: SchedulerRun[];
  recent_jsonl_runs?: SchedulerRun[];
  runtime_jobs?: SchedulerRuntimeJob[];
  postgres_summary?: SchedulerPostgresSummary;
  postgres_command_text?: string;
};

export type SchedulerAutomationControlMutationResponse = {
  ok: true;
  changed: boolean;
  previous_paused: boolean;
  automation_control: SchedulerAutomationControl;
};

export type ManualAgentDiscoveryResponse = {
  ok: boolean;
  accepted: boolean;
  job_name: "agent_discovery";
  trigger_source: "manual_admin";
};

export type AgentDiscoveryRunSummary = {
  ok: boolean;
  available: boolean;
  run_id: string;
  job_name: "agent_discovery";
  status: "succeeded" | "failed" | "unknown";
  trigger: "manual" | "scheduled" | "unknown";
  started_at: string;
  finished_at: string;
  return_code: number | null;
  summary_message: string;
  company_discovery: {
    status: "succeeded" | "failed" | "skipped" | "unknown";
    queries_attempted: number | null;
    queries_failed: number | null;
    total_candidate_count: number | null;
    candidate_counts_by_ats: Record<string, number>;
  };
  discovery: {
    run_unique_discovered_by_ats: Record<string, number>;
    sources: Record<string, Record<string, number>>;
  };
  components: Record<string, "succeeded" | "failed" | "skipped" | "unknown">;
  failure_components: string[];
};

export class AgentDiscoverySummaryUnavailableError extends Error {}

function schedulerControlErrorDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail.trim() || fallback;
  if (
    detail !== null
    && typeof detail === "object"
    && !Array.isArray(detail)
    && "error_category" in detail
    && detail.error_category === "scheduler_automation_control_unavailable"
  ) {
    return "Scheduler automation control is unavailable.";
  }
  return fallback;
}

export async function readSchedulerSummary(): Promise<SchedulerSummaryPayload> {
  const response = await fetch("/scheduler/summary?limit=25", {
    method: "GET",
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  const payload = (await response.json().catch(() => ({}))) as SchedulerSummaryPayload & { detail?: unknown };
  if (!response.ok) {
    throw new Error(schedulerControlErrorDetail(
      payload?.detail,
      `Scheduler summary request failed (${response.status})`,
    ));
  }
  return payload;
}

export async function runAgentDiscoveryNow(): Promise<ManualAgentDiscoveryResponse> {
  const response = await fetch("/scheduler/jobs/agent_discovery/run-now", {
    method: "POST",
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  const payload = (await response.json().catch(() => ({}))) as Partial<ManualAgentDiscoveryResponse> & {
    detail?: string | { error_category?: string };
  };
  if (!response.ok) {
    const detail = typeof payload.detail === "string"
      ? payload.detail
      : clean(payload.detail?.error_category).replace(/_/g, " ");
    throw new Error(detail || `Manual Agent Discovery request failed (${response.status})`);
  }
  return payload as ManualAgentDiscoveryResponse;
}

export async function updateSchedulerAutomationControl(
  paused: boolean,
): Promise<SchedulerAutomationControlMutationResponse> {
  const response = await fetch("/scheduler/automation-control", {
    method: "PUT",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ paused }),
  });
  const payload = (await response.json().catch(() => ({}))) as Partial<SchedulerAutomationControlMutationResponse> & {
    detail?: unknown;
  };
  if (!response.ok) {
    throw new Error(schedulerControlErrorDetail(
      payload?.detail,
      `Scheduler automation control request failed (${response.status})`,
    ));
  }
  return payload as SchedulerAutomationControlMutationResponse;
}

export async function readAgentDiscoveryRunSummary(
  runId: string,
): Promise<AgentDiscoveryRunSummary> {
  const response = await fetch(
    `/scheduler/runs/${encodeURIComponent(clean(runId))}/agent-discovery-summary`,
    {
      method: "GET",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    },
  );
  const payload = (await response.json().catch(() => ({}))) as AgentDiscoveryRunSummary & {
    detail?: string | { message?: string };
  };
  if (response.status === 404) {
    throw new AgentDiscoverySummaryUnavailableError("Discovery summary unavailable");
  }
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : payload.detail?.message;
    throw new Error(detail || `Discovery summary request failed (${response.status})`);
  }
  return payload;
}

export function clean(value: unknown): string {
  return String(value ?? "").trim();
}

export function shown(value: unknown, fallback = "Unavailable"): string {
  return clean(value) || fallback;
}

export function statusSlug(value: unknown): string {
  return clean(value).toLowerCase().replace(/[^a-z0-9]+/g, "-") || "unknown";
}

const DATE_ONLY_FORMATTER = new Intl.DateTimeFormat(undefined, {
  month: "short",
  day: "numeric",
  year: "numeric",
});

const TIME_ONLY_FORMATTER = new Intl.DateTimeFormat(undefined, {
  hour: "numeric",
  minute: "2-digit",
});

const CLOCK_FORMATTER = new Intl.DateTimeFormat(undefined, {
  hour: "numeric",
  minute: "2-digit",
});

export function formatDateTime(value: unknown): string {
  const raw = clean(value);
  if (!raw) return "Unavailable";
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  return `${DATE_ONLY_FORMATTER.format(parsed)}, ${TIME_ONLY_FORMATTER.format(parsed)}`;
}

export function formatExpectedRunDateTime(value: unknown): string {
  const raw = clean(value);
  if (!raw) return "Unavailable";
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return "Unavailable";
  return `${DATE_ONLY_FORMATTER.format(parsed)} · ${TIME_ONLY_FORMATTER.format(parsed)}`;
}

export function schedulerNextRunPresentation(
  job: SchedulerRuntimeJob,
  now: Date,
): SchedulerNextRunPresentation {
  if (job.manual_run_active === true) {
    return { tone: "running", label: "RUNNING NOW" };
  }
  if (job.runtime_state === "running") {
    return { tone: "running", label: "RUNNING NOW" };
  }
  if (job.runtime_state === "unavailable") {
    return { tone: "unknown", label: "SCHEDULE UNKNOWN" };
  }
  if (
    job.installed === false
    || job.loaded === false
    || job.enabled === false
    || job.armed === false
    || job.runtime_state === "not_installed"
    || job.runtime_state === "unloaded"
  ) {
    return { tone: "unavailable", label: "NEXT RUN UNAVAILABLE" };
  }
  if (
    job.installed === null
    || job.loaded === null
    || job.enabled === null
    || job.armed === null
    || job.running === null
  ) {
    return { tone: "unknown", label: "SCHEDULE UNKNOWN" };
  }

  const expected = new Date(clean(job.expected_next_run_at));
  if (!job.expected_next_run_at || Number.isNaN(expected.getTime())) {
    return { tone: "awaiting", label: "SCHEDULED · AWAITING FIRST RUN" };
  }
  const formatted = formatExpectedRunDateTime(job.expected_next_run_at);
  if (now.getTime() > expected.getTime()) {
    return {
      tone: "overdue",
      label: `EXPECTED RUN OVERDUE · ${formatted}`,
    };
  }
  return { tone: "scheduled", label: `EXPECTED NEXT · ${formatted}` };
}

export function schedulerTriggerLabel(value: unknown): string {
  const trigger = clean(value).toLowerCase();
  if (trigger === "external_scheduler_wrapper") return "Scheduled";
  if (trigger === "manual_admin") return "Manual";
  return "Unknown";
}

export function formatClockTime(date: Date): string {
  return CLOCK_FORMATTER.format(date);
}

export function isFailedStatus(status: unknown): boolean {
  return clean(status).toLowerCase() === "failed";
}

export function formatCadence(seconds: unknown): string {
  const value = Number(seconds);
  if (!Number.isFinite(value) || value <= 0) return "Unavailable";
  if (value % 3600 === 0) {
    const hours = value / 3600;
    return `Every ${hours} ${hours === 1 ? "hour" : "hours"}`;
  }
  return `Every ${value} seconds`;
}

/**
 * Deterministic Job Status ordering: failed/attention jobs first, then most
 * recently started. Falls back to stable latest-first ordering when no
 * status distinguishes failure, since the underlying rows are already
 * "latest run per job" (one row per scheduled job).
 */
export function sortJobStatusRows(rows: SchedulerRun[]): SchedulerRun[] {
  return [...rows].sort((a, b) => {
    const aFailed = isFailedStatus(a.status) ? 0 : 1;
    const bFailed = isFailedStatus(b.status) ? 0 : 1;
    if (aFailed !== bFailed) return aFailed - bFailed;
    const aTime = Date.parse(clean(a.started_at)) || 0;
    const bTime = Date.parse(clean(b.started_at)) || 0;
    return bTime - aTime;
  });
}

export function runRowKey(row: SchedulerRun, index: number): string {
  return clean(row.run_id) || [clean(row.job_name), clean(row.started_at), index].join("|");
}
