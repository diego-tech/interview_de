# tests/conftest.py
import os
import pytest
import app as appmod

# Apaga el scheduler en tests, por si acaso
os.environ.setdefault("ENABLE_SCHEDULER", "0")
os.environ.setdefault("DEBUG", "0")

@pytest.fixture
def client(monkeypatch):
    # Evita conexiones reales a DB en /preview
    monkeypatch.setattr(appmod, "init_engine", lambda *a, **k: object())
    with appmod.app.test_client() as c:
        yield c
