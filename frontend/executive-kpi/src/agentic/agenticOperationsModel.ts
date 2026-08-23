export type AgenticOperationsCurrentPipeline = {
  available?: boolean;
  state?: "available" | "not_configured" | "not_found" | "malformed" | "unavailable" | string;
  source_path?: string;
  run_id?: string;
  status?: string;
  current_stage?: string;
  completed_stages?: string[];
  stage_order?: string[];
  stage_started_at?: string;
  stage_message?: string;
  counts?: Record<string, unknown>;
  config?: Record<string, unknown>;
  final_job_count?: number | null;
  return_code?: number | string | null;
  error?: string;
  started_at?: string;
  finished_at?: string;
  updated_at?: string;
  updated_at_utc?: string;
  status_path?: string;
};

export type AgenticOperationsRecentRun = {
  run_id?: string;
  status?: string;
  current_stage?: string;
  stage_message?: string;
  summary_message?: string;
  return_code?: number | string | null;
  started_at?: string;
  updated_at?: string;
  completed_at?: string;
  error?: string;
  final_job_count?: number | null;
  counts?: Record<string, unknown>;
  config?: Record<string, unknown>;
};

export type AgenticOperationsRecentRunsState = {
  available?: boolean;
  state?: "available" | "unavailable" | string;
  count?: number;
  bound?: number;
};

export type AgenticOperationsSafetySummary = {
  canonical_agent_count?: number;
  score_mutation_capable_count?: number;
  rank_mutation_capable_count?: number;
  queue_mutation_capable_count?: number;
  resume_text_mutation_capable_count?: number;
  operator_state_persistence_capable_count?: number;
  application_action_capable_count?: number;
};

export type AgenticOperationsSafetyMetadata = {
  read_only?: boolean;
  admin_only?: boolean;
  cross_user_access?: boolean;
  database_write_performed?: boolean;
  schema_write_performed?: boolean;
  provider_call_performed?: boolean;
  pipeline_execution_performed?: boolean;
  scheduler_mutation_performed?: boolean;
  scoring_changed?: boolean;
  ranking_changed?: boolean;
  queue_mutation_performed?: boolean;
  resume_mutation_performed?: boolean;
  application_execution_performed?: boolean;
  ats_submission_performed?: boolean;
};

export type AgenticOperationsOverviewPayload = {
  ok?: boolean;
  read_only?: boolean;
  admin_only?: boolean;
  owner_user_id?: string;
  current_pipeline?: AgenticOperationsCurrentPipeline;
  recent_runs?: AgenticOperationsRecentRun[];
  recent_runs_state?: AgenticOperationsRecentRunsState;
  canonical_agents?: Record<string, unknown>[];
  safety_summary?: AgenticOperationsSafetySummary;
  safety_metadata?: AgenticOperationsSafetyMetadata;
};

export async function readAgenticOperationsOverview(): Promise<AgenticOperationsOverviewPayload> {
  const response = await fetch("/profile/admin/agentic-operations/overview", {
    method: "GET",
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  const payload = (await response.json().catch(() => ({}))) as AgenticOperationsOverviewPayload & {
    detail?: string;
  };
  if (!response.ok) {
    throw new Error(payload.detail || `Agentic Operations overview request failed (${response.status})`);
  }
  return payload;
}
