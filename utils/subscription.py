"""Проверка подписки на Telegram-канал."""

import logging
import telebot
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

CHANNEL_USERNAME = "ozonwariors"
CHANNEL_LINK = "https://t.me/ozonwariors"
MAX_BOT_LINK = "https://max.ru/id771692758487_bot"

SUBSCRIBE_TEXT = (
    "Для использования бота необходимо подписаться на канал!\n\n"
    f"Подпишись здесь: {CHANNEL_LINK}\n\n"
    "После подписки нажми /start снова.\n\n"
    "Бот бесплатен — подписка на канал помогает нам с улучшениями!"
)

UNSUBSCRIBE_TEXT = (
    "Ты отписался от канала! Для использования бота нужно подписаться снова.\n\n"
    f"Подпишись: {CHANNEL_LINK}\n\n"
    "Бот бесплатен — подписка на канал помогает нам с улучшениями!"
)


def is_subscribed(bot: telebot.TeleBot, user_id: int) -> bool:
    """Проверить, подписан ли пользователь на канал."""
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        status = member.status
        # 'creator', 'administrator', 'member' — считаются подписчиками
        return status in ("creator", "administrator", "member")
    except Exception as e:
        logger.warning("Ошибка проверки подписки для user %d: %s", user_id, e)
        # Если ошибка (например, бот не админ канала) — пропускаем проверку
        return True


def require_subscription(func: Callable) -> Callable:
    """
    Декоратор: проверяет подписку на канал перед выполнением обработчика.
    Если не подписан — отправляет сообщение с просьбой подписаться.
    """
    @wraps(func)
    def wrapper(message: telebot.types.Message, *args, **kwargs):
        bot = kwargs.get("bot") or (args[0] if args and isinstance(args[0], telebot.TeleBot) else None)
        if bot is None:
            # Пытаемся получить bot из message (не работает напрямую, но на случай если передан)
            return func(message, *args, **kwargs)

        user_id = message.from_user.id

        if not is_subscribed(bot, user_id):
            bot.reply_to(message, SUBSCRIBE_TEXT, parse_mode="HTML")
            return None

        return func(message, *args, **kwargs)
    return wrapper
