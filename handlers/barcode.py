"""Генерация штрих-кодов."""

import logging
import telebot
import barcode as barcode_lib
from barcode.writer import ImageWriter

from config import Config
from utils.file_manager import temp_image
from utils.rate_limiter import RateLimiter, rate_limit
from utils.db import log_activity

logger = logging.getLogger(__name__)


from typing import Any

def send_barcode_image(bot: telebot.TeleBot, chat_id: int, text_to_encode: str, user: Any = None) -> None:
    """Сгенерировать Code128 штрих-код и отправить в чат."""
    with temp_image(suffix=".png") as tmp_path:
        try:
            code128 = barcode_lib.get_barcode_class("code128")
            my_barcode = code128(text_to_encode, writer=ImageWriter())
            # barcode.save() добавляет .png → передаём путь без расширения
            saved_path = my_barcode.save(str(tmp_path.with_suffix("")))

            with open(saved_path, "rb") as photo:
                bot.send_photo(chat_id, photo, caption=f"Штрих-код для: {text_to_encode}")
        except Exception as e:
            bot.send_message(chat_id, "⚠️ Ошибка при генерации штрих-кода.")
            if user:
                log_activity(user, "barcode_error", f"Ошибка: {str(e)}")
            logger.exception("Ошибка генерации для chat %d", chat_id)


def register(bot: telebot.TeleBot, config: Config, limiter: RateLimiter) -> None:
    """Зарегистрировать обработчик генерации штрих-кодов из текста."""

    @bot.message_handler(content_types=["text"], func=lambda m: m.text and not m.text.startswith("/"))
    @rate_limit(limiter, bot)
    def generate_and_send_barcode(message: telebot.types.Message) -> None:
        """Любой текст → генерация штрих-кода (catch-all handler)."""
        text_to_encode = message.text.strip()
        
        if not text_to_encode:
            bot.reply_to(message, "Пожалуйста, отправьте корректный текст.")
            return

        log_activity(message.from_user, "barcode_generate", f"Текст: {text_to_encode[:50]}")
        bot.send_chat_action(message.chat.id, "upload_photo")
        send_barcode_image(bot, message.chat.id, text_to_encode, message.from_user)

    logger.info("Обработчик генерации штрих-кодов зарегистрирован")
