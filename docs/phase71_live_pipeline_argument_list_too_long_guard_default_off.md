# Phase 71A: Live Pipeline launch argument-list guard

Phase 71A hardens the existing Live Pipeline launch path against
`OSError(7, "Argument list too long")` at subprocess startup.

The change is default-off in behavior: it does not add a new workflow stage, does
not call a provider or LLM, and does not change scraping, retry/cache/dedup,
ranking, scoring, ATS health checks, metrics, artifact creation, resume
mutation, handoff, or application execution behavior.

## Launch contract

- API request handling remains responsible for passing normalized scalar options
  into the service.
- The service admits the run, writes the normal runtime status, and launches the
  existing pipeline subprocess with bounded scalar argv.
- `job_packet_limit=0` remains the explicit "all selected jobs" value.
- Existing flags are preserved, including `job_limit`, `job_packet_limit`,
  `delete_seen_data`, `generate_tailoring`, `generate_llm_tailoring`,
  `refresh_llm_tailoring`, `generate_llm_fallback`, and
  `generate_llm_adjudication`.
- User preference data, including selected role families, target seniority,
  preferred locations, preferred skills, and excluded keywords, is retained in
  the run-scoped launch config/status config and is not passed as child
  environment JSON.
- Selected jobs, job descriptions, planning packets, provider payloads, and
  large JSON blobs must not be passed through subprocess argv.

## Guard behavior

The launch path now records a run-scoped `live_pipeline_launch_config.json`
containing only normalized launch options and explicit markers that it does not
contain selected jobs, job descriptions, planning packets, or large payloads.

Before `Popen`, the service verifies:

- argv byte size is bounded;
- child environment byte size is bounded;
- oversized inherited environment variables are compacted deterministically while
  preserving explicit run-control variables needed by the child process.

If an oversized launch command is detected, the run fails before `Popen` with a
clear status/error instead of surfacing an opaque OS launch failure.

## Safety

Phase 71A does not:

- call a live provider or LLM;
- call network;
- mutate or overwrite resumes;
- create resume artifacts;
- automate ATS actions;
- submit applications;
- enqueue apply/submit actions;
- change scoring formulas or weights.
