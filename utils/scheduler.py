"""Планировщик периодических сообщений."""

import logging
import datetime
import threading
import time

logger = logging.getLogger(__name__)


def send_daily_message(bot, db_module):
    """Отправить сообщение со ссылкой на MAX бота всем активным пользователям."""
    from utils.db import get_all_user_ids

    user_ids = get_all_user_ids()
    if not user_ids:
        logger.info("Нет пользователей для рассылки")
        return

    text = (
        "Привет! Напоминаем: у нас есть бот в MAX!\n\n"
        "Теперь генерировать и сканировать штрих-коды можно и там.\n\n"
        "Попробуй: https://max.ru/id771692758487_bot\n\n"
        "Бот бесплатен — подписка на канал помогает нам с улучшениями!"
    )

    sent = 0
    failed = 0
    for user_id in user_ids:
        try:
            bot.send_message(user_id, text)
            sent += 1
        except Exception:
            failed += 1

    logger.info("Рассылка завершена: отправлено %d, ошибок %d", sent, failed)


def start_scheduler(bot, db_module):
    """Запустить планировщик в фоновом потоке."""
    def _run():
        logger.info("Планировщик запущ. Следующая рассылка в 06:12 MSK")

        while True:
            now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
            target = now.replace(hour=6, minute=12, second=0, microsecond=0)

            if now >= target:
                target += datetime.timedelta(days=1)

            wait_seconds = (target - now).total_seconds()
            logger.info("До следующей рассылки: %.0f секунд", wait_seconds)

            time.sleep(wait_seconds)

            try:
                send_daily_message(bot, db_module)
            except Exception:
                logger.exception("Ошибка рассылки")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
