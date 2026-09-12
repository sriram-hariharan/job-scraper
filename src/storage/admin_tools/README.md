Temporary storage admin/migration tools.
Purpose:
- apply schema artifacts
- one-time backfills
- Postgres rebuild / recovery

Production release upgrades use the finite, additive coordinator:

```bash
python -m src.storage.admin_tools.production_schema_upgrade
python -m src.storage.admin_tools.production_schema_upgrade --apply
```

The first command is the default read-only plan. `--apply` requires
`DATABASE_URL`, validates current schema-owner contracts where available, and
runs only the explicit allowlist in one `ON_ERROR_STOP` transaction.

Keep until: 2026-04-06
If burn-in remains clean after that date, either:
1. keep this folder as permanent admin tooling, or
2. move it to scripts/storage_admin, or
3. delete it.
