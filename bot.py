"""Инициализация экземпляра бота."""

import telebot
from telebot import apihelper
from config import Config

# Увеличиваем таймауты для стабильной работы с api.telegram.org
# (включая стартовый skip_pending и отправку/загрузку изображений)
apihelper.CONNECT_TIMEOUT = 15
apihelper.READ_TIMEOUT = 60


def create_bot(config: Config) -> telebot.TeleBot:
    """Создать и настроить экземпляр бота."""
    return telebot.TeleBot(
        config.bot_token,
        parse_mode="HTML",
        num_threads=config.num_threads,
    )
