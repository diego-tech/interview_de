# src/scheduler.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from src.pipelines.ingestion import process_ingestion
from src.config.settings import is_debug

def scheduled_ingestion_job():
    logging.info("Scheduled ingestion started")
    try:
        res = process_ingestion(days_back=7, page_size=100, max_pages=1)
        logging.info("Scheduled ingestion OK: %s", res)
    except Exception:
        logging.exception("Scheduled ingestion FAILED")

def start_scheduler(debug=is_debug()):
    tz = ZoneInfo("Europe/Madrid")
    scheduler = BackgroundScheduler(timezone=tz)
    if debug:
        scheduler.add_job(scheduled_ingestion_job, "interval", seconds=15)
        logging.info("Scheduler started (DEV mode)")
    else:
        scheduler.add_job(scheduled_ingestion_job, CronTrigger(hour=7, minute=0))
        logging.info("Scheduler started (PROD mode)")
    scheduler.start()
