from types import SimpleNamespace

from backend.app.repositories import database as database_module


def test_get_database_returns_cached_instance(monkeypatch) -> None:
    database_module.get_database.cache_clear()
    created = []
    expected_database = object()

    class FakeDatabase:
        def __new__(cls, connection_string):
            created.append(connection_string)
            return expected_database

    monkeypatch.setattr(
        database_module,
        "get_settings",
        lambda: SimpleNamespace(pgvector_connection_string="postgresql://jobs-db"),
    )
    monkeypatch.setattr(database_module, "Database", FakeDatabase)

    try:
        first = database_module.get_database()
        second = database_module.get_database()
    finally:
        database_module.get_database.cache_clear()

    assert first is expected_database
    assert second is first
    assert created == ["postgresql://jobs-db"]