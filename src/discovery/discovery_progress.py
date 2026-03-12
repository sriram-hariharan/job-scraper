import json
from pathlib import Path

OFFSET_FILE = Path("data/discovery_offsets.json")


def load_offsets():
    if not OFFSET_FILE.exists():
        return {}

    try:
        with open(OFFSET_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_offsets(offsets):
    OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OFFSET_FILE, "w", encoding="utf-8") as f:
        json.dump(offsets, f, indent=2)


def get_next_batch(items, source_name, batch_size=100):
    if not items:
        return []

    offsets = load_offsets()
    start = offsets.get(source_name, 0)

    if start >= len(items):
        start = 0

    end = start + batch_size
    batch = items[start:end]

    if not batch:
        start = 0
        end = min(batch_size, len(items))
        batch = items[start:end]

    next_start = end
    if next_start >= len(items):
        next_start = 0

    offsets[source_name] = next_start
    save_offsets(offsets)

    return batch