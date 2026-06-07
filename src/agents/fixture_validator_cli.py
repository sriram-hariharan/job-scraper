"""Manual CLI wrapper for validating one explicitly provided fixture file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from src.agents.fixture_validator import validate_fixture_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate one explicitly provided synthetic fixture file."
    )
    parser.add_argument("--fixture", help="Path to one fixture JSON file.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the validator result as structured JSON.",
    )
    return parser


def _print_input_error(message: str, *, emit_json: bool) -> None:
    if emit_json:
        print(
            json.dumps(
                {
                    "validation_status": "failed",
                    "is_valid": False,
                    "reason_codes": ["invalid_cli_input"],
                    "error": message,
                },
                sort_keys=True,
            )
        )
        return
    print(message, file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.fixture:
        _print_input_error("missing required --fixture path", emit_json=args.json)
        return 2

    fixture_path = Path(args.fixture)
    if fixture_path.is_dir():
        _print_input_error("--fixture must be a file path, not a directory", emit_json=args.json)
        return 2
    if not fixture_path.is_file():
        _print_input_error("--fixture path does not exist", emit_json=args.json)
        return 2

    result = validate_fixture_file(fixture_path)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(result["validation_status"])

    return 0 if result["is_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
