"""Обработчики команд /start, /help, /version."""

import logging
import telebot
from config import Config
from handlers.subscription_check import check_and_block
from utils.subscription import is_subscribed, CHANNEL_LINK, MAX_BOT_LINK

logger = logging.getLogger(__name__)

CHANGELOG = (
    "v3.1.0 — Проверка подписки на канал, автосообщения\n"
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
        if check_and_block(bot, message):
            return
        bot.reply_to(
            message,
            f"🤖 <b>Версия бота:</b> <code>{config.version}</code>\n\n"
            f"📋 <b>История изменений:</b>\n{CHANGELOG}",
        )

    @bot.message_handler(commands=["start", "help"])
    def send_welcome(message: telebot.types.Message) -> None:
        if check_and_block(bot, message):
            return
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
            "/help — эта справка\n\n"
            "📱 <b>Также доступен в:</b>\n"
            f"MAX: {MAX_BOT_LINK}\n"
            "VK: https://vk.com/club239550562",
        )

    logger.info("Обработчики команд зарегистрированы")
