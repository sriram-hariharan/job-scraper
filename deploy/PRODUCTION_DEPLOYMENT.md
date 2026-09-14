# ApplyLens production deployment

## Topology and invariants

Production is the Hetzner Ubuntu host `job-scraper-prod-1`, operated over SSH as
`deploy`. The repository is `/home/deploy/apps/job-scraper`. Caddy terminates
public traffic for `https://applylensjobs.com` and proxies to the single web
replica bound to `127.0.0.1:8000`.

Docker Compose owns the web process, PostgreSQL 18, and Redis 7. PostgreSQL is
authoritative and retains its existing `job-scraper_postgres_data` volume.
Redis is cache/lock infrastructure and is not authoritative. The web runtime's
pipeline-run, data, and output paths use named volumes. Every Compose command
must explicitly load `.env.production`.

`/health` is a web-process liveness check. It does not prove PostgreSQL or Redis
readiness; check those services independently.

## Immutable provider qualification authority

Production provider routing reads the approved V1 qualification snapshot from
`/app/src/evaluation/production_provider_qualification_registry_v1.json`. The
file is tracked in the image and must have both raw and repository-canonical
SHA-256 `6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f`.
The persistent `/app/outputs` volume remains evaluation/runtime state and cannot
override this packaged routing authority. Skill Extraction and Job Fit continue
to use their separately tracked renderer-bound V2 authorities.

After building an image and before recreating the web service, verify the
packaged file and resolve the owner-independent routing inventory without
provider credentials or `/app/outputs/provider_benchmark/provider-qualification-registry.json`:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm --no-deps -e GROQ_API_KEY= -e OPENAI_API_KEY= -e GEMINI_API_KEY= web python -c 'from hashlib import sha256; from pathlib import Path; from src.app.provider_model_routing_service import list_provider_model_routing_statuses; p=Path("/app/src/evaluation/production_provider_qualification_registry_v1.json"); assert sha256(p.read_bytes()).hexdigest()=="6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f"; routes=list_provider_model_routing_statuses()["workloads"]; assert len(routes)==12; assert sum(r["execution_mode"]=="qualified_provider_model" for r in routes)==9; assert sum(r["execution_mode"]=="deterministic" for r in routes)==3'
```

This verification is read-only. Do not regenerate the registry during deploy,
copy an artifact from `/app/outputs`, or treat deployment as authorization for
provider calls or qualification changes. The approval record is
`docs/provider_qualification_registry_v1_production_consumption_approval_attestation.md`.

## Release procedure

Run commands from `/home/deploy/apps/job-scraper`. Set `TARGET_SHA` to the exact
reviewed release commit and record all preflight output in the operator log.

1. Confirm the host, user, working tree, current revision, free disk space, and
   Compose configuration. Do not proceed from a dirty checkout.

   ```bash
   hostname
   id -un
   pwd
   git status --short
   git rev-parse HEAD
   df -h
   docker compose --env-file .env.production -f docker-compose.prod.yml config --quiet
   ```

2. Take a fresh database backup before changing code or schema. The backup is a
   gzip-compressed SQL dump under
   `/home/deploy/backups/job-scraper/postgres`, mode `0600`, with 14-day
   retention.

   ```bash
   ./deploy/backup_postgres.sh
   ```

3. Capture the rollback point: current Git SHA, current web image ID, Compose
   status, and the new backup filename.

   ```bash
   git rev-parse HEAD
   docker compose --env-file .env.production -f docker-compose.prod.yml images web
   docker compose --env-file .env.production -f docker-compose.prod.yml ps
   ls -lt /home/deploy/backups/job-scraper/postgres | head
   ```

4. Fetch and verify the exact target commit, then place the checkout at that
   reviewed commit. Never deploy an unreviewed moving branch tip.

   ```bash
   git fetch --prune origin
   git cat-file -e "${TARGET_SHA}^{commit}"
   git switch --detach "${TARGET_SHA}"
   git status --short
   ```

5. Build the new web image while the old container continues serving.

   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml build web
   ```

6. Run the schema coordinator in its default read-only plan mode. Review the
   ordered file list and SHA-256 values. The coordinator has a finite additive
   allowlist; it excludes pgvector and default-off durable/agentic schemas.

   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml run --rm --no-deps web python -m src.storage.admin_tools.production_schema_upgrade
   ```

7. After the plan is approved and the fresh backup is confirmed, explicitly
   apply the same allowlist in one `ON_ERROR_STOP` transaction.

   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml run --rm --no-deps web python -m src.storage.admin_tools.production_schema_upgrade --apply
   ```

8. Install the required non-committed per-user credential encryption key if it
   is not already present. The command modifies only `.env.production`, refuses
   to replace an existing key, sets mode `0600`, and does not print the secret.

   ```bash
   python3 deploy/install_fernet_key.py --env-file .env.production
   python3 deploy/install_fernet_key.py --env-file .env.production --apply
   ```

9. Recreate only the web service. Do not remove volumes and do not recreate a
   healthy database or Redis service unnecessarily.

   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml up -d --no-deps web
   ```

10. Check web liveness, then independently check PostgreSQL and Redis.

    ```bash
    docker compose --env-file .env.production -f docker-compose.prod.yml ps
    curl --fail --silent --show-error http://127.0.0.1:8000/health
    docker compose --env-file .env.production -f docker-compose.prod.yml exec -T db sh -c 'pg_isready --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"'
    docker compose --env-file .env.production -f docker-compose.prod.yml exec -T redis redis-cli ping
    ```

11. Transition the three reviewed systemd timers to their calendar-only UTC
    schedules. Capture the existing state first, and perform the transition in
    a window that ends before the next intended calendar occurrence.

    ```bash
    systemctl show applylens-live-pipeline.timer applylens-postgres-backup.timer applylens-agent-discovery.timer --property=ActiveState,SubState,LastTriggerUSec,NextElapseUSecMonotonic,NextElapseUSecRealtime,TimersMonotonic,TimersCalendar > /tmp/applylens-timers-before-transition.txt
    systemctl list-timers --all 'applylens-*' >> /tmp/applylens-timers-before-transition.txt
    systemctl is-active applylens-live-pipeline.service applylens-postgres-backup.service applylens-agent-discovery.service
    ```

    If any ApplyLens oneshot service is active, wait for it to finish and
    confirm its result; do not stop a running service merely to replace its
    timer. Then stop only the three ApplyLens timers. While they are stopped,
    clear only their persistent timer timestamp state so the former contract
    cannot influence the new `Persistent=true` calendar contract.

    ```bash
    sudo systemctl stop applylens-live-pipeline.timer applylens-postgres-backup.timer applylens-agent-discovery.timer
    systemctl is-active applylens-live-pipeline.timer applylens-postgres-backup.timer applylens-agent-discovery.timer
    sudo systemctl clean --what=state applylens-live-pipeline.timer
    sudo systemctl clean --what=state applylens-postgres-backup.timer
    sudo systemctl clean --what=state applylens-agent-discovery.timer
    sudo install -o root -g root -m 0644 deploy/systemd/*.service deploy/systemd/*.timer /etc/systemd/system/
    sudo systemd-analyze verify /etc/systemd/system/applylens-live-pipeline.service /etc/systemd/system/applylens-live-pipeline.timer /etc/systemd/system/applylens-postgres-backup.service /etc/systemd/system/applylens-postgres-backup.timer /etc/systemd/system/applylens-agent-discovery.service /etc/systemd/system/applylens-agent-discovery.timer
    systemd-analyze calendar '*-*-* 04,10,16,22:42:00 UTC'
    systemd-analyze calendar '*-*-* 04:47:00 UTC'
    systemd-analyze calendar '*-*-* 04:57:00 UTC'
    docker compose --env-file .env.production -f docker-compose.prod.yml exec -T web python -u -m src.pipeline.scheduler --job live_pipeline --global-acquisition-only --skip-application-planning --delete-seen-data no --history-path data/scheduler_run_history.jsonl --sync-postgres-run-history --require-postgres-run-history-sync --print-only
    docker compose --env-file .env.production -f docker-compose.prod.yml exec -T web python -u -m src.pipeline.scheduler --job agent_discovery --history-path data/scheduler_run_history.jsonl --sync-postgres-run-history --require-postgres-run-history-sync --print-only
    sudo systemctl daemon-reload
    transition_started="$(date --iso-8601=seconds)"
    sudo systemctl enable applylens-postgres-backup.timer applylens-live-pipeline.timer applylens-agent-discovery.timer
    sudo systemctl start applylens-postgres-backup.timer applylens-live-pipeline.timer applylens-agent-discovery.timer
    systemctl show applylens-live-pipeline.timer applylens-postgres-backup.timer applylens-agent-discovery.timer --property=ActiveState,SubState,TimersCalendar,TimersMonotonic,NextElapseUSecRealtime
    systemctl list-timers --all 'applylens-*'
    journalctl --since "${transition_started}" --unit=applylens-live-pipeline.service --unit=applylens-postgres-backup.service --unit=applylens-agent-discovery.service --no-pager
    ```

    The six-hour live schedule remains global-acquisition-only. It cannot run
    application planning, tailoring, fallback/adjudication, or seen-data reset.
    The discovery schedule is daily. Both append persistent JSONL history and
    require the existing PostgreSQL history sync. A systemd timer does not start
    a second copy while its oneshot service is active; application-level locks
    remain unchanged.

    The exact schedules are:

    - live pipeline: `OnCalendar=*-*-* 04,10,16,22:42:00 UTC`;
    - PostgreSQL backup: `OnCalendar=*-*-* 04:47:00 UTC`;
    - agent discovery: `OnCalendar=*-*-* 04:57:00 UTC`.

    Every timer retains `Persistent=true`. After genuine downtime, systemd may
    therefore perform one catch-up activation for a calendar occurrence that
    was missed while the timer was inactive. This is intentional. Old timer
    timestamp state is not authoritative for the new contract, which is why it
    is captured and then cleaned only after the three timers are stopped.

    Do not add `OnActiveSec`, `OnBootSec`, `OnStartupSec`,
    `OnUnitActiveSec`, or `OnUnitInactiveSec`. The demonstrated manager re-exec
    re-armed the old activation-relative `OnActiveSec` legs without a reboot;
    `OnBootSec` is also unsafe when installing on a long-running host whose
    boot-relative deadline has already passed. Each production `[Timer]`
    section must contain only `OnCalendar`, `Persistent`, and `Unit`.

    Before leaving automatic scheduling enabled, confirm that `TimersCalendar`
    contains only the reviewed expression, `TimersMonotonic` is empty, and
    `NextElapseUSecRealtime` plus `systemctl list-timers` show a future intended
    occurrence. The post-start journal query must show that no ApplyLens service
    unexpectedly ran during the transition. At the first real scheduled times,
    verify the timer and service results, scheduler JSONL/PostgreSQL history for
    the two scheduler jobs, and the dated compressed PostgreSQL backup artifact.

    `systemctl daemon-reexec` is not part of normal deployment. Reproducing the
    manager re-exec regression requires a maintenance window and must be
    separately authorized, with the real ApplyLens timers stopped or inert
    temporary probe units used instead.

12. Perform authenticated user smoke checks through `applylensjobs.com`, inspect
    Caddy/web logs, confirm volume mounts, and verify timer state. Do not trigger
    live providers merely as a deployment smoke test.

## Rollback

Stop the new timers first if scheduler behavior is suspect. Record current logs
and state, then disable only the affected timers. Return the checkout to the
captured SHA or rebuild the captured image, and recreate only `web` with the
same explicit Compose arguments. The production schema upgrade is additive and
is designed to remain backward-compatible; do not drop tables or restore the
database as a routine code rollback.

If data restoration is genuinely required, stop writers, preserve the failed
database, and use a separately reviewed manual restore procedure against the
specific pre-release backup. This repository never restores automatically.

```bash
sudo systemctl disable --now applylens-live-pipeline.timer applylens-postgres-backup.timer applylens-agent-discovery.timer
git switch --detach "${ROLLBACK_SHA}"
docker compose --env-file .env.production -f docker-compose.prod.yml build web
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --no-deps web
docker compose --env-file .env.production -f docker-compose.prod.yml ps
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

Never invoke Compose with `down -v`: it would delete authoritative volumes.
