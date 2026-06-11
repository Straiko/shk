"""Декоратор rate limiting для защиты от спама."""

import time
import logging
from functools import wraps
from threading import Lock
from typing import Callable

logger = logging.getLogger(__name__)


class RateLimiter:
    """Контролирует частоту запросов от пользователей."""

    def __init__(self, interval_seconds: int = 2) -> None:
        self._interval = interval_seconds
        self._user_timestamps: dict[int, float] = {}
        self._lock = Lock()

    def is_allowed(self, user_id: int) -> bool:
        """Проверить, может ли пользователь отправить запрос."""
        current_time = time.time()
        with self._lock:
            # Очистка старых записей для предотвращения утечки памяти
            if len(self._user_timestamps) > 1000:
                self._user_timestamps = {
                    uid: ts for uid, ts in self._user_timestamps.items()
                    if current_time - ts < self._interval * 10
                }

            last_time = self._user_timestamps.get(user_id, 0)
            if current_time - last_time < self._interval:
                return False
            self._user_timestamps[user_id] = current_time
            return True


def rate_limit(limiter: RateLimiter, bot) -> Callable:
    """
    Фабрика декораторов для rate limiting.

    Использование:
        @bot.message_handler(...)
        @rate_limit(limiter, bot)
        def handler(message): ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            if not limiter.is_allowed(message.from_user.id):
                bot.reply_to(message, "⏳ Подожди немного, не спеши!")
                return None
            return func(message, *args, **kwargs)
        return wrapper
    return decorator
