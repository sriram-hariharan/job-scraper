"""Shared isolation for cross-cutting authenticated API middleware."""

import pytest


@pytest.fixture(autouse=True)
def _isolate_persistent_bulk_guard(monkeypatch):
    """Endpoint unit tests start with no active Bulk run unless they opt in.

    The dedicated persistent-Bulk tests override this seam to exercise active,
    terminal, unavailable, and owner-independent states. This prevents unrelated
    API unit tests from reaching the developer PostgreSQL instance merely to
    establish their precondition that no Bulk run exists.
    """
    from src.app import api

    monkeypatch.setattr(
        api.bulk_generation_service,
        "active_bulk_generation_guard_state",
        lambda **_kwargs: {},
    )
