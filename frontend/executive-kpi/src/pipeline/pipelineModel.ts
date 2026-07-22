export const PIPELINE_POLL_INTERVAL_MS = 2_000;
export const PIPELINE_STALE_AFTER_MS = PIPELINE_POLL_INTERVAL_MS * 15;

export const DEFAULT_STAGE_ORDER = [
  "startup",
  "scraping",
  "filtering",
  "dedupe",
  "ranking",
  "cache_filter",
  "details",
  "intelligence",
  "ai_evaluation_filter",
  "embedding_prefilter",
  "ai_evaluation",
  "resume_matching",
  "application_priority",
  "rag_export",
  "planning",
  "finalization",
] as const;

export const STAGE_LABELS: Record<string, string> = {
  startup: "Startup",
  scraping: "Scraping",
  filtering: "Filtering",
  dedupe: "Deduplication",
  ranking: "Ranking",
  cache_filter: "Cache Filter",
  details: "Details",
  intelligence: "Intelligence",
  ai_evaluation_filter: "AI Evaluation Filter",
  embedding_prefilter: "Embedding Prefilter",
  ai_evaluation: "AI Evaluation",
  resume_matching: "Resume Matching",
  application_priority: "Application Priority",
  rag_export: "RAG Export",
  planning: "Planning",
  finalization: "Finalization",
};

export const COUNT_GROUPS = [
  {
    label: "Collection",
    keys: [
      ["scraped_jobs", "Scraped"],
      ["filtered_jobs", "Filtered"],
      ["new_jobs", "New"],
    ],
  },
  {
    label: "Relevance and deduplication",
    keys: [
      ["deduped_jobs", "Deduplicated"],
      ["ranked_jobs", "Ranked"],
      ["detailed_jobs", "Detailed"],
    ],
  },
  {
    label: "Intelligence and evaluation",
    keys: [
      ["intelligent_jobs", "Intelligence"],
      ["evaluable_jobs", "AI Eligible"],
      ["prefilter_jobs", "Prefilter"],
      ["ai_jobs", "AI Evaluated"],
    ],
  },
  {
    label: "Resume matching and planning",
    keys: [
      ["resume_matched_jobs", "Resume Matched"],
      ["scored_jobs", "Scored"],
      ["rag_export_count", "RAG Exported"],
      ["planning_packets_total", "Planning Packets"],
      ["planning_packets_completed", "Packets Completed"],
    ],
  },
  {
    label: "Final output",
    keys: [["final_jobs", "Final Jobs"]],
  },
] as const;

export const FLOW_STAGES = [
  ["scraped_jobs", "Collected"],
  ["filtered_jobs", "Filtered"],
  ["deduped_jobs", "Deduplicated"],
  ["ranked_jobs", "Ranked"],
  ["ai_jobs", "Evaluated"],
  ["resume_matched_jobs", "Resume matched"],
  ["final_jobs", "Final"],
] as const;

export type PipelineDisplayStatus = "idle" | "starting" | "running" | "succeeded" | "failed" | "unavailable";

export type SourceHealthItem = {
  source: string;
  status?: string;
  jobs_returned?: number;
  last_success?: string;
  error?: string;
};

export type PipelineRecord = {
  status?: string;
  run_id?: string;
  return_code?: number | null;
  started_at?: string;
  updated_at?: string;
  updated_at_utc?: string;
  finished_at?: string;
  current_stage?: string;
  completed_stages?: string[];
  stage_order?: string[];
  stage_started_at?: string;
  stage_message?: string;
  summary_message?: string;
  final_job_count?: number | null;
  error?: string;
  is_running?: boolean;
  counts?: Record<string, unknown>;
  config?: Record<string, unknown>;
  source_health?: SourceHealthItem[];
};

export type PipelineStatusResponse = {
  ok?: boolean;
  pipeline?: PipelineRecord;
};

export function displayStatus(rawStatus: unknown): PipelineDisplayStatus {
  const status = String(rawStatus || "idle").trim().toLowerCase();
  if (status === "idle") return "idle";
  if (status === "queued" || status === "starting") return "starting";
  if (status === "running") return "running";
  if (status === "succeeded") return "succeeded";
  if (["failed", "cancelled", "canceled", "stopped"].includes(status)) return "failed";
  return "unavailable";
}

export function stageOrder(pipeline: PipelineRecord): string[] {
  const supplied = Array.isArray(pipeline.stage_order)
    ? pipeline.stage_order.filter((stage): stage is string => typeof stage === "string" && stage.length > 0)
    : [];
  return supplied.length ? supplied : [...DEFAULT_STAGE_ORDER];
}

export function numericCount(value: unknown): number | null {
  if (value === "" || value === null || value === undefined || typeof value === "boolean") return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

export function formatDateTime(value: unknown): string {
  if (!value) return "";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export function elapsedLabel(startedAt: unknown, finishedAt: unknown, nowMs = Date.now()): string {
  const started = new Date(String(startedAt || ""));
  if (Number.isNaN(started.getTime())) return "";
  const finished = finishedAt ? new Date(String(finishedAt)) : null;
  const endMs = finished && !Number.isNaN(finished.getTime()) ? finished.getTime() : nowMs;
  const totalSeconds = Math.max(0, Math.floor((endMs - started.getTime()) / 1_000));
  const hours = Math.floor(totalSeconds / 3_600);
  const minutes = Math.floor((totalSeconds % 3_600) / 60);
  const seconds = totalSeconds % 60;
  if (hours) return `${hours}h ${minutes}m`;
  if (minutes) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

export function explicitUpdatedAt(pipeline: PipelineRecord): string {
  return String(pipeline.updated_at_utc || pipeline.updated_at || "").trim();
}

export function isStatusStale(pipeline: PipelineRecord, nowMs = Date.now()): boolean {
  if (displayStatus(pipeline.status) !== "running") return false;
  const updatedAt = explicitUpdatedAt(pipeline);
  if (!updatedAt) return false;
  const updated = new Date(updatedAt);
  return !Number.isNaN(updated.getTime()) && nowMs - updated.getTime() > PIPELINE_STALE_AFTER_MS;
}
