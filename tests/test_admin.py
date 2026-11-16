"""Тесты для обработчиков панели администратора."""

from unittest.mock import MagicMock
from telebot.apihelper import ApiTelegramException
from handlers.admin import _edit_or_send


def test_edit_or_send_ignores_message_not_modified():
    """Ошибка 400 Bad Request: message is not modified не приводит к падению."""
    bot = MagicMock()
    message = MagicMock()
    message.content_type = "text"
    message.chat.id = 123
    message.message_id = 456

    result_json = {"error_code": 400, "description": "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"}
    bot.edit_message_text.side_effect = ApiTelegramException("edit_message_text", None, result_json)

    # Should not raise exception
    _edit_or_send(bot, message, "text", markup=None)

    bot.edit_message_text.assert_called_once()
    bot.send_message.assert_not_called()


def test_edit_or_send_falls_back_to_send_message_on_error():
    """Если редактирование невозможно (например, сообщение удалено), отправляется новое сообщение."""
    bot = MagicMock()
    message = MagicMock()
    message.content_type = "text"
    message.chat.id = 123
    message.message_id = 456

    result_json = {"error_code": 400, "description": "Bad Request: message to edit not found"}
    bot.edit_message_text.side_effect = ApiTelegramException("edit_message_text", None, result_json)

    _edit_or_send(bot, message, "text", markup=None)

    bot.edit_message_text.assert_called_once()
    bot.send_message.assert_called_once_with(123, "text", reply_markup=None, parse_mode="HTML")
