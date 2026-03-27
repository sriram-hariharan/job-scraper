from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple


ARCHIVE_DIR = Path("outputs/_archive/application_planning_phase7")
JOB_PACKET_DIR = Path("outputs/application_planning/job_packets")
DEFAULT_BASE_MANIFEST = ARCHIVE_DIR / "phase7_patch_batch_manifest.json"

EXCLUDED_PACKET_PREFIXES: Tuple[str, ...] = (
    "_debug_",
    "_phase",
)

EXCLUDED_PACKET_BASENAMES: Tuple[str, ...] = (
    "_debug_fast_regen_test",
    "_phase1a_bullet_lineage_test",
    "_phase4c_exact_signal_validation",
    "_phase4c_live_validation",
)


def _is_excluded_packet(packet_path: Path) -> bool:
    stem = packet_path.stem.strip()

    if stem in EXCLUDED_PACKET_BASENAMES:
        return True

    for prefix in EXCLUDED_PACKET_PREFIXES:
        if stem.startswith(prefix):
            return True

    return False


def _tailoring_paths_for_packet(packet_json: Path) -> Dict[str, str]:
    stem = packet_json.stem
    return {
        "packet_json": str(packet_json),
        "output_json": str(packet_json.with_name(f"{stem}__tailoring.json")),
        "output_md": str(packet_json.with_name(f"{stem}__tailoring.md")),
        "output_llm_json": str(packet_json.with_name(f"{stem}__tailoring_llm.json")),
    }


def _collect_packet_jsons(packet_dir: Path) -> List[Path]:
    if not packet_dir.exists():
        raise FileNotFoundError(f"Packet directory not found: {packet_dir}")

    packet_paths = sorted(
        p for p in packet_dir.glob("*.json")
        if not p.name.endswith("__tailoring.json")
        and not p.name.endswith("__tailoring_llm.json")
        and not _is_excluded_packet(p)
    )
    return packet_paths


def _build_manifest_items(packet_paths: List[Path]) -> List[Dict[str, str]]:
    return [_tailoring_paths_for_packet(p) for p in packet_paths]


def _load_manifest_items(base_manifest: Path) -> List[Dict[str, str]]:
    if not base_manifest.exists():
        raise FileNotFoundError(f"Base manifest not found: {base_manifest}")

    payload = json.loads(base_manifest.read_text())
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ValueError(f"Base manifest has invalid items payload: {base_manifest}")
    return items


def _filter_existing_manifest_items(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    filtered: List[Dict[str, str]] = []

    for item in items:
        packet_json = Path(str(item.get("packet_json", "") or "").strip())
        if not packet_json:
            continue
        if _is_excluded_packet(packet_json):
            continue
        filtered.append(
            {
                "packet_json": str(item.get("packet_json", "") or "").strip(),
                "output_json": str(item.get("output_json", "") or "").strip(),
                "output_md": str(item.get("output_md", "") or "").strip(),
                "output_llm_json": str(item.get("output_llm_json", "") or "").strip(),
            }
        )

    return filtered


def _write_manifest(output_path: Path, items: List[Dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "items": items,
        "count": len(items),
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a deterministic clean Phase 7 patch batch manifest excluding debug/test packets."
    )
    parser.add_argument(
        "--packet-dir",
        default=str(JOB_PACKET_DIR),
        help="Directory containing packet JSON files when no base manifest is used.",
    )
    parser.add_argument(
        "--base-manifest",
        default=str(DEFAULT_BASE_MANIFEST),
        help="Existing manifest to clean. If present, this is preferred over scanning the packet directory.",
    )
    parser.add_argument(
        "--output-manifest",
        default=str(ARCHIVE_DIR / "phase7_patch_batch_manifest_clean.json"),
        help="Where to write the rebuilt clean manifest JSON.",
    )
    args = parser.parse_args()

    packet_dir = Path(args.packet_dir)
    base_manifest = Path(args.base_manifest)
    output_manifest = Path(args.output_manifest)

    source_mode = ""
    if base_manifest.exists():
        source_mode = "base_manifest"
        base_items = _load_manifest_items(base_manifest)
        items = _filter_existing_manifest_items(base_items)
    else:
        source_mode = "packet_scan"
        packet_paths = _collect_packet_jsons(packet_dir)
        items = _build_manifest_items(packet_paths)

    _write_manifest(output_manifest, items)

    print(f"source_mode={source_mode}")
    print(f"packet_dir={packet_dir}")
    print(f"base_manifest={base_manifest}")
    print(f"output_manifest={output_manifest}")
    print(f"item_count={len(items)}")
    print("excluded_prefixes=" + ",".join(EXCLUDED_PACKET_PREFIXES))
    print("excluded_basenames=" + ",".join(EXCLUDED_PACKET_BASENAMES))


if __name__ == "__main__":
    main()