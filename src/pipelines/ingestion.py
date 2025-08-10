from src.config.settings import NEWSAPI_KEY, API_URL, DATABASE_URL
from src.utils.query_builder import build_q_from_db
from src.services.fetch_service import fetch_ai_marketing_news
from src.services.clean_service import clean_raw_data, filter_by_min_length
from src.repositories.news import upsert_news_bulk
from src.repositories.db import init_engine
from datetime import datetime, timedelta, timezone
import pandas as pd
import time
import logging

# Configuración del logger para el módulo de ingesta
logger = logging.getLogger("pipeline.ingestion")

def run_ingestion(engine, frm: str, to: str, page_size: int = 100, max_pages: int = 1, sleep_secs: float = 0.2):
    """
    Ejecuta el proceso de extracción y limpieza de noticias desde la API de NewsAPI.

    Parámetros:
        engine: Conexión a la base de datos.
        frm (str): Fecha/hora de inicio en formato ISO 8601 (ej. '2025-08-01T00:00:00').
        to (str): Fecha/hora de fin en formato ISO 8601.
        page_size (int, opcional): Número de artículos por página (máx. 100 en plan gratuito).
        max_pages (int, opcional): Número máximo de páginas a consultar.
        sleep_secs (float, opcional): Tiempo de espera entre páginas para evitar bloqueos.

    Retorna:
        tuple:
            curated_df (pd.DataFrame): DataFrame con noticias limpias y filtradas.
            metrics (dict): Métricas del proceso (páginas intentadas, artículos crudos, artículos limpios).
    """
    # Construye query de búsqueda a partir de keywords almacenadas en BD
    queries = build_q_from_db(engine=engine)
    all_curated = []
    total_results_seen = 0

    for page in range(1, max_pages + 1):
        safe_params_log = {
            "q": queries,
            "page": page,
            "pageSize": page_size,
            "from": frm,
            "to": to,
            "sortBy": "relevancy"
        }
        logger.info("Fetching page=%s params=%s", page, safe_params_log)

        # Parámetros de la petición a la API
        params = {
            "apiKey": NEWSAPI_KEY,
           **safe_params_log
        }

        # Obtiene datos crudos desde la API
        df_raw, meta = fetch_ai_marketing_news(api_url=API_URL, params=params)
        if not meta or meta.get("status") != "ok":
            raise RuntimeError(f"NewsAPI error: {meta}")

        # Si no hay artículos en la respuesta, termina el bucle
        if df_raw is None or df_raw.empty:
            logger.info("Página sin artículos, fin de paginado.")
            break

        total_results_seen += len(df_raw)

        # Limpieza y filtrado de datos
        df_curated = clean_raw_data(df_raw=df_raw)
        df_curated = filter_by_min_length(df=df_curated, min_total_chars=800)
        all_curated.append(df_curated)

        # Si una página tiene menos resultados de los solicitados, asumimos que no hay más datos
        if len(df_raw) < page_size:
            logger.info("Última página (len(df_raw) < page_size).")
            break

        # Pausa para evitar alcanzar límites de rate limit
        time.sleep(sleep_secs)

    # Consolida todos los DataFrames y elimina duplicados por hash de URL
    curated_df = (
        pd.concat(all_curated, ignore_index=True)
        .drop_duplicates(subset="url")
        .reset_index(drop=True)
        if all_curated else pd.DataFrame()
    )

    # Métricas de ejecución
    metrics = {
        "pages_attempted": len(all_curated),
        "raw_count": total_results_seen,
        "clean_count": int(len(curated_df)),
    }
    logger.info("Metrics: %s", metrics)

    return curated_df, metrics


def process_ingestion(days_back=7, page_size=100, max_pages=1):
    """
    Orquesta el proceso ETL completo: extrae, limpia y guarda noticias en la BD.

    Parámetros:
        days_back (int, opcional): Días atrás desde hoy para filtrar artículos.
        page_size (int, opcional): Número de artículos por página.
        max_pages (int, opcional): Número máximo de páginas a consultar.

    Retorna:
        dict:
            inserted (int): Número de artículos insertados/actualizados en BD.
            metrics (dict): Métricas de la ingesta.
    """
    engine = init_engine(DATABASE_URL)

    # Define rango de fechas en base a days_back
    now = datetime.now(timezone.utc)
    frm = (now - timedelta(days=days_back)).isoformat(timespec="seconds")
    to = now.isoformat(timespec="seconds")

    # Ejecuta la ingesta de datos
    df, metrics = run_ingestion(
        engine=engine,
        frm=frm,
        to=to,
        page_size=page_size,
        max_pages=max_pages
    )

    inserted = 0
    if not df.empty:
        inserted = upsert_news_bulk(engine, df)

    return {
        "inserted": inserted,
        "metrics": metrics
    }