"""Команда /admin для просмотра статистики и активности (через Telegram-меню)."""

import logging
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.rate_limiter import RateLimiter, rate_limit
from utils.db import get_stats, get_recent_activity, get_users, get_all_user_ids, DB_PATH, db_lock
import sqlite3

logger = logging.getLogger(__name__)

def get_admin_keyboard():
    """Создает клавиатуру (меню) админки."""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📝 Действия", callback_data="admin_activity")
    )
    markup.row(
        InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")
    )
    markup.row(
        InlineKeyboardButton("❌ Закрыть", callback_data="admin_close")
    )
    return markup

def _process_broadcast(message, bot, admin_id):
    if message.from_user.id != admin_id:
        bot.reply_to(message, "⛔ Только администратор может делать рассылку.")
        return
    text = message.text
    if not text:
        bot.reply_to(message, "⛔ Пустое сообщение.")
        return

    user_ids = get_all_user_ids()
    sent = 0
    for uid in user_ids:
        try:
            bot.send_message(uid, text)
            sent += 1
        except Exception:
            pass

    bot.reply_to(message, f"✅ Рассылка завершена! Отправлено: {sent} из {len(user_ids)}")


def register(bot: telebot.TeleBot, config: Config, limiter: RateLimiter) -> None:
    """Регистрация команды /admin и её кнопок."""

    def is_admin(user_id: int) -> bool:
        return config.admin_user_id and user_id == config.admin_user_id

    @bot.message_handler(commands=["admin"])
    @rate_limit(limiter, bot)
    def send_admin_menu(message: telebot.types.Message) -> None:
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа.")
            return

        bot.reply_to(
            message,
            "👋 <b>Панель администратора</b>\n\nВыберите нужный раздел:",
            reply_markup=get_admin_keyboard()
        )



    def _edit_or_send(bot, message, text, markup):
        if message.content_type == 'text':
            bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup, parse_mode="HTML")
        else:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
    def handle_admin_callbacks(call: telebot.types.CallbackQuery) -> None:
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Нет доступа.", show_alert=True)
            return

        action = call.data.replace("admin_", "", 1)

        if action == "close":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return
            
        elif action == "main":
            text = "👋 <b>Панель администратора</b>\n\nВыберите нужный раздел:"
            _edit_or_send(bot, call.message, text, get_admin_keyboard())
            
        elif action == "stats":
            stats = get_stats()
            text = (
                "📊 <b>Общая статистика:</b>\n\n"
                f"👥 Всего юзеров: <b>{stats['total_users']}</b>\n"
                f"📅 Уникальных сегодня: <b>{stats['today_users']}</b>\n"
                f"🔄 Всего запросов: <b>{stats['total_requests']}</b>\n"
            )
            _edit_or_send(bot, call.message, text, get_admin_keyboard())
            
        elif action == "activity":
            activity = get_recent_activity(50)
            if not activity:
                text = "📝 <b>Последние действия:</b>\n\nПусто."
                _edit_or_send(bot, call.message, text, get_admin_keyboard())
            else:
                lines = []
                markup = InlineKeyboardMarkup()
                photo_buttons = []
                
                for a in activity:
                    time_str = a['timestamp'][11:19]
                    name = a.get('first_name') or a.get('username') or "Без имени"
                    act_icon = "📷" if "photo" in a['action'] else "📝"
                    details = a.get('details') or "Нет данных"
                    
                    if a.get('file_id'):
                        lines.append(f"<code>{time_str}</code> | {act_icon} {name[:12]} (Акт #{a['id']})\n└ <i>{details}</i>")
                        photo_buttons.append(InlineKeyboardButton(f"📸 #{a['id']}", callback_data=f"admin_photo_{a['id']}"))
                    else:
                        lines.append(f"<code>{time_str}</code> | {act_icon} {name[:12]}\n└ <i>{details}</i>")
                
                text = "📝 <b>Последние 50 действий:</b>\n\n" + "\n\n".join(lines)
                if len(text) > 4000:
                    text = text[:4000] + "\n... (обрезано)"
                    
                for i in range(0, len(photo_buttons), 5):
                    markup.row(*photo_buttons[i:i+5])
                    
                markup.row(InlineKeyboardButton("🗑 Очистить последние 5", callback_data="admin_clear_5"))
                markup.row(InlineKeyboardButton("⬅️ В главное меню", callback_data="admin_main"))
                
                _edit_or_send(bot, call.message, text, markup)
                
        elif action == "clear_5":
            from utils.db import delete_last_activities
            delete_last_activities(5)
            bot.answer_callback_query(call.id, "✅ Последние 5 действий удалены!")
            call.data = "admin_activity"
            handle_admin_callbacks(call)
            return
            
        elif action.startswith("photo_"):
            act_id = int(action.split("_")[1])
            from utils.db import get_activity_by_id
            row = get_activity_by_id(act_id)
            if not row or not row.get('file_id'):
                bot.answer_callback_query(call.id, "⚠️ Фото не найдено.", show_alert=True)
                return
            
            bot.delete_message(call.message.chat.id, call.message.message_id)
            back_markup = InlineKeyboardMarkup()
            back_markup.add(InlineKeyboardButton("⬅️ Назад в действия", callback_data="admin_activity"))
            bot.send_photo(
                call.message.chat.id, 
                row['file_id'], 
                caption=f"📝 <b>Лог #{act_id}:</b> {row['details']}", 
                reply_markup=back_markup, 
                parse_mode="HTML"
            )
            
        elif action == "users":
            users = get_users(limit=100)
            if not users:
                text = "👥 <b>Последние пользователи:</b>\n\nПусто."
            else:
                lines = []
                for u in users:
                    name = u.get('first_name') or u.get('username') or "Без имени"
                    last_seen = u['last_seen'][11:19]
                    lines.append(f"👤 {name[:15]} | <code>{u['user_id']}</code> | 🕒 {last_seen}")
                
                text = "👥 <b>Последние 100 заходивших:</b>\n\n" + "\n".join(lines)
                if len(text) > 4000:
                    text = text[:4000] + "\n... (обрезано)"
                
            _edit_or_send(bot, call.message, text, get_admin_keyboard())

        elif action == "broadcast":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(
                call.message.chat.id,
                "📢 <b>Отправьте текст рассылки</b>\n\nСледующее сообщение будет разослано всем пользователям:",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, _process_broadcast, bot, call.from_user.id)
            return

        bot.answer_callback_query(call.id)

    logger.info("Обработчик админки с меню зарегистрирован")
