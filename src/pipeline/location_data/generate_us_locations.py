from __future__ import annotations

import argparse
import csv
import io
import json
import re
import unicodedata
import zipfile
from pathlib import Path

import pycountry


SOURCE_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2025_Gazetteer/2025_Gaz_place_national.zip"
)
SOURCE_FILE = "2025_Gaz_place_national.txt"
ARTIFACT_VERSION = "us-census-gazetteer-places-2025-v1"
PLACE_SUFFIX_RE = re.compile(
    r"\s+(?:city|town|village|borough|municipality|CDP|consolidated government|"
    r"unified government|metro government|balance|zona urbana|comunidad)$",
    re.IGNORECASE,
)


def _normalized_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def build_artifact(source_zip: Path) -> dict:
    state_names = {
        subdivision.code.split("-", 1)[1]: subdivision.name
        for subdivision in pycountry.subdivisions.get(country_code="US")
    }
    with zipfile.ZipFile(source_zip) as archive:
        with archive.open(SOURCE_FILE) as raw_file:
            rows = list(
                csv.DictReader(
                    io.TextIOWrapper(raw_file, encoding="utf-8-sig"),
                    delimiter="|",
                )
            )

    places = []
    seen = set()
    for row in rows:
        state_code = str(row.get("USPS") or "").strip().upper()
        raw_name = str(row.get("NAME") or "").strip()
        city_name = PLACE_SUFFIX_RE.sub("", raw_name).strip()
        normalized_name = _normalized_name(city_name)
        key = (state_code, normalized_name)
        if not state_code or not normalized_name or key in seen:
            continue
        if state_code not in state_names:
            raise ValueError(f"Missing US subdivision mapping for {state_code!r}.")
        seen.add(key)
        places.append([state_code, city_name, normalized_name])

    source_codes = sorted({str(row.get("USPS") or "").strip().upper() for row in rows})
    return {
        "version": ARTIFACT_VERSION,
        "source": {
            "organization": "United States Census Bureau",
            "year": 2025,
            "file": SOURCE_FILE,
            "url": SOURCE_URL,
        },
        "states": [{"code": code, "name": state_names[code]} for code in source_codes],
        "places": places,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the compact ApplyLens US location artifact."
    )
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args()

    payload = build_artifact(args.source_zip)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "artifact_version": payload["version"],
                "place_entries": len(payload["places"]),
                "state_entries": len(payload["states"]),
                "output_bytes": args.output_json.stat().st_size,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
