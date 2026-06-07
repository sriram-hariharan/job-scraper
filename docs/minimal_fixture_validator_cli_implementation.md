# Minimal Fixture Validator CLI Implementation

Doc path: `docs/minimal_fixture_validator_cli_implementation.md`

Phase 77A is minimal fixture validator CLI implementation only. Fixture validator CLI added: `src/agents/fixture_validator_cli.py`. Fixture validator CLI tests added: `tests/test_fixture_validator_cli.py`. The CLI is manual-only. The CLI requires explicit fixture file path input only. The CLI supports JSON output. The CLI does not discover fixture directories. The CLI does not execute fixtures. The CLI does not write files. The CLI does not mutate. The CLI does not call DB. The CLI does not call network. The CLI does not call subprocess. The CLI does not call workflow_runner. The CLI does not call generator, simulator, proposal planner, app services, queue, DB, or application submission. The CLI is not wired into runtime. The CLI is not wired into live planning. The CLI is not wired into workflow_runner. No additional fixture payload files are added. The existing fixture remains synthetic and inert. No runtime failure-mode tests are added. No storage integration tests are added. No DB schema file is added. No migration is added. No SQL DDL is added. No storage API is added. No DB writes are added. No live execution is enabled. No mutation is enabled. No approval API/storage is enabled. No queue updates are added. No application submission is added.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Implementation Scope

- Minimal fixture validator CLI implementation: `PASS`
- Fixture validator CLI: `PASS`
- Fixture validator CLI tests: `PASS`
- Runtime integration: `NO_GO`
- Workflow runner integration: `NO_GO`
- Live planning integration: `NO_GO`
- Additional fixture payload files: `NO_GO`
- Runtime failure-mode tests: `NO_GO`
- Storage integration tests: `NO_GO`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## CLI Boundary

- manual-only
- explicit fixture file path input only
- no directory discovery
- no fixture execution
- no writes
- no DB calls
- no network calls
- no subprocess calls
- no queue mutation
- no application submission
- no generator/simulator/planner/workflow_runner/app-service invocation
- no runtime integration

## CLI Command Contract

- `python -m src.agents.fixture_validator_cli --fixture <path> --json`
- exit code `0`: valid fixture
- exit code `1`: invalid fixture
- exit code `2`: usage/input error

## Test Coverage

- valid `safe_execution_request_minimal.json` returns exit code `0`
- valid CLI JSON output parses
- JSON output includes `validation_status=passed`
- JSON output includes `is_valid=true`
- JSON output includes `did_execute_fixture=false`
- JSON output includes `did_mutate_production=false`
- JSON output includes `did_write_db=false`
- invalid tmp fixture with `allow_db_write=true` returns exit code `1`
- invalid tmp fixture includes `db_write_not_allowed`
- missing `--fixture` returns exit code `2`
- directory path passed to `--fixture` returns exit code `2`
- directory path passed to `--fixture` does not discover files
- CLI test does not modify real fixture file
- fixture directory still contains only `.gitkeep` and `safe_execution_request_minimal.json`
- CLI has no runtime imports or side-effect imports

## Runtime Non-Integration Confirmation

- `workflow_runner.py` does not import/call fixture_validator_cli
- `run_application_planning.py` does not import/call fixture_validator_cli
- `application_execution_queue.py` does not import/call fixture_validator_cli
- `src/app/services.py` does not import/call fixture_validator_cli
- orchestrator harness does not import/call fixture_validator_cli
- proposal planner does not import/call fixture_validator_cli
- dry-run simulator does not import/call fixture_validator_cli
- read-only generator does not import/call fixture_validator_cli

## Forbidden Next-Step Shortcuts

- do not wire CLI into runtime next without explicit approval
- do not wire validator into workflow_runner next without explicit approval
- do not wire validator into live planning next without explicit approval
- do not add runtime failure-mode tests next
- do not add storage integration tests next
- do not add DB schema files next
- do not add migrations next
- do not add SQL DDL next
- do not add storage APIs next
- do not add approval APIs next
- do not add mutation APIs next
- do not add DB writes next
- do not add live queue updates next
- do not start application submission automation next
- do not enable workflow_runner live execution next

## Recommended Next Phase

Recommended next phase: 77B minimal fixture validator CLI implementation final audit and merge gate.

After 77B: 78A minimal fixture validator CLI implementation release safety checkpoint, docs/tests only.

The 78A release safety checkpoint is tracked in `docs/minimal_fixture_validator_cli_implementation_release_safety_checkpoint.md`.
