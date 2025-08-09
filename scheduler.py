# src/scheduler.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from src.pipelines.ingestion import process_ingestion
from src.config.settings import is_debug

def scheduled_ingestion_job():
    """
    Job que ejecuta la ingesta programada de noticias.

    Flujo:
      1. Registra inicio en logs.
      2. Llama a `process_ingestion` con parámetros por defecto:
         - days_back = 7 (últimos 7 días)
         - page_size = 100 (máx. artículos por request)
         - max_pages = 1 (solo primera página de resultados)
      3. Registra éxito o error en logs.

    Se ejecuta automáticamente según la configuración del scheduler.
    """
    logging.info("Scheduled ingestion started")
    try:
        res = process_ingestion(days_back=7, page_size=100, max_pages=1)
        logging.info("Scheduled ingestion OK: %s", res)
    except Exception:
        logging.exception("Scheduled ingestion FAILED")

def start_scheduler(debug=is_debug()):
    """
    Inicializa y arranca el scheduler en segundo plano.

    Modo de ejecución:
      - DEV (debug=True):
          Ejecuta la ingesta cada 15 segundos para pruebas rápidas.
      - PROD (debug=False):
          Ejecuta la ingesta cada día a las 07:00 hora de Madrid.

    Args:
        debug (bool): indica si se usa el modo desarrollo o producción.

    Notas:
        - Usa `ZoneInfo("Europe/Madrid")` para asegurar zona horaria correcta.
        - Usa `apscheduler.schedulers.background.BackgroundScheduler` para
          permitir que la ejecución no bloquee el resto de la app.
    """
    tz = ZoneInfo("Europe/Madrid")
    scheduler = BackgroundScheduler(timezone=tz)

    if debug:
        scheduler.add_job(scheduled_ingestion_job, "interval", seconds=15)
        logging.info("Scheduler started (DEV mode)")
    else:
        scheduler.add_job(scheduled_ingestion_job, CronTrigger(hour=7, minute=0))
        logging.info("Scheduler started (PROD mode)")

    scheduler.start()
