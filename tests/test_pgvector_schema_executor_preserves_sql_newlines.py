from src.storage.vector_evidence import store


def test_schema_setup_preserves_newlines_for_sql_comments():
    captured = {}

    class Cursor:
        description = None

        def execute(self, sql, params=None):
            captured["sql"] = sql
            captured["params"] = params

        def close(self):
            pass

    class Connection:
        def cursor(self):
            return Cursor()

    result = store.execute_pgvector_schema_setup(db_executor=Connection())

    assert result["executed"] is True
    assert captured["params"] is None
    assert "\n" in captured["sql"]
    assert "DO $$" in captured["sql"]
    assert "-- Static pgvector" in captured["sql"]


def test_schema_setup_sql_is_not_collapsed_into_single_comment():
    captured = {}

    class Cursor:
        description = None

        def execute(self, sql, params=None):
            captured["sql"] = sql

        def close(self):
            pass

    class Connection:
        def cursor(self):
            return Cursor()

    store.execute_pgvector_schema_setup(db_executor=Connection())

    first_non_comment = ""
    for line in captured["sql"].splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("--"):
            first_non_comment = stripped
            break

    assert first_non_comment == "DO $$"
