"""Тесты для RateLimiter."""

import time
from utils.rate_limiter import RateLimiter


def test_first_request_allowed():
    """Первый запрос от пользователя всегда разрешён."""
    limiter = RateLimiter(interval_seconds=2)
    assert limiter.is_allowed(user_id=1) is True


def test_rapid_request_blocked():
    """Повторный запрос слишком быстро — заблокирован."""
    limiter = RateLimiter(interval_seconds=10)
    limiter.is_allowed(user_id=1)
    assert limiter.is_allowed(user_id=1) is False


def test_different_users_independent():
    """Разные пользователи не влияют друг на друга."""
    limiter = RateLimiter(interval_seconds=10)
    limiter.is_allowed(user_id=1)
    assert limiter.is_allowed(user_id=2) is True


def test_request_allowed_after_interval():
    """После истечения интервала запрос снова разрешён."""
    limiter = RateLimiter(interval_seconds=0)  # 0 секунд = без ограничений
    limiter.is_allowed(user_id=1)
    time.sleep(0.01)
    assert limiter.is_allowed(user_id=1) is True
