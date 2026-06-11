"""Тесты для конфигурации."""

import os
import pytest

from config import load_config


def test_config_fails_without_token(monkeypatch):
    """Без BOT_TOKEN бот не должен запускаться."""
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        load_config()


def test_config_loads_with_token(monkeypatch):
    """С BOT_TOKEN конфигурация загружается успешно."""
    monkeypatch.setenv("BOT_TOKEN", "test-token-123")
    config = load_config()
    assert config.bot_token == "test-token-123"
    assert config.ocr_api_key == "helloworld"
    assert config.rate_limit_seconds == 2
    assert config.num_threads == 4


def test_config_custom_values(monkeypatch):
    """Переменные окружения переопределяют дефолты."""
    monkeypatch.setenv("BOT_TOKEN", "custom-token")
    monkeypatch.setenv("OCR_API_KEY", "custom-key")
    monkeypatch.setenv("RATE_LIMIT_SECONDS", "5")
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "50")
    monkeypatch.setenv("NUM_THREADS", "8")

    config = load_config()
    assert config.bot_token == "custom-token"
    assert config.ocr_api_key == "custom-key"
    assert config.rate_limit_seconds == 5
    assert config.max_file_size_mb == 50
    assert config.num_threads == 8


def test_config_is_frozen(monkeypatch):
    """Config должен быть immutable (frozen dataclass)."""
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    config = load_config()
    with pytest.raises(AttributeError):
        config.bot_token = "hacked"
