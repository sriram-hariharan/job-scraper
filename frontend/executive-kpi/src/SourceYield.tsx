import { useState } from "react";
import { Activity, ChevronDown, Database } from "lucide-react";

export const SOURCE_YIELD_EVENT = "applylens:source-yield-state";

type StatusCounts = { SUCCESS: number; PARTIAL: number; EMPTY: number; FAILED: number };

export type SourceYieldRow = {
  source: string;
  accounts_queried: number;
  scraped_jobs: number;
  title_pass_jobs: number;
  title_reject_jobs: number;
  location_pass_jobs: number;
  location_reject_jobs: number;
  freshness_pass_jobs: number;
  not_recent_jobs: number;
  missing_timestamp_jobs: number;
  final_corpus_jobs: number;
  final_display_jobs: number;
  yield_percent: number;
  raw_job_count: number;
  normalized_job_count: number;
  page_count: number;
  request_count: number;
  retry_count: number;
  partial_result_count: number;
  acquisition_status_counts: StatusCounts;
  timestamp_present_count: number;
  timestamp_missing_count: number;
  description_present_count: number;
  description_missing_count: number;
  canonical_url_present_count: number;
  canonical_url_missing_count: number;
};

export type SourceYieldData = {
  available: boolean;
  run_id: string;
  generated_from: {
    source_health_report: boolean;
    source_acquisition_metrics: boolean;
    current_run_job_corpus: boolean;
  };
  totals: {
    source_count: number;
    accounts_queried: number;
    scraped_jobs: number;
    title_pass_jobs: number;
    location_pass_jobs: number;
    freshness_pass_jobs: number;
    final_corpus_jobs: number;
    final_display_jobs: number;
  };
  sources: SourceYieldRow[];
};

export type SourceYieldState = {
  status: "loading" | "ready" | "error";
  data?: SourceYieldData | null;
  message?: string;
};

export const DEFAULT_SOURCE_YIELD_STATE: SourceYieldState = { status: "loading" };

const numberFormat = new Intl.NumberFormat("en-US");
const count = (value: number | undefined) => numberFormat.format(Number.isFinite(value) ? value || 0 : 0);

function sourceLabel(value: string) {
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ") || "Unknown source";
}

const TARGETS_EXPLANATION = "Company boards, ATS tenants, global feeds, or configured query profiles contacted during this run.";

export function sourceYieldHealth(row: Pick<SourceYieldRow, "acquisition_status_counts">) {
  const statuses = row.acquisition_status_counts;
  if (statuses.SUCCESS > 0) {
    return statuses.FAILED > 0 || statuses.PARTIAL > 0
      ? { label: "Degraded", tone: "degraded" }
      : { label: "Healthy", tone: "healthy" };
  }
  if (statuses.FAILED > 0) return { label: "Failed", tone: "failed" };
  if (statuses.PARTIAL > 0) return { label: "Partial", tone: "partial" };
  if (statuses.EMPTY > 0) return { label: "Empty", tone: "empty" };
  return { label: "Unavailable", tone: "unavailable" };
}

function targetStatusSummary(statuses: StatusCounts) {
  return `Successful targets: ${count(statuses.SUCCESS)}; partial targets: ${count(statuses.PARTIAL)}; empty targets: ${count(statuses.EMPTY)}; failed targets: ${count(statuses.FAILED)}.`;
}

function Funnel({ row }: { row: SourceYieldRow }) {
  const acquired = row.scraped_jobs || row.raw_job_count;
  const steps = [
    ["Acquired", acquired],
    ["Title", row.title_pass_jobs],
    ["U.S.", row.location_pass_jobs],
    ["Fresh", row.freshness_pass_jobs],
    ["Final", row.final_display_jobs],
  ] as const;
  return (
    <div className="source-yield-funnel" aria-label={steps.map(([label, value]) => `${label} ${count(value)}`).join(", ")}>
      {steps.map(([label, value]) => (
        <span key={label} className="source-yield-funnel__step" title={`${label}: ${count(value)}`}>
          <span style={{ width: `${acquired ? Math.max(8, (value / acquired) * 100) : 0}%` }} />
        </span>
      ))}
    </div>
  );
}

function DetailMetric({ label, value }: { label: string; value: number }) {
  return <div><span>{label}</span><strong>{count(value)}</strong></div>;
}

function SourceRow({ row }: { row: SourceYieldRow }) {
  const [expanded, setExpanded] = useState(false);
  const detailId = `source-yield-detail-${row.source.replace(/[^a-z0-9_-]/gi, "-")}`;
  const health = sourceYieldHealth(row);
  const healthSummary = targetStatusSummary(row.acquisition_status_counts);
  const acquired = row.scraped_jobs || row.raw_job_count;
  return (
    <>
      <tr>
        <th scope="row">
          <button
            type="button"
            className="source-yield-source-button"
            aria-expanded={expanded}
            aria-controls={detailId}
            onClick={() => setExpanded((value) => !value)}
          >
            <ChevronDown aria-hidden="true" className={expanded ? "is-expanded" : ""} size={16} />
            <span>{sourceLabel(row.source)}</span>
          </button>
        </th>
        <td>{count(row.accounts_queried)}</td>
        <td><div className="source-yield-acquired"><span>{count(acquired)}</span><Funnel row={row} /></div></td>
        <td>{count(row.title_pass_jobs)}</td>
        <td>{count(row.location_pass_jobs)}</td>
        <td>{count(row.freshness_pass_jobs)}</td>
        <td><strong>{count(row.final_display_jobs)}</strong></td>
        <td><span className="source-yield-percent">{row.yield_percent.toFixed(1)}%</span></td>
        <td><span className={`source-yield-health source-yield-health--${health.tone}`} title={healthSummary}>{health.label}</span></td>
      </tr>
      {expanded && (
        <tr className="source-yield-detail-row">
          <td colSpan={9} id={detailId}>
            <div className="source-yield-detail">
              <div className="source-yield-detail__funnel">
                <span>Conversion funnel</span>
                <Funnel row={row} />
              </div>
              <div className="source-yield-detail__metrics">
                <DetailMetric label="Raw provider jobs" value={row.raw_job_count} />
                <DetailMetric label="Normalized jobs" value={row.normalized_job_count} />
                <DetailMetric label="Final corpus jobs" value={row.final_corpus_jobs} />
                <DetailMetric label="Final displayed jobs" value={row.final_display_jobs} />
                <DetailMetric label="Title rejects" value={row.title_reject_jobs} />
                <DetailMetric label="Location rejects" value={row.location_reject_jobs} />
                <DetailMetric label="Not recent" value={row.not_recent_jobs} />
                <DetailMetric label="Missing timestamps" value={row.missing_timestamp_jobs} />
                <DetailMetric label="Pages" value={row.page_count} />
                <DetailMetric label="Requests" value={row.request_count} />
                <DetailMetric label="Retries" value={row.retry_count} />
                <DetailMetric label="Partial results" value={row.partial_result_count} />
              </div>
              <p className="source-yield-detail__evidence">
                Targets · {count(row.acquisition_status_counts.SUCCESS)} successful / {count(row.acquisition_status_counts.PARTIAL)} partial / {count(row.acquisition_status_counts.EMPTY)} empty / {count(row.acquisition_status_counts.FAILED)} failed · Completeness · timestamp {count(row.timestamp_present_count)} present / {count(row.timestamp_missing_count)} missing · description {count(row.description_present_count)} present / {count(row.description_missing_count)} missing · canonical URL {count(row.canonical_url_present_count)} present / {count(row.canonical_url_missing_count)} missing
              </p>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function StateMessage({ icon, title, body }: { icon: "activity" | "database"; title: string; body: string }) {
  const Icon = icon === "activity" ? Activity : Database;
  return (
    <div className="source-yield-state">
      <Icon aria-hidden="true" size={22} />
      <div><strong>{title}</strong><span>{body}</span></div>
    </div>
  );
}

export function SourceYield({ state }: { state: SourceYieldState }) {
  if (state.status === "loading") {
    return (
      <div className="source-yield-card" aria-label="Loading source yield">
        <div className="source-yield-skeleton source-yield-skeleton--heading" />
        <div className="source-yield-skeleton source-yield-skeleton--table" />
      </div>
    );
  }
  if (state.status === "error") {
    return <div className="source-yield-card"><StateMessage icon="activity" title="Source yield unavailable" body={state.message || "Status could not be loaded."} /></div>;
  }
  const data = state.data;
  if (!data?.available) {
    return <div className="source-yield-card"><StateMessage icon="database" title="Source evidence unavailable" body="Source yield data is unavailable for this run." /></div>;
  }
  if (!data.sources.length) {
    return <div className="source-yield-card"><StateMessage icon="database" title="No source activity" body="The latest completed run produced no source-yield rows." /></div>;
  }

  return (
    <section className="source-yield-card" aria-labelledby="sourceYieldHeading">
      <header className="source-yield-header">
        <div>
          <span className="source-yield-eyebrow">Acquisition intelligence</span>
          <h2 id="sourceYieldHeading">Source Yield</h2>
          <p>Latest completed pipeline run{data.run_id ? ` · ${data.run_id}` : ""}</p>
          <p className="source-yield-coverage-note">Sources shown reflect the latest completed pipeline run.</p>
          <span className="sr-only" id="sourceYieldTargetsHelp">{TARGETS_EXPLANATION}</span>
        </div>
        <div className="source-yield-chips" aria-label="Source yield summary">
          <span><strong>{count(data.totals.source_count)}</strong> sources contributing</span>
          <span title={TARGETS_EXPLANATION} aria-describedby="sourceYieldTargetsHelp"><strong>{count(data.totals.accounts_queried)}</strong> targets queried</span>
          <span><strong>{count(data.totals.scraped_jobs)}</strong> acquired</span>
          <span className="is-accent"><strong>{count(data.totals.final_display_jobs)}</strong> final jobs</span>
        </div>
      </header>
      <div className="source-yield-table-wrap">
        <table className="source-yield-table">
          <caption className="sr-only">Source yield funnel metrics for the latest successful pipeline run</caption>
          <thead><tr>
            <th scope="col">Source</th><th scope="col"><span className="source-yield-target-label" title={TARGETS_EXPLANATION} aria-describedby="sourceYieldTargetsHelp">Targets queried</span></th><th scope="col">Acquired</th>
            <th scope="col">Title pass</th><th scope="col">U.S. pass</th><th scope="col">Fresh 24h</th>
            <th scope="col">Final jobs</th><th scope="col">Yield</th><th scope="col">Health</th>
          </tr></thead>
          <tbody>{data.sources.map((row) => <SourceRow key={row.source} row={row} />)}</tbody>
        </table>
      </div>
    </section>
  );
}
