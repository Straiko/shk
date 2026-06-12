"""Утилита проверки подписки для обработчиков."""

import telebot
from utils.subscription import is_subscribed, SUBSCRIBE_TEXT


def check_and_block(bot: telebot.TeleBot, message: telebot.types.Message) -> bool:
    """
    Проверить подписку. Если не подписан — отправить сообщение и вернуть True (заблокировано).
    Если подписан — вернуть False (можно продолжать).
    """
    if not is_subscribed(bot, message.from_user.id):
        bot.reply_to(message, SUBSCRIBE_TEXT, parse_mode="HTML")
        return True
    return False
