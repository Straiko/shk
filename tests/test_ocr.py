"""Тесты для OCR-сервиса (только парсинг, без API-вызовов)."""

from services.ocr import _extract_codes


def test_extract_codes_with_valid_barcode():
    """Код с цифрами и буквами должен быть найден."""
    result = _extract_codes("ii1234567890")
    assert "ii1234567890" in result


def test_extract_codes_filters_short_text():
    """Слова короче 5 символов отфильтровываются."""
    result = _extract_codes("AB12")
    assert result == []


def test_extract_codes_filters_no_digits():
    """Слова без цифр отфильтровываются."""
    result = _extract_codes("ABCDEFGH")
    assert result == []


def test_extract_codes_filters_russian():
    """Русские слова не проходят фильтр."""
    result = _extract_codes("Привет мир Тестовый")
    assert result == []


def test_extract_codes_strips_punctuation():
    """Пунктуация удаляется перед анализом."""
    result = _extract_codes("(ABC12345)")
    assert "ABC12345" in result


def test_extract_codes_ocr_autocorrect():
    """Автоисправление 'i1' → 'ii' в начале кода перед цифрами."""
    result = _extract_codes("i11234567")
    assert "ii1234567" in result


def test_extract_codes_multiple():
    """Из текста с несколькими кодами извлекаются все."""
    result = _extract_codes("ABC12345 noise XYZ99887766")
    assert len(result) == 2
    assert "ABC12345" in result
    assert "XYZ99887766" in result
