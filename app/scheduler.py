from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot

from app.config import get_settings
from app.database import SessionLocal
from app.services.price_service import send_weekly_reports, update_prices

settings = get_settings()

DAY_MAP = {
    "mon": "mon",
    "tue": "tue",
    "wed": "wed",
    "thu": "thu",
    "fri": "fri",
    "sat": "sat",
    "sun": "sun",
}


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    report_day = DAY_MAP.get(settings.weekly_report_day, "mon")

    async def check_prices_job() -> None:
        db = SessionLocal()
        try:
            await update_prices(db, bot)
        finally:
            db.close()

    async def weekly_report_job() -> None:
        db = SessionLocal()
        try:
            await send_weekly_reports(db, bot)
        finally:
            db.close()

    scheduler.add_job(
        check_prices_job,
        IntervalTrigger(hours=settings.price_check_interval_hours),
        id="price_check",
        replace_existing=True,
    )
    scheduler.add_job(
        weekly_report_job,
        CronTrigger(day_of_week=report_day, hour=settings.weekly_report_hour, minute=0),
        id="weekly_report",
        replace_existing=True,
    )
    return scheduler
