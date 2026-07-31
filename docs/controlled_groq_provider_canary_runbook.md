# Controlled Groq Provider Canary Runbook

## Scope

This runbook governs a future operator-authorized, four-call Groq canary. It
does not authorize execution, production routing, fallback, application
actions, ATS actions, OpenAI, Gemini, or publication of a model winner.

## Preparation and execution sequence

1. Verify that the repository and index are clean.
2. Verify the exact approved branch and committed HEAD.
3. Validate the separately operator-created authorization and pricing inputs.
4. Verify that the result and checkpoint paths are ignored, absent, distinct,
   non-symlinked, and under the approved benchmark-output directory.
5. Verify both approved Groq models are available immediately before execution.
6. Reconfirm the approved pricing source and validity window immediately before
   execution.
7. Confirm the deterministic schedule contains exactly four calls: two for
   each approved Groq model.
8. Confirm serial concurrency one, fallback false, harness retries zero, SDK retries zero,
   and a 30-second timeout.
9. Confirm no pipeline, graph, provider, benchmark, scheduler, worker, child,
   timer, or repository-owned process is active.
10. Begin only the separately authorized serial execution.
11. Stop on the first hard failure, missing usage, unauthorized behavior, or
    ambiguous timeout. Never retry or resume an ambiguous key automatically.
12. Review only the redacted normalized result and bounded checkpoint.
13. Delete ignored result and checkpoint artifacts within seven days.
14. Do not alter provider defaults, fallback, production routing, application
    behavior, or ATS behavior.
15. Do not publish a model winner or routing decision from four calls.

## Permanent boundaries

The canary retains no raw provider envelope, header, request identifier,
reasoning trace, raw provider error, or separately exposed prompt. It uses
observed latency and token usage only. A result cannot activate production or
transfer authority.
