"""Обработчики команд /start, /help, /version."""

import logging
import telebot
from config import Config

logger = logging.getLogger(__name__)

CHANGELOG = (
    "v3.0.0 — Рефакторинг: модульная архитектура, безопасность, логирование\n"
    "v2.0.0 — Production Ready: многопоточность, rate limiting, автоочистка\n"
    "v1.5.2 — Автоисправление ошибки OCR\n"
    "v1.5.0 — Умный фильтр текста\n"
    "v1.2.0 — Генерация баркода после фото\n"
    "v1.1.0 — Чтение ШК/QR с фото"
)


def register(bot: telebot.TeleBot, config: Config) -> None:
    """Зарегистрировать обработчики команд."""

    @bot.message_handler(commands=["version"])
    def send_version(message: telebot.types.Message) -> None:
        bot.reply_to(
            message,
            f"🤖 <b>Версия бота:</b> <code>{config.version}</code>\n\n"
            f"📋 <b>История изменений:</b>\n{CHANGELOG}",
        )

    @bot.message_handler(commands=["start", "help"])
    def send_welcome(message: telebot.types.Message) -> None:
        bot.reply_to(
            message,
            "Привет! Я умею находить штрих-коды и текст на фото и генерировать новые!\n\n"
            "📷 <b>Читать штрих-коды</b>\n"
            "Просто отправь мне фото или скан (картинкой или файлом).\n"
            "Я найду на нём штрих-коды или текст и выдам результат.\n\n"
            "✏️ <b>Создать штрих-код</b>\n"
            "Отправь любой текст (латиницу или цифры), и я сделаю из него штрих-код.\n\n"
            "⚡️ <b>Команды:</b>\n"
            "/version — версия бота\n"
            "/help — эта справка",
        )

    logger.info("Обработчики команд зарегистрированы")
