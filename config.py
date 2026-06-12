"""Конфигурация бота — загрузка из .env файла."""

import os
import sys
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    """Настройки бота. Все секреты загружаются из переменных окружения."""

    bot_token: str
    ocr_api_key: str = "helloworld"
    rate_limit_seconds: int = 2
    max_file_size_mb: int = 20
    num_threads: int = 4
    admin_user_id: int | None = None
    miniapp_url: str | None = None
    channel_username: str = "ozonwariors"
    max_bot_link: str = "https://max.ru/id771692758487_bot"
    version: str = "3.1.0"


def load_config() -> Config:
    """Загрузить конфигурацию из переменных окружения (.env файла)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv не установлен, используем только переменные окружения")

    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.critical("❌ BOT_TOKEN не задан! Создайте .env файл (см. .env.example)")
        sys.exit(1)

    admin_id_str = os.getenv("ADMIN_USER_ID")
    admin_user_id = int(admin_id_str) if admin_id_str else None

    return Config(
        bot_token=token,
        ocr_api_key=os.getenv("OCR_API_KEY", "helloworld"),
        rate_limit_seconds=int(os.getenv("RATE_LIMIT_SECONDS", "2")),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "20")),
        num_threads=int(os.getenv("NUM_THREADS", "4")),
        admin_user_id=admin_user_id,
        miniapp_url=os.getenv("MINIAPP_URL"),
        channel_username=os.getenv("CHANNEL_USERNAME", "ozonwariors"),
        max_bot_link=os.getenv("MAX_BOT_LINK", "https://max.ru/id771692758487_bot"),
    )
