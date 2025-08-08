import os
from dotenv import load_dotenv

# Cargar variables desde .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Variables de configuración
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
API_URL = os.getenv("API_URL")
DATABASE_URL = os.getenv("DATABASE_URL")  # conexión a PostgreSQL

# Validaciones mínimas
if not NEWSAPI_KEY:
    raise ValueError("Falta NEWSAPI_KEY en el archivo .env")
if not DATABASE_URL:
    raise ValueError("Falta DATABASE_URL en el archivo .env")
