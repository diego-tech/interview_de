"""
Aplicación Flask que expone endpoints para interactuar con el pipeline ETL de noticias.
Incluye:
- Lectura de datos desde la base de datos.
- Vista previa de la ingesta (sin persistencia).
- Ingesta completa con persistencia en la base de datos.
- Opción de ejecución periódica mediante scheduler.

Endpoints:
    GET  /           -> Check.
    GET  /news       -> Obtiene noticias desde la base de datos.
    GET  /preview    -> Ejecuta la ingesta de noticias desde NewsAPI sin guardarlas.
    POST /ingest     -> Ejecuta la ingesta completa y persiste en la base de datos.
"""

import logging
from flask import Flask, jsonify, request
from datetime import datetime, timedelta, timezone
from src.repositories.db import init_engine
from src.config.settings import DATABASE_URL, is_enable_scheduler, is_debug
from src.pipelines.ingestion import run_ingestion, process_ingestion
from sqlalchemy import text
from scheduler import start_scheduler

# Configuración global de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True
)

# Inicialización de la aplicación Flask
app = Flask(__name__)

@app.get("/")
def check():
    """
    Endpoint de check para verificar que el servicio está activo.
    
    Returns:
        JSON con {"status": "ok"} y código HTTP 200.
    """
    return jsonify({"status": "ok"}), 200

# -------------------------------
# 1) GET /news -> Lectura desde DB
# -------------------------------
@app.get("/news")
def list_news():
    """
    Obtiene una lista paginada de noticias desde la base de datos.
    No realiza llamadas a la API externa.

    Query Params:
        limit (int, opcional): Número máximo de noticias a devolver (1-200, por defecto 50).
        offset (int, opcional): Número de registros a saltar para paginación (por defecto 0).

    Returns:
        JSON con estado, número de resultados y la lista de noticias.
    """
    try:
        # Validación de parámetros
        limit = max(1, min(int(request.args.get("limit", 50)), 200))
        offset = max(0, int(request.args.get("offset", 0)))

        # Conexión a base de datos
        engine = init_engine(DATABASE_URL)

        # Consulta SQL parametrizada
        sql = text("""
            SELECT url, title, description, author, url_to_image, published_at, source_name
            FROM news
            ORDER BY published_at DESC NULLS LAST
            LIMIT :limit OFFSET :offset
        """)

        with engine.connect() as conn:
            result = conn.execute(sql, {"limit": limit, "offset": offset})
            rows = result.mappings().all()
            data = [dict(r) for r in rows]

        # Serialización de fechas a formato ISO 8601
        for r in data:
            if r.get("published_at") is not None:
                r["published_at"] = r["published_at"].isoformat()

        return jsonify({"status": "success", "count": len(data), "data": data}), 200

    except Exception as e:
        logging.error(f"Error en list_news: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------------------------------------------------
# 2) GET /preview -> Ingesta sin persistencia (modo demo)
# ---------------------------------------------------------
@app.get("/preview")
def preview_news():
    """
    Ejecuta la ingesta de noticias desde la API externa pero sin guardarlas en la base de datos.
    Útil para verificar la transformación de datos y métricas de ingesta en modo demo.

    Query Params:
        days_back (int, opcional): Días hacia atrás desde la fecha actual para filtrar noticias.
        page_size (int, opcional): Número de noticias por página.s": "error"
        }
        max_pages (int, opcional): Número máximo de páginas a consultar.

    Returns:
        JSON con estado, número de resultados, métricas y datos transformados.
    """
    try:
        # Lectura de parámetros con valores por defecto
        days_back = int(request.args.get("days_back", 7))
        page_size = int(request.args.get("page_size", 100))
        max_pages = int(request.args.get("max_pages", 1))

        # Cálculo de fechas
        now = datetime.now(timezone.utc)
        frm = (now - timedelta(days=days_back)).isoformat(timespec="seconds")
        to  = now.isoformat(timespec="seconds")

        # Conexión a base de datos
        engine = init_engine(DATABASE_URL)

        # Ejecución de la ingesta (fase Extract + Transform)
        curated_df, metrics = run_ingestion(
            engine=engine, frm=frm, to=to, page_size=page_size, max_pages=max_pages
        )

        return jsonify({
            "status": "success",
            "count": int(len(curated_df)) if not curated_df.empty else 0,
            "metrics": metrics,
            "data": curated_df.to_dict(orient="records")
        }), 200

    except Exception as e:
        logging.error(f"Error en preview_news: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ------------------------------------------------------------
# 3) POST /ingest -> Ingesta completa con persistencia en DB
# ------------------------------------------------------------
@app.post("/ingest")
def ingest_and_save():
    """
    Ejecuta la ingesta completa de noticias desde la API externa y las guarda en la base de datos.
    Diseñado para ser usado por orquestadores o tareas programadas.

    Body JSON:
        days_back (int, opcional): Días hacia atrás para filtrar noticias (por defecto 7).
        page_size (int, opcional): Noticias por página (por defecto 100).
        max_pages (int, opcional): Máximo de páginas a consultar (por defecto 1).

    Ejemplo Body JSON:
        {
            "days_back": 7,
            "page_size": 100,
            "max_pages": 1
        }

    Returns:
        JSON con estado, métricas y número de registros insertados/actualizados.
    """
    try:
        # Lectura de parámetros desde el cuerpo de la petición
        payload = request.get_json(silent=True) or {}

        # Ejecución del proceso ETL completo
        res = process_ingestion(
            days_back=int(payload.get("days_back", 7)),
            page_size=int(payload.get("page_size", 100)),
            max_pages=int(payload.get("max_pages", 1)),
        )
        return jsonify({"status": "success", **res}), 201
    except Exception as e:
        logging.error(f"Error en ingest_and_save: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ------------------------------------------------------------
# Punto de entrada principal
# ------------------------------------------------------------
if __name__ == "__main__":
    # Si está habilitado el scheduler, iniciar tareas programadas
    if is_enable_scheduler():
        start_scheduler()

    # Lanzar servidor Flask
    app.run(host="0.0.0.0", port=1234, debug=is_debug())
