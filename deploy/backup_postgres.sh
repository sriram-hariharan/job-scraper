#!/usr/bin/env bash
set -euo pipefail

umask 077

readonly BACKUP_DIR="/home/deploy/backups/job-scraper/postgres"
readonly RETENTION_DAYS="14"
readonly COMPOSE_FILE="docker-compose.prod.yml"

if [[ ! -f "${COMPOSE_FILE}" || ! -f ".env.production" ]]; then
  echo "Run this script from /home/deploy/apps/job-scraper with .env.production present." >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"

timestamp="$(date -u +'%Y%m%dT%H%M%SZ')"
final_path="${BACKUP_DIR}/job_scraper_ops_${timestamp}.sql.gz"
if [[ -e "${final_path}" ]]; then
  echo "Backup destination already exists; refusing to overwrite it: ${final_path}" >&2
  exit 1
fi
temporary_path="$(mktemp "${BACKUP_DIR}/.job_scraper_ops_${timestamp}.sql.gz.tmp.XXXXXX")"

cleanup() {
  rm -f -- "${temporary_path}"
}
trap cleanup EXIT

docker compose --env-file .env.production -f "${COMPOSE_FILE}" exec -T db \
  sh -c 'exec pg_dump --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --format=plain --no-owner --no-privileges' \
  | gzip -9 > "${temporary_path}"

if [[ ! -s "${temporary_path}" ]]; then
  echo "Backup output is empty; refusing to publish it." >&2
  exit 1
fi

uncompressed_bytes="$(gzip -cd -- "${temporary_path}" | wc -c | tr -d '[:space:]')"
if [[ ! "${uncompressed_bytes}" =~ ^[1-9][0-9]*$ ]]; then
  echo "Backup contains no SQL payload; refusing to publish it." >&2
  exit 1
fi

chmod 600 "${temporary_path}"
mv -- "${temporary_path}" "${final_path}"
trap - EXIT

find "${BACKUP_DIR}" -maxdepth 1 -type f \
  -name 'job_scraper_ops_*.sql.gz' -mtime +"${RETENTION_DAYS}" -delete

echo "PostgreSQL backup completed: ${final_path}"
echo "Retention: ${RETENTION_DAYS} days"
