import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agent'

    def ready(self):
        from .logging_config import setup_logging

        setup_logging()
        if os.environ.get("RUN_MAIN") or os.environ.get("APSCHEDULER_RUNNING"):
            return
        os.environ["APSCHEDULER_RUNNING"] = "1"
        try:
            from apscheduler.schedulers.background import BackgroundScheduler

            scheduler = BackgroundScheduler()
            scheduler.add_job(
                "agent.followup:verificar_followup",
                trigger="interval",
                minutes=int(os.getenv("AGENT_FOLLOWUP_INTERVAL_MINUTES", "15")),
            )
            scheduler.start()
            logger.info("Scheduler de follow-up iniciado")
        except Exception:
            logger.exception("Falha ao iniciar scheduler de follow-up")
