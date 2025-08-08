from src.config.settings import NEWSAPI_KEY, API_URL
from src.utils.query_builder import build_q_from_db
from src.services.fetch_service import fetch_ai_marketing_news
from src.services.clean_service import clean_raw_data, filter_by_min_length
import pandas as pd
import time

def run_ingestion(engine, frm: str, to: str, page_size: int = 100, max_pages: int = 1, sleep_secs: float = 0.2):
    queries = build_q_from_db(engine=engine)
    all_curated = []
    total_raw = 0

    for page in range(1, max_pages + 1):
        params = {
            "apiKey": NEWSAPI_KEY,
            "q": queries,
            "page": page,
            "pageSize": page_size,
            "sortBy": "publishedAt",
            "from": frm,
            "to": to
        }

        df_raw, meta = fetch_ai_marketing_news(api_url=API_URL, params=params)

        if not meta or meta.get("status") != "ok":
            raise RuntimeError(f"NewsAPI error: {meta}")
        
        if df_raw is None or df_raw.empty:
            raise Exception("El Data Farme se encuentra vacío")
        
        df_curated = clean_raw_data(df_raw=df_raw)
        df_curated = filter_by_min_length(df=df_curated, min_total_chars=800)
        all_curated.append(df_curated)

        if len(all_curated) == meta.get("totalResults"):
            break

        time.sleep(sleep_secs)
    
    if all_curated:
        curated_df = (
            pd.concat(all_curated, ignore_index=True)
                .drop_duplicates(subset="url")
                .reset_index(drop=True)
        )
    else:    
        curated_df = pd.DataFrame()

    metrics = {
        "pages_attempted": min(max_pages, len(all_curated) or 1),
        "raw_count": total_raw,
        "clean_count": int(len(curated_df)),
    }
    return curated_df, metrics