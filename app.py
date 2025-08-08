# app.py
import logging
from flask import Flask, jsonify, request
from datetime import datetime, timedelta, timezone
from src.repositories.db import init_engine
from src.config.settings import DATABASE_URL, ENABLE_SCHEDULER, is_debug
from src.pipelines.ingestion import run_ingestion, process_ingestion
from sqlalchemy import text
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", force=True)

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

# 1) GET /news -> lee DESDE BBDD (no toca la API)
@app.get("/news")
def list_news():
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 200))
        offset = max(0, int(request.args.get("offset", 0)))

        engine = init_engine(DATABASE_URL)
        sql = text("""
            SELECT url, title, description, author, url_to_image, published_at, source_name
            FROM news
            ORDER BY published_at DESC NULLS LAST
            LIMIT :limit OFFSET :offset
        """)

        with engine.connect() as conn:
            result = conn.execute(sql, {"limit": limit, "offset": offset})
            rows = result.mappings().all()          # list[RowMapping]
            data = [dict(r) for r in rows]          # <- convertir a dict

        # (opcional) serializar datetimes a ISO 8601
        for r in data:
            if r.get("published_at") is not None:
                r["published_at"] = r["published_at"].isoformat()

        return jsonify({"status": "success", "count": len(data), "data": data}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 2) GET /preview -> prueba la ingesta SIN persistir (útil en demo)
@app.get("/preview")
def preview_news():
    try:
        days_back = int(request.args.get("days_back", 7))
        page_size = int(request.args.get("page_size", 100))
        max_pages = int(request.args.get("max_pages", 1))

        now = datetime.now(timezone.utc)
        frm = (now - timedelta(days=days_back)).isoformat(timespec="seconds")
        to  = now.isoformat(timespec="seconds")

        engine = init_engine(DATABASE_URL)
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
        return jsonify({"status": "error", "message": str(e)}), 500

# 3) POST /ingest -> ingesta y PERSISTE (para orquestador/cron)
@app.post("/ingest")
def ingest_and_save():
    try:
        payload = request.get_json(silent=True) or {}
        res = process_ingestion(
            days_back=int(payload.get("days_back", 7)),
            page_size=int(payload.get("page_size", 100)),
            max_pages=int(payload.get("max_pages", 1)),
        )
        return jsonify({"status": "success", **res}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
if __name__ == "__main__":
    if ENABLE_SCHEDULER == "1":
        start_scheduler()
    app.run(host="0.0.0.0", port=1234, debug=is_debug())