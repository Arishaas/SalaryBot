import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
    price_alert_threshold_percent: float = float(
        os.getenv("PRICE_ALERT_THRESHOLD_PERCENT", "10")
    )
    price_check_interval_hours: int = int(os.getenv("PRICE_CHECK_INTERVAL_HOURS", "6"))
    weekly_report_day: str = os.getenv("WEEKLY_REPORT_DAY", "mon").lower()
    weekly_report_hour: int = int(os.getenv("WEEKLY_REPORT_HOUR", "10"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
