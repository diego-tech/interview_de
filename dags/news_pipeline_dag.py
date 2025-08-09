from __future__ import annotations
from datetime import timedelta
import logging
import pendulum

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import get_current_context

DAG_ID = "news_ai_marketing_ingestion"

def _process_ingestion():
    from src.pipelines.ingestion import process_ingestion

    ctx = get_current_context()
    params = ctx.get("params", {}) or {}
    days_back = int(params.get("days_back", 7))
    page_size = int(params.get("page_size", 100))
    max_pages = int(params.get("max_pages", 1))

    try:
        result = process_ingestion(
            days_back=days_back,
            page_size=page_size,
            max_pages=max_pages,
        )
        logging.getLogger(DAG_ID).info("Process result: %s", result)
        return result
    except AirflowSkipException:
        raise
    except Exception as e:
        logging.getLogger(DAG_ID).exception("Ingestion pipeline failed: %s", e)
        raise

default_args = {
    "owner": "diego",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "max_retry_delay": timedelta(minutes=30),
}


with DAG(
    dag_id=DAG_ID,
    default_args=default_args,
    schedule="0 6 * * *",  # Diario a las 06:00 Europe/Madrid
    start_date=pendulum.datetime(2025, 8, 1, tz="Europe/Madrid"),
    catchup=False,
    max_active_runs=1,
    tags=["etl", "newsapi"],
    params={
        "days_back": 7,
        "page_size": 100,
        "max_pages": 1,
    },
    doc_md="""
        # ETL all-in-one: NewsAPI → Limpieza → Upsert en BD

        Este DAG ejecuta un **pipeline unificado** que: 
        1) construye la query desde BD, 2) pagina la NewsAPI, 3) limpia/filtra resultados y 
        4) realiza **upsert** en la base de datos.  
        Devuelve un **resumen pequeño** en XCom (sin datos pesados).

        ## Parámetros (ajustables en la UI)
        - `days_back` (int): ventana de días hacia atrás para la búsqueda. *(default: 7)*
        - `page_size` (int): tamaño de página para la API. *(default: 100)*
        - `max_pages` (int): número máximo de páginas a recuperar. *(default: 1)*

        ## Planificación
        - **Schedule**: `0 6 * * *` (diario a las 06:00 Europe/Madrid)
        - **Start date**: 2025-08-01
        - **Catchup**: desactivado

        ## Flujo interno
        - **Build query**: lee keywords desde BD y normaliza términos (soporta listas/negaciones).
        - **Fetch**: pagina NewsAPI en la ventana `[now - days_back, now]`.
        - **Clean**: normaliza campos, filtra por longitud mínima y elimina duplicados.
        - **Upsert**: inserta/actualiza en BD en modo bulk.

        ## Salida (XCom)
        ```json
        {
        "raw": <int>,
        "clean": <int>,
        "inserted": <int>,
        "window": { "from": "<ISO8601>", "to": "<ISO8601>" }
        }
    """,
) as dag:
    run = PythonOperator(
        task_id="process_ingestion",
        python_callable=_process_ingestion,
        do_xcom_push=True,
        execution_timeout=timedelta(minutes=15)
    )
