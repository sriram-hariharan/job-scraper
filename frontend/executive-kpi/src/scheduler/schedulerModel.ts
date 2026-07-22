export type SchedulerRun = {
  run_id?: string;
  job_name?: string;
  status?: string;
  return_code?: number | string | null;
  started_at?: string;
  finished_at?: string;
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

export type SchedulerSummaryPayload = {
  ok?: boolean;
  limit?: number;
  contract_health?: SchedulerContractHealth;
  history?: SchedulerHistorySummary;
  latest_runs_by_job?: SchedulerRun[];
  recent_postgres_runs?: SchedulerRun[];
  recent_jsonl_runs?: SchedulerRun[];
  postgres_summary?: SchedulerPostgresSummary;
  postgres_command_text?: string;
};

export async function readSchedulerSummary(): Promise<SchedulerSummaryPayload> {
  const response = await fetch("/scheduler/summary?limit=25", {
    method: "GET",
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  const payload = (await response.json().catch(() => ({}))) as SchedulerSummaryPayload & { detail?: string };
  if (!response.ok) {
    throw new Error(payload?.detail || `Scheduler summary request failed (${response.status})`);
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

export function formatClockTime(date: Date): string {
  return CLOCK_FORMATTER.format(date);
}

export function isFailedStatus(status: unknown): boolean {
  return clean(status).toLowerCase() === "failed";
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
