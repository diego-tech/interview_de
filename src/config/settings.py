import os
from dotenv import load_dotenv

# Cargar variables desde .env
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(ROOT, ".env"))

# Variables de configuración
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
API_URL = os.getenv("API_URL")
DATABASE_URL = os.getenv("DATABASE_URL")  # conexión a PostgreSQL
DEBUG = os.getenv("DEBUG")
ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER")

# Validaciones mínimas
if not NEWSAPI_KEY:
    raise ValueError("Falta NEWSAPI_KEY en el archivo .env")
if not DATABASE_URL:
    raise ValueError("Falta DATABASE_URL en el archivo .env")

def is_debug() -> bool:
    return DEBUG == "1"