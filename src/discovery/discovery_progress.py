from src.storage.discovery_store import load_discovery_offsets, save_discovery_offsets


def load_offsets():
    return load_discovery_offsets()


def save_offsets(offsets):
    save_discovery_offsets(offsets)


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
