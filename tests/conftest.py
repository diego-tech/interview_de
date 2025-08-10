import os
import pytest
import app as appmod

# ---------------------------------------------------------
# Configuración previa para entorno de testing
# ---------------------------------------------------------
os.environ.setdefault("ENABLE_SCHEDULER", "0")
os.environ.setdefault("DEBUG", "0")


@pytest.fixture
def client(monkeypatch):
    """
    Fijura de Pytest que devuelve un cliente de pruebas para la app Flask.
    
    """
    # Bloquea conexiones reales a la base de datos en /preview o en otros endpoints
    monkeypatch.setattr(appmod, "init_engine", lambda *a, **k: object())

    # Crea cliente de pruebas para la app Flask
    with appmod.app.test_client() as c:
        yield c
