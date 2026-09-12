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

11. Install the reviewed systemd artifacts. Preview both scheduler commands
    through the canonical wrapper before enabling timers; `--print-only` does
    not run either job.

    ```bash
    sudo install -o root -g root -m 0644 deploy/systemd/*.service deploy/systemd/*.timer /etc/systemd/system/
    sudo systemctl daemon-reload
    docker compose --env-file .env.production -f docker-compose.prod.yml exec -T web python -u -m src.pipeline.scheduler --job live_pipeline --global-acquisition-only --skip-application-planning --delete-seen-data no --history-path data/scheduler_run_history.jsonl --sync-postgres-run-history --require-postgres-run-history-sync --print-only
    docker compose --env-file .env.production -f docker-compose.prod.yml exec -T web python -u -m src.pipeline.scheduler --job agent_discovery --history-path data/scheduler_run_history.jsonl --sync-postgres-run-history --require-postgres-run-history-sync --print-only
    sudo systemctl enable --now applylens-postgres-backup.timer applylens-live-pipeline.timer applylens-agent-discovery.timer
    systemctl list-timers 'applylens-*'
    ```

    The six-hour live schedule remains global-acquisition-only. It cannot run
    application planning, tailoring, fallback/adjudication, or seen-data reset.
    The discovery schedule is daily. Both append persistent JSONL history and
    require the existing PostgreSQL history sync. A systemd timer does not start
    a second copy while its oneshot service is active; application-level locks
    remain unchanged.

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
sudo systemctl disable --now applylens-live-pipeline.timer applylens-agent-discovery.timer
git switch --detach "${ROLLBACK_SHA}"
docker compose --env-file .env.production -f docker-compose.prod.yml build web
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --no-deps web
docker compose --env-file .env.production -f docker-compose.prod.yml ps
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

Never invoke Compose with `down -v`: it would delete authoritative volumes.
