#!/usr/bin/env python3
"""Explicitly install an initial Fernet-compatible key into an env file."""

from __future__ import annotations

import argparse
import base64
import os
import tempfile
from pathlib import Path

KEY_NAME = "APPLYLENS_AI_CREDENTIAL_FERNET_KEYS"


def _install_key(env_path: Path) -> None:
    if not env_path.exists() or not env_path.is_file():
        raise SystemExit(f"Environment file does not exist: {env_path}")

    source = env_path.read_text(encoding="utf-8")
    if any(line.strip().startswith(f"{KEY_NAME}=") for line in source.splitlines()):
        raise SystemExit(
            f"{KEY_NAME} is already present; refusing to replace or rotate it."
        )

    key = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")
    updated = source
    if updated and not updated.endswith("\n"):
        updated += "\n"
    updated += f"{KEY_NAME}={key}\n"

    env_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{env_path.name}.",
        suffix=".tmp",
        dir=str(env_path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, env_path)
        os.chmod(env_path, 0o600)
    finally:
        temp_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install an initial ApplyLens Fernet key without printing it."
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env.production"))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Required explicit authorization to modify the env file.",
    )
    args = parser.parse_args()

    if not args.apply:
        print(f"plan=install_initial_secret env_file={args.env_file} key={KEY_NAME}")
        print("apply=false; no file was changed")
        return 0

    _install_key(args.env_file)
    print(f"installed=true env_file={args.env_file} key={KEY_NAME}")
    print("secret_value_printed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
