# app.py
from flask import Flask, jsonify, request
from datetime import datetime, timedelta, timezone
from src.repositories.db import init_engine
from src.repositories.news import upsert_news_bulk
from src.config.settings import DATABASE_URL
from src.pipelines.ingestion import run_ingestion

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

# 1) GET /news -> lee DESDE BBDD (no toca la API)
@app.get("/news")
def list_news():
    # aquí idealmente paginas y filtras desde la BBDD
    # si aún no tienes un SELECT, por ahora puedes devolver un 501 o un TODO
    return jsonify({"status": "todo", "message": "Implementar lectura desde BBDD"}), 501

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
        payload   = request.get_json(silent=True) or {}
        days_back = int(payload.get("days_back", 7))
        page_size = int(payload.get("page_size", 100))
        max_pages = int(payload.get("max_pages", 1))

        now = datetime.now(timezone.utc)
        frm = (now - timedelta(days=days_back)).isoformat(timespec="seconds")
        to  = now.isoformat(timespec="seconds")

        engine = init_engine(DATABASE_URL)
        curated_df, metrics = run_ingestion(
            engine=engine, frm=frm, to=to, page_size=page_size, max_pages=max_pages
        )

        if curated_df.empty:
            return jsonify({"status": "success", "inserted": 0, "metrics": metrics}), 201

        inserted = upsert_news_bulk(engine, curated_df)  # tu upsert
        return jsonify({"status": "success", "inserted": inserted, "metrics": metrics}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1234, debug=True)
