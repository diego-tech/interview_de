# tests/test_api.py
import pandas as pd
import app as appmod

# ---------------------------------------------------------
# Pruebas de "humo" para los endpoints principales de la API
# ---------------------------------------------------------
# Estas pruebas validan que la API responde correctamente
# en los casos más básicos, sin depender de integraciones reales
# (BD, NewsAPI, etc.) gracias al uso de monkeypatching.
# ---------------------------------------------------------

def test_health_ok(client):
    """
    Verifica que el endpoint /health responde correctamente.

    - Debe devolver HTTP 200.
    - La respuesta JSON debe contener {"status": "ok"}.
    """
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_preview_ok(client, monkeypatch):
    """
    Verifica que el endpoint /preview funciona correctamente.

    - Se simula `run_ingestion` para que devuelva:
        * Un DataFrame con un único artículo.
        * Métricas de ejemplo.
    - Se valida que:
        * La respuesta HTTP sea 200.
        * El estado sea "success".
        * El conteo de artículos sea correcto.
        * Las métricas incluyan `clean_count` con el valor esperado.
    """

    # Simulación de `run_ingestion` con datos ficticios
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

    # Sobrescribe `run_ingestion` en appmod para no llamar a NewsAPI real
    monkeypatch.setattr(appmod, "run_ingestion", fake_run_ingestion)

    # Llamada al endpoint
    r = client.get("/preview?days_back=2&page_size=5&max_pages=1")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "success"
    assert data["count"] == 1
    assert isinstance(data["data"], list)
    assert data["metrics"]["clean_count"] == 1


def test_ingest_ok(client, monkeypatch):
    """
    Verifica que el endpoint /ingest inserta datos correctamente.

    - Se simula `process_ingestion` para que devuelva:
        * inserted = 3
        * métricas con {"status": "ok"}
    - Se valida que:
        * La respuesta HTTP sea 201 (creado).
        * El estado sea "success".
        * Se haya insertado la cantidad correcta de registros.
        * Las métricas coincidan con lo esperado.
    """

    # Simulación de `process_ingestion` con valores ficticios
    monkeypatch.setattr(
        appmod, "process_ingestion",
        lambda **kw: {"inserted": 3, "metrics": {"status": "ok"}}
    )

    # Llamada al endpoint
    r = client.post("/ingest", json={"days_back": 7, "page_size": 50, "max_pages": 1})
    assert r.status_code == 201
    data = r.get_json()
    assert data["status"] == "success"
    assert data["inserted"] == 3
    assert data["metrics"]["status"] == "ok"
