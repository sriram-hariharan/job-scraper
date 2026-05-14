from __future__ import annotations

import contextlib
import os
import time
from pathlib import Path
from typing import Iterator


@contextlib.contextmanager
def exclusive_file_lock(
    lock_path: str | Path,
    *,
    timeout_seconds: float = 30.0,
    poll_seconds: float = 0.05,
) -> Iterator[None]:
    """
    Cross-process exclusive lock for shared local files.

    Uses fcntl on Unix/macOS. Falls back to atomic lockfile creation when fcntl
    is unavailable. This is intentionally stdlib-only.
    """
    path = Path(lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import fcntl  # type: ignore

        with path.open("a+", encoding="utf-8") as handle:
            deadline = time.monotonic() + timeout_seconds

            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Timed out waiting for file lock: {path}")
                    time.sleep(poll_seconds)

            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

        return

    except ImportError:
        deadline = time.monotonic() + timeout_seconds
        lock_fd = None

        while True:
            try:
                lock_fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(lock_fd, str(os.getpid()).encode("utf-8"))
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out waiting for file lock: {path}")
                time.sleep(poll_seconds)

        try:
            yield
        finally:
            if lock_fd is not None:
                os.close(lock_fd)
            try:
                path.unlink()
            except FileNotFoundError:
                pass
