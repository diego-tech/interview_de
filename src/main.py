from config.settings import NEWSAPI_KEY, API_URL, DATABASE_URL
from utils.query_builder import build_q_from_db
from services.fetch_service import fetch_ai_marketing_news
from services.clean_service import clean_raw_data, filter_by_min_length
from repositories.db import init_engine
import pandas as pd
import time
from datetime import datetime, timedelta, timezone

if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    frm = (now - timedelta(days=7)).isoformat(timespec="seconds")
    to  = now.isoformat(timespec="seconds")
    engine = init_engine(DATABASE_URL)

    queries = build_q_from_db(engine=engine)

    pageSize = 100
    max_pages = 1          # súbelo si tu plan lo permite
    sleep_secs = 0.2        # sé amable con la API

    all_curated = []        # aquí acumulamos ya limpios
    for page in range(1, max_pages + 1):
        params = {
            "apiKey": NEWSAPI_KEY,
            "q": queries,
            "page": page,
            "pageSize": 100,
            "sortBy": "publishedAt",
            "from": frm,
            "to": to,
        }

        df_raw, meta = fetch_ai_marketing_news(API_URL, params)
        if meta.get("status") != "ok":
            print(f"[page {page}] Error: {meta.get('error_message')}")
            break

        if df_raw is None or df_raw.empty:
            print(f"[page {page}] sin artículos → fin")
            break

        # Limpieza por página (rápida y con poca memoria)
        df_curated = clean_raw_data(df_raw)
        df_curated = filter_by_min_length(df_curated, min_total_chars=800)  # opcional

        all_curated.append(df_curated)
        print(f"[page {page}] artículos crudos: {len(df_raw)} | limpios: {len(df_curated)}")
        
        # Heurística de parada: si la API devuelve < page_size, no hay más páginas
        if len(all_curated) == meta.get("totalResults"):
            break

        time.sleep(sleep_secs)

    # Concatenar y deduplicar por URL (por si hubo solapes entre páginas/queries)
    if all_curated:
        curated_df = pd.concat(all_curated, ignore_index=True).drop_duplicates(subset="url").reset_index(drop=True)
        print(f"Total limpios tras paginar+dedupe: {len(curated_df)}")
    else:
        print("No se obtuvieron artículos.")
