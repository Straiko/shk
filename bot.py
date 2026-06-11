"""Инициализация экземпляра бота."""

import telebot
from config import Config


def create_bot(config: Config) -> telebot.TeleBot:
    """Создать и настроить экземпляр бота."""
    return telebot.TeleBot(
        config.bot_token,
        parse_mode="HTML",
        num_threads=config.num_threads,
    )
