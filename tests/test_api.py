# tests/test_api_smoke.py
import pytest
import pandas as pd
import app as appmod

def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"

def test_preview_ok(client, monkeypatch):
    # run_ingestion devuelve un DF pequeño + métricas
    def fake_run_ingestion(engine, frm, to, page_size, max_pages):
        df = pd.DataFrame([{
            "url": "https://example.com/a",
            "title": "Titulo",
            "description": "Desc",
            "content": "Contenido...",
            "author": "Autor",
            "published_at": "2025-08-08T00:00:00Z",
            "url_to_image": "https://img",
            "source_id": "sid",
            "source_name": "sname"
        }])
        return df, {"status": "ok", "raw_count": 1, "clean_count": 1}

    monkeypatch.setattr(appmod, "run_ingestion", fake_run_ingestion)

    r = client.get("/preview?days_back=2&page_size=5&max_pages=1")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "success"
    assert data["count"] == 1
    assert isinstance(data["data"], list)
    assert data["metrics"]["clean_count"] == 1

def test_ingest_ok(client, monkeypatch):
    # process_ingestion devuelve lo que insertaría
    monkeypatch.setattr(
        appmod, "process_ingestion",
        lambda **kw: {"inserted": 3, "metrics": {"status": "ok"}}
    )

    r = client.post("/ingest", json={"days_back": 7, "page_size": 50, "max_pages": 1})
    assert r.status_code == 201
    data = r.get_json()
    assert data["status"] == "success"
    assert data["inserted"] == 3
    assert data["metrics"]["status"] == "ok"
