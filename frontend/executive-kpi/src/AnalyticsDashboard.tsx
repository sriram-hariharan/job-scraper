import { FileClock, Rows3 } from "lucide-react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

/**
 * Adapted from AnalyticsDashboard by Dhileep Kumar GM.
 * Source: https://21st.dev/@dhileepkumargm/components/analytics-dashboard
 * Adopted 2026-07-17. ApplyLens adaptations replace sample business metrics and
 * temporal demo series with four real queue metrics and an honest current-snapshot view.
 */

export type ExecutiveKpiMetrics = {
  queueRows: number | null;
  nextSteps: number | null;
  undecidedJobReviews: number | null;
  undecidedMaybeTailor: number | null;
};

export type ExecutiveSnapshot = {
  status: "not_generated" | "fresh" | "aging" | "stale";
  runId: string;
  completedAt: string;
  totalJobs: number;
};

export type ExecutiveKpiState =
  | { status: "loading" }
  | { status: "ready"; metrics: ExecutiveKpiMetrics; snapshot?: ExecutiveSnapshot }
  | { status: "error"; message?: string };

type MetricDefinition = {
  key: keyof ExecutiveKpiMetrics;
  label: string;
  tone: "blue" | "green" | "violet" | "cyan";
};

const METRICS: MetricDefinition[] = [
  { key: "queueRows", label: "Queue Rows", tone: "blue" },
  { key: "nextSteps", label: "Next Steps", tone: "green" },
  {
    key: "undecidedJobReviews",
    label: "Undecided Job Reviews",
    tone: "violet",
  },
  {
    key: "undecidedMaybeTailor",
    label: "Undecided Maybe Tailor",
    tone: "cyan",
  },
];

const INTEGER_FORMATTER = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

function safeMetricValue(value: number | null | undefined): number {
  return Number.isFinite(value) ? Math.max(0, Number(value)) : 0;
}

function formatMetric(value: number | null | undefined): string {
  return Number.isFinite(value) ? INTEGER_FORMATTER.format(Number(value)) : "—";
}

type SnapshotTooltipProps = {
  active?: boolean;
  payload?: Array<{ payload?: { current?: number; baseline?: number } }>;
};

export function SnapshotTooltip({ active, payload }: SnapshotTooltipProps) {
  if (!active || !payload?.length) return null;

  const point = payload[0]?.payload;
  if (!point) return null;

  return (
    <div className="executive-kpi-tooltip">
      <span>Current</span>
      <strong>{formatMetric(point.current)}</strong>
      {Number(point.baseline) > 0 ? (
        <small>Queue baseline: {formatMetric(point.baseline)}</small>
      ) : null}
    </div>
  );
}

function SnapshotChart({ value, queueRows, label }: { value: number; queueRows: number; label: string }) {
  const baseline = Math.max(queueRows, value, 1);
  const chartData = [
    {
      name: "Current snapshot",
      current: value,
      remaining: Math.max(0, baseline - value),
      baseline: queueRows,
    },
  ];
  const summary = queueRows > 0
    ? `${label}: ${formatMetric(value)} against a current queue baseline of ${formatMetric(queueRows)}`
    : `${label}: ${formatMetric(value)} in the current snapshot`;

  return (
    <div className="executive-kpi-chart" role="img" aria-label={summary}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
          <XAxis type="number" domain={[0, baseline]} hide />
          <YAxis type="category" dataKey="name" hide />
          <Tooltip
            allowEscapeViewBox={{ x: false, y: true }}
            content={<SnapshotTooltip />}
            cursor={false}
            wrapperStyle={{ zIndex: 30, pointerEvents: "none" }}
          />
          <Bar
            dataKey="current"
            stackId="snapshot"
            fill="var(--executive-kpi-accent)"
            radius={[4, 0, 0, 4]}
            isAnimationActive={false}
          />
          <Bar
            dataKey="remaining"
            stackId="snapshot"
            fill="var(--executive-kpi-track)"
            radius={[0, 4, 4, 0]}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function LoadingCard({ metric }: { metric: MetricDefinition }) {
  return (
    <article className={`executive-kpi-card executive-kpi-card--${metric.tone}`} aria-busy="true">
      <div className="executive-kpi-card-header">
        <span className="executive-kpi-label">{metric.label}</span>
      </div>
      <div className="executive-kpi-skeleton executive-kpi-skeleton--value" />
      <div className="executive-kpi-skeleton executive-kpi-skeleton--caption" />
      <div className="executive-kpi-skeleton executive-kpi-skeleton--chart" />
    </article>
  );
}

export function AnalyticsDashboard({ state }: { state: ExecutiveKpiState }) {
  if (state.status === "loading") {
    return (
      <div className="executive-kpi-dashboard kpi-grid kpi-grid-cols-1 sm:kpi-grid-cols-2 xl:kpi-grid-cols-4 kpi-gap-3" aria-label="Loading executive queue metrics">
        {METRICS.map((metric) => <LoadingCard key={metric.key} metric={metric} />)}
      </div>
    );
  }

  const isError = state.status === "error";
  const metrics: ExecutiveKpiMetrics = isError
    ? { queueRows: null, nextSteps: null, undecidedJobReviews: null, undecidedMaybeTailor: null }
    : state.metrics;
  const queueRows = safeMetricValue(metrics.queueRows);
  const snapshot = state.status === "ready" ? state.snapshot : undefined;
  const snapshotStatus = snapshot?.status || "fresh";
  const snapshotDate = snapshot?.completedAt
    ? new Intl.DateTimeFormat(undefined, { year: "numeric", month: "short", day: "numeric" }).format(new Date(snapshot.completedAt))
    : "";

  if (!isError && snapshotStatus === "not_generated") {
    return (
      <div className="executive-kpi-not-generated" role="status">
        <span className="executive-kpi-not-generated__icon" aria-hidden="true"><Rows3 size={24} /></span>
        <div>
          <strong>Your personalized job recommendations are not ready yet.</strong>
          <span>Refresh your jobs to analyze the latest opportunities against your preferences and resumes.</span>
        </div>
      </div>
    );
  }

  const snapshotCaption = snapshotStatus === "fresh"
    ? "Current personalized snapshot"
    : `Based on your ${snapshotDate || "latest"} personalized refresh`;
  const snapshotBadge = snapshotStatus === "aging"
    ? "Aging snapshot"
    : snapshotStatus === "stale"
      ? "Stale snapshot"
      : "";

  return (
    <div className="executive-kpi-section">
    <div
      className="executive-kpi-dashboard kpi-grid kpi-grid-cols-1 sm:kpi-grid-cols-2 xl:kpi-grid-cols-4 kpi-gap-3"
      aria-label="Executive queue metrics"
    >
      {METRICS.map((metric) => {
        const value = metrics[metric.key];
        const numericValue = safeMetricValue(value);

        return (
          <article className={`executive-kpi-card executive-kpi-card--${metric.tone}`} key={metric.key}>
            <div className="executive-kpi-card-header">
              <span className="executive-kpi-label">{metric.label}</span>
              {snapshotBadge ? <span className={`executive-kpi-snapshot-badge is-${snapshotStatus}`}>{snapshotBadge}</span> : null}
            </div>
            <strong className="executive-kpi-value">{isError ? "Unavailable" : formatMetric(value)}</strong>
            <span className="executive-kpi-caption">
              {isError ? "Status data could not be loaded" : snapshotCaption}
            </span>
            {isError ? (
              <div className="executive-kpi-error" role="status">Reload the page to try again.</div>
            ) : (
              <SnapshotChart value={numericValue} queueRows={queueRows} label={metric.label} />
            )}
          </article>
        );
      })}
    </div>
    {!isError && (snapshotStatus === "aging" || snapshotStatus === "stale") ? (
      <section className={`executive-snapshot-panel is-${snapshotStatus}`} role="status">
        <span className="executive-snapshot-panel__icon" aria-hidden="true"><FileClock size={25} strokeWidth={2} /></span>
        <div>
          <strong>{snapshotStatus === "stale" ? "Personalized recommendations are out of date" : "Personalized recommendations are getting older"}</strong>
          <span>{snapshotStatus === "stale" ? "You're viewing an old snapshot. Refresh your jobs to generate a new executive queue from the latest shared opportunities." : "Your current recommendations may not include the newest shared opportunities."}</span>
          {snapshotDate ? <small>Last personalized refresh: {snapshotDate}</small> : null}
          {queueRows === 0 && snapshot?.runId ? <small>No matching jobs were found in your latest personalized refresh.</small> : null}
        </div>
      </section>
    ) : null}
    {!isError && snapshotStatus === "fresh" && queueRows === 0 && snapshot?.runId ? (
      <div className="executive-kpi-zero-note" role="status">
        No matching jobs were found in your latest personalized refresh.{snapshotDate ? ` Snapshot completed ${snapshotDate}.` : ""}
      </div>
    ) : null}
    </div>
  );
}
