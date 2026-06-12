"""
SHK Bot — Telegram-бот для сканирования и генерации штрих-кодов.

Точка входа приложения.
"""

import logging
import time
import os

from config import load_config
from bot import create_bot
from utils.rate_limiter import RateLimiter
from utils.db import init_db
from utils.scheduler import start_scheduler
from handlers import commands, photo, barcode, admin


def setup_logging() -> None:
    """Настроить логирование в консоль + файл."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("bot.log", encoding="utf-8"),
        ],
    )


def main() -> None:
    """Запуск бота."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Инициализация БД
    init_db()

    # Загрузка конфигурации из .env
    config = load_config()
    logger.info("🚀 Бот v%s запускается...", config.version)

    # Создание бота и rate limiter
    bot = create_bot(config)
    limiter = RateLimiter(config.rate_limit_seconds)

    # Регистрация обработчиков (порядок важен — catch-all последним!)
    admin.register(bot, config, limiter)
    commands.register(bot, config)
    photo.register(bot, config, limiter)
    barcode.register(bot, config, limiter)

    # Запуск планировщика (рассылка в 6:12)
    from utils import db as db_module
    start_scheduler(bot, db_module)

    logger.info(
        "⚙️ Потоки: %d | Rate limit: %dс | Макс. файл: %dMB | Канал: @%s",
        config.num_threads,
        config.rate_limit_seconds,
        config.max_file_size_mb,
        config.channel_username,
    )

    # Запуск с автоматическим переподключением
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except KeyboardInterrupt:
            logger.info("👋 Бот остановлен пользователем")
            logging.shutdown()
            break
        except Exception:
            logger.exception("Ошибка polling")
            logger.info("🔄 Переподключение через 5 секунд...")
            time.sleep(5)


if __name__ == "__main__":
    main()
