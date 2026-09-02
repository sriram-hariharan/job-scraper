from __future__ import annotations

import argparse

from src.app.bulk_generation_service import run_bulk_generation_worker


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one persisted Bulk Generate batch.")
    parser.add_argument("--owner-user-id", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    return run_bulk_generation_worker(owner_user_id=args.owner_user_id, run_id=args.run_id)


if __name__ == "__main__":
    raise SystemExit(main())
