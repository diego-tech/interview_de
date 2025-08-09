from __future__ import annotations
from datetime import datetime, timedelta
import json
import logging
import pandas as pd

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Importa TU código (gracias a PYTHONPATH=/opt/airflow/app)
from src.repositories.db import init_engine
from src.repositories.news import upsert_news  # -> implementa ON CONFLICT en tu repo
from src.services.fetch_service import fetch_news  # devuelve list[dict]
from src.services.clean_service import clean_articles  # recibe list[dict] -> DataFrame limpio

DEFAULT_ARGS = {
    "owner": "diego",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def extract(**ctx):
    # Puedes pasar ventanas temporales si quieres incrementalidad
    articles = fetch_news()
    ctx["ti"].xcom_push(key="raw_articles", value=articles)

def transform(**ctx):
    articles = ctx["ti"].xcom_pull(key="raw_articles", task_ids="extract")
    if not articles:
        logging.info("No articles to transform.")
        ctx["ti"].xcom_push(key="clean_df_json", value="[]")
        return

    df: pd.DataFrame = clean_articles(articles)  # normaliza + filtro AI & Marketing + dedup + fechas
    ctx["ti"].xcom_push(key="clean_df_json", value=df.to_json(orient="records", date_unit="s"))

def load(**ctx):
    rows_json = ctx["ti"].xcom_pull(key="clean_df_json", task_ids="transform")
    df = pd.DataFrame(json.loads(rows_json)) if rows_json else pd.DataFrame()
    if df.empty:
        logging.info("Nothing to load.")
        return

    # Conexión por Hook (si configuras en Airflow UI una conn 'supabase_db'), o usa init_engine(DATABASE_URL).
    try:
        hook = PostgresHook(postgres_conn_id="supabase_db")
        engine = hook.get_sqlalchemy_engine()
    except Exception:
        # Fallback a tu init_engine leyendo DATABASE_URL (de tu settings/.env)
        from src.config.settings import DATABASE_URL
        engine = init_engine(DATABASE_URL)

    upsert_news(df, engine)  # implementa ON CONFLICT (url_hash) DO UPDATE

with DAG(
    dag_id="news_ai_marketing_pipeline",
    default_args=DEFAULT_ARGS,
    schedule="0 6 * * *",    # diario 06:00 Europe/Madrid
    start_date=datetime(2025, 8, 1),
    catchup=False,
    tags=["etl", "news", "supabase"],
) as dag:

    t_extract = PythonOperator(task_id="extract", python_callable=extract)
    t_transform = PythonOperator(task_id="transform", python_callable=transform)
    t_load = PythonOperator(task_id="load", python_callable=load)

    t_extract >> t_transform >> t_load
