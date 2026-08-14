import json
import re

import pytest

from src.storage import discovery_store
from src.utils.file_loader import load_lines


class _MemoryDiscoveryDatabase:
    def __init__(self):
        self.records = {
            ("ashby", "acme"): {
                "metadata_json": {"source": "seed", "unknown": {"keep": True}},
                "first_seen_at": "first-acme",
                "last_seen_at": "last-acme",
            },
            ("ashby", "legacy"): {
                "metadata_json": {"source": "legacy"},
                "first_seen_at": "first-legacy",
                "last_seen_at": "last-legacy",
            },
            ("ashby", "other"): {
                "metadata_json": {"source": "network"},
                "first_seen_at": "first-other",
                "last_seen_at": "last-other",
            },
            ("lever", "acme"): {
                "metadata_json": {"source": "lever-seed"},
                "first_seen_at": "first-lever",
                "last_seen_at": "last-lever",
            },
        }
        self.crawl_state = {
            "acme": {"last_scraped": 123.0},
            "legacy": {"last_scraped": 456.0},
        }
        self.mutation_sql = []

    def query(self, sql):
        if sql.startswith("WITH company_rows AS"):
            provider_match = re.search(r"WHERE ats = '([^']*)'", sql)
            provider = provider_match.group(1) if provider_match else None
            rows = []
            for (ats, company), record in sorted(self.records.items()):
                if provider is None or ats == provider:
                    rows.append(
                        {
                            "company": company,
                            "metadata_json": record["metadata_json"],
                        }
                    )
            return {"rows": rows}

        if sql.startswith("WITH existing AS MATERIALIZED"):
            self.mutation_sql.append(sql)
            target = re.search(
                r"WHERE ats = '([^']*)'\s+AND company = '([^']*)'",
                sql,
            )
            assert target is not None
            key = target.groups()
            record = self.records.get(key)
            if record is None:
                return {"found": False, "changed": False}

            lifecycle_match = re.search(
                r"'(\{\"disabled\":(?:true|false),\"reason\":.*?\})'::jsonb",
                sql,
            )
            assert lifecycle_match is not None
            lifecycle = json.loads(lifecycle_match.group(1))
            changed = record["metadata_json"].get("acquisition_lifecycle") != lifecycle
            if changed:
                record["metadata_json"] = {
                    **record["metadata_json"],
                    "acquisition_lifecycle": lifecycle,
                }
            return {"found": True, "changed": changed}

        raise AssertionError(f"unexpected SQL owner: {sql[:80]}")


@pytest.fixture
def lifecycle_store(monkeypatch):
    database = _MemoryDiscoveryDatabase()
    cache = {}
    deleted = []
    cache_writes = []

    monkeypatch.setattr(discovery_store, "init_discovery_store", lambda: None)
    monkeypatch.setattr(discovery_store, "_run_psql_json_query", database.query)
    monkeypatch.setattr(
        discovery_store,
        "_cache_get_list_safe",
        lambda key: cache.get(key),
    )

    def cache_set(key, values):
        cache[key] = sorted(values)
        cache_writes.append((key, tuple(sorted(values))))

    def cache_delete(*keys):
        deleted.extend(keys)
        for key in keys:
            cache.pop(key, None)

    monkeypatch.setattr(discovery_store, "_cache_set_list_safe", cache_set)
    monkeypatch.setattr(discovery_store, "_cache_delete_safe", cache_delete)
    return database, cache, deleted, cache_writes


def _set_disabled(provider="ashby", company="acme", disabled=True, reason="stale"):
    return discovery_store.set_discovered_ats_company_acquisition_disabled(
        provider,
        company,
        disabled=disabled,
        reason=reason,
    )


def test_legacy_default_inclusion_and_explicit_disabled_visibility(lifecycle_store):
    database, _, _, cache_writes = lifecycle_store

    assert discovery_store.get_discovered_ats_companies("ashby") == {
        "acme",
        "legacy",
        "other",
    }
    assert _set_disabled()["changed"] is True
    assert discovery_store.get_discovered_ats_companies("ashby") == {
        "legacy",
        "other",
    }
    writes_before_inspection = len(cache_writes)
    assert discovery_store.get_discovered_ats_companies(
        "ashby",
        include_disabled=True,
    ) == {"acme", "legacy", "other"}
    assert len(cache_writes) == writes_before_inspection
    assert database.records[("ashby", "legacy")]["metadata_json"] == {
        "source": "legacy"
    }


def test_disable_and_enable_are_idempotent_and_refresh_effective_cache(lifecycle_store):
    _, cache, deleted, _ = lifecycle_store
    provider_key = discovery_store._ats_companies_cache_key("ashby")
    all_key = discovery_store._ats_companies_cache_key("")

    assert "acme" in discovery_store.get_discovered_ats_companies("ashby")
    assert provider_key in cache
    assert _set_disabled() == {
        "found": True,
        "changed": True,
        "acquisition_disabled": True,
    }
    assert _set_disabled() == {
        "found": True,
        "changed": False,
        "acquisition_disabled": True,
    }
    assert "acme" not in discovery_store.get_discovered_ats_companies("ashby")
    assert deleted.count(provider_key) == 2
    assert deleted.count(all_key) == 2

    assert _set_disabled(disabled=False) == {
        "found": True,
        "changed": True,
        "acquisition_disabled": False,
    }
    assert _set_disabled(disabled=False) == {
        "found": True,
        "changed": False,
        "acquisition_disabled": False,
    }
    assert "acme" in discovery_store.get_discovered_ats_companies("ashby")
    assert deleted.count(provider_key) == 4
    assert deleted.count(all_key) == 4


def test_lifecycle_mutation_is_exact_provider_scoped_and_never_inserts(lifecycle_store):
    database, _, deleted, _ = lifecycle_store
    original_keys = set(database.records)

    assert _set_disabled(provider="Ashby")["found"] is False
    assert _set_disabled(company="Acme")["found"] is False
    assert _set_disabled(provider="unknown", company="missing")["found"] is False
    assert set(database.records) == original_keys
    assert deleted == []

    assert _set_disabled()["found"] is True
    assert database.records[("ashby", "acme")]["metadata_json"][
        "acquisition_lifecycle"
    ]["disabled"] is True
    assert "acquisition_lifecycle" not in database.records[("lever", "acme")][
        "metadata_json"
    ]


def test_reason_is_sanitized_bounded_and_required_when_disabling(lifecycle_store):
    database, _, _, _ = lifecycle_store
    reason = "  repeated\n\tprovider   failure  " + ("x" * 200)

    assert _set_disabled(reason=reason)["found"] is True
    stored = database.records[("ashby", "acme")]["metadata_json"][
        "acquisition_lifecycle"
    ]["reason"]
    assert stored.startswith("repeated provider failure ")
    assert "\n" not in stored
    assert "\t" not in stored
    assert len(stored) == discovery_store._ACQUISITION_DISABLED_REASON_MAX_LENGTH

    with pytest.raises(ValueError, match="reason"):
        _set_disabled(company="other", reason=" \n\t ")


def test_metadata_timestamps_crawl_state_and_unrelated_records_are_preserved(
    lifecycle_store,
):
    database, _, _, _ = lifecycle_store
    before_acme = json.loads(json.dumps(database.records[("ashby", "acme")]))
    before_other = json.loads(json.dumps(database.records[("ashby", "other")]))
    before_schedule = json.loads(json.dumps(database.crawl_state))

    assert _set_disabled()["found"] is True
    after_acme = database.records[("ashby", "acme")]
    assert after_acme["metadata_json"]["source"] == "seed"
    assert after_acme["metadata_json"]["unknown"] == {"keep": True}
    assert after_acme["first_seen_at"] == before_acme["first_seen_at"]
    assert after_acme["last_seen_at"] == before_acme["last_seen_at"]
    assert database.records[("ashby", "other")] == before_other
    assert database.crawl_state == before_schedule

    mutation_sql = database.mutation_sql[-1]
    assert "jsonb_set" in mutation_sql
    assert "INSERT" not in mutation_sql
    assert "DELETE" not in mutation_sql
    assert "first_seen_at" not in mutation_sql
    assert "last_seen_at" not in mutation_sql
    assert "discovery_crawl_state" not in mutation_sql


def test_discovery_uri_uses_effective_inventory_and_reenable_restores_it(
    lifecycle_store,
):
    assert _set_disabled()["found"] is True
    assert load_lines("discovery://ats/ashby") == ["legacy", "other"]

    assert _set_disabled(disabled=False)["found"] is True
    assert load_lines("discovery://ats/ashby") == ["acme", "legacy", "other"]
