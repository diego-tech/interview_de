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

    Funciones:
        - Sobrescribe `init_engine` en `appmod` para que NO intente
          conectar a la base de datos real durante las pruebas
          (devolviendo un objeto "falso").
        - Crea un `test_client()` de Flask para simular peticiones HTTP
          a la aplicación sin levantar un servidor real.

    Args:
        monkeypatch: fixture nativa de pytest para reemplazar funciones/atributos.

    Yields:
        client (FlaskClient): cliente de pruebas para hacer peticiones tipo:
            resp = client.get("/endpoint")
            resp = client.post("/endpoint", json={"key": "value"})
    """
    # Bloquea conexiones reales a la base de datos en /preview o en otros endpoints
    monkeypatch.setattr(appmod, "init_engine", lambda *a, **k: object())

    # Crea cliente de pruebas para la app Flask
    with appmod.app.test_client() as c:
        yield c
