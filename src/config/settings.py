import os
from dotenv import load_dotenv

# === Carga de variables de entorno ===
# Calcula la ruta raíz del proyecto (2 niveles arriba de este archivo)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Carga las variables definidas en el archivo .env
load_dotenv(os.path.join(ROOT, ".env"))

# === Variables de configuración globales ===
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")          # Clave para la API de NewsAPI
API_URL = os.getenv("API_URL")                  # URL base de la API a consultar
DATABASE_URL = os.getenv("DATABASE_URL")        # Conexión a la base de datos PostgreSQL
DEBUG = os.getenv("DEBUG")                      # "1" para habilitar modo debug
ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER")# "1" para habilitar ejecución programada

# === Validaciones mínimas de entorno ===
if not NEWSAPI_KEY:
    raise ValueError("Falta NEWSAPI_KEY en el archivo .env")
if not DATABASE_URL:
    raise ValueError("Falta DATABASE_URL en el archivo .env")

def is_debug() -> bool:
    """
    Retorna:
        bool: True si DEBUG está configurado como "1", False en caso contrario.

    Uso:
        if is_debug():
            print("Modo debug activado")
    """
    return DEBUG == "1"

def is_enable_scheduler() -> bool:
    """
    Retorna:
        bool: True si ENABLE_SCHEDULER está configurado como "1".

    Uso:
        if is_enable_scheduler():
            start_scheduler()
    """
    return ENABLE_SCHEDULER == "1"
