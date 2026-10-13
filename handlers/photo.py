"""Обработка фото: сканирование штрих-кодов + OCR."""

import hashlib
import logging
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image

from config import Config
from services.scanner import scan_barcodes
from services.ocr import scan_text_ocr
from handlers.barcode import send_barcode_image
from handlers.subscription_check import check_and_block
from utils.subscription import is_subscribed
from utils.file_manager import temp_image
from utils.rate_limiter import RateLimiter, rate_limit
from utils.db import log_activity

logger = logging.getLogger(__name__)

# Temporary in-memory cache for long codes (>50 bytes) to respect Telegram's 64-byte callback_data limit
_LONG_CODE_CACHE: dict[str, str] = {}



def register(bot: telebot.TeleBot, config: Config, limiter: RateLimiter) -> None:
    """Зарегистрировать обработчик фото/документов."""

    @bot.message_handler(content_types=["photo", "document"])
    @rate_limit(limiter, bot)
    def handle_photo(message: telebot.types.Message) -> None:
        """Обработка входящего фото: сканирование ШК + OCR + генерация баркода."""
        if check_and_block(bot, message):
            return
        user_id = message.from_user.id
        bot.send_chat_action(message.chat.id, "typing")

        # Определяем file_id и проверяем тип
        file_id, file_size = _extract_file_info(message)
        if file_id is None:
            bot.reply_to(message, "Пожалуйста, отправьте изображение (картинку).")
            return

        # Проверка размера файла
        max_bytes = config.max_file_size_mb * 1024 * 1024
        if file_size and file_size > max_bytes:
            bot.reply_to(
                message, f"⚠️ Файл слишком большой (максимум {config.max_file_size_mb}MB)."
            )
            log_activity(message.from_user, "photo_scan", f"Превышен размер: {file_size} байт", file_id=file_id)
            return

        with temp_image(suffix=".jpg") as photo_path:
            try:
                # Скачиваем файл
                file_info = bot.get_file(file_id)
                
                # Дополнительная проверка размера (если изначально file_size был None)
                if file_info.file_size and file_info.file_size > max_bytes:
                    bot.reply_to(
                        message, f"⚠️ Файл слишком большой (максимум {config.max_file_size_mb}MB)."
                    )
                    return

                downloaded_file = bot.download_file(file_info.file_path)
                photo_path.write_bytes(downloaded_file)

                # Сканируем штрих-коды
                img = Image.open(photo_path)
                decoded_objects = scan_barcodes(img)
                barcode_codes = [obj.text for obj in decoded_objects]

                # OCR текста
                ocr_codes = scan_text_ocr(str(photo_path), config.yandex_api_key)

                # Объединяем все найденные коды
                codes = list(dict.fromkeys(barcode_codes + ocr_codes))

                if not codes:
                    bot.reply_to(
                        message,
                        "❌ Штрих-коды или текст не найдены на фото.\n"
                        "Попробуй сделать фото чётче.",
                    )
                    log_activity(message.from_user, "photo_scan", "Ничего не найдено", file_id=file_id)
                    return

                # Приоритет: штрих-коды из zxingcpp > OCR текст
                if barcode_codes:
                    chosen = max(barcode_codes, key=len)
                else:
                    chosen = max(codes, key=len)

                reply = _format_reply(codes, chosen)
                markup = _build_codes_keyboard(codes) if len(codes) > 1 else None
                bot.reply_to(message, reply, reply_markup=markup)
                send_barcode_image(bot, message.chat.id, chosen, message.from_user)
                log_activity(message.from_user, "photo_scan", f"Найдено: {chosen}", file_id=file_id)

            except Exception as e:
                bot.reply_to(message, "⚠️ Ошибка при обработке фото.")
                log_activity(message.from_user, "photo_error", f"Ошибка: {str(e)[:50]}", file_id=file_id)
                logger.exception("Ошибка обработки фото для user %d", user_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith(("gen_bc:", "gen_bch:")))
    def handle_barcode_button(call: telebot.types.CallbackQuery) -> None:
        """Handle inline button click: generate Code128 barcode for selected code."""
        if not is_subscribed(bot, call.from_user.id):
            bot.answer_callback_query(
                call.id,
                "⚠️ Для использования бота необходимо подписаться на канал!",
                show_alert=True,
            )
            return

        if not limiter.is_allowed(call.from_user.id):
            bot.answer_callback_query(call.id, "⏳ Подожди немного, не спеши!")
            return

        if call.data.startswith("gen_bc:"):
            code = call.data.replace("gen_bc:", "", 1)
        else:
            code_hash = call.data.replace("gen_bch:", "", 1)
            code = _LONG_CODE_CACHE.get(code_hash)
            if not code:
                bot.answer_callback_query(
                    call.id,
                    "⚠️ Время действия кнопки истекло. Отправьте фото заново.",
                    show_alert=True,
                )
                return

        bot.answer_callback_query(call.id, f"Генерирую: {code[:15]}...")
        send_barcode_image(bot, call.message.chat.id, code, call.from_user)
        log_activity(call.from_user, "barcode_button_click", f"Выбран: {code[:50]}")

    logger.info("Обработчик фото зарегистрирован")


def _extract_file_info(
    message: telebot.types.Message,
) -> tuple[str | None, int | None]:
    """Извлечь file_id и file_size из сообщения."""
    if message.content_type == "photo":
        return message.photo[-1].file_id, message.photo[-1].file_size
    elif message.content_type == "document":
        if message.document.mime_type and message.document.mime_type.startswith("image/"):
            return message.document.file_id, message.document.file_size
    return None, None


def _format_reply(codes: list[str], chosen: str) -> str:
    """Сформировать ответное сообщение со списком кодов."""
    if len(codes) == 1:
        return f"✅ Найдено:\n\n<code>{chosen}</code>"

    all_codes_text = "\n".join(f"• <code>{c}</code>" for c in codes)
    return (
        f"🔍 Найдено (штрих-коды + текст):\n\n"
        f"{all_codes_text}\n\n"
        f"🏆 Выбран главный код (самый длинный): <code>{chosen}</code>\n\n"
        f"👇 <i>Нажмите кнопку ниже, чтобы получить штрих-код для нужного кода:</i>"
    )


def _build_codes_keyboard(codes: list[str]) -> InlineKeyboardMarkup:
    """Build inline keyboard for generating barcodes from detected codes."""
    if len(_LONG_CODE_CACHE) > 500:
        _LONG_CODE_CACHE.clear()

    markup = InlineKeyboardMarkup()
    buttons = []

    for code in codes:
        btn_label = f"📊 {code[:22]}..." if len(code) > 22 else f"📊 {code}"
        raw_bytes = code.encode("utf-8")
        if len(raw_bytes) <= 50:
            cb_data = f"gen_bc:{code}"
        else:
            code_hash = hashlib.md5(raw_bytes).hexdigest()[:12]
            _LONG_CODE_CACHE[code_hash] = code
            cb_data = f"gen_bch:{code_hash}"

        buttons.append(InlineKeyboardButton(text=btn_label, callback_data=cb_data))

    max_len = max(len(c) for c in codes) if codes else 0
    row_width = 1 if max_len > 15 else 2

    for i in range(0, len(buttons), row_width):
        markup.row(*buttons[i : i + row_width])

    return markup

