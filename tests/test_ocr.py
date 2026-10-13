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


def test_scan_text_ocr_missing_key(monkeypatch, tmp_path):
    """При отсутствии API ключа возвращается пустой список."""
    monkeypatch.delenv("YANDEX_API_KEY", raising=False)
    img_file = tmp_path / "test.jpg"
    img_file.write_bytes(b"dummy")

    from services.ocr import scan_text_ocr
    assert scan_text_ocr(str(img_file), api_key=None) == []


def test_scan_text_ocr_invalid_key(monkeypatch, tmp_path):
    """Ключ, не начинающийся на AQVN, отклоняется."""
    monkeypatch.setenv("YANDEX_API_KEY", "K88309127788957")
    img_file = tmp_path / "test.jpg"
    img_file.write_bytes(b"dummy")

    from services.ocr import scan_text_ocr
    assert scan_text_ocr(str(img_file)) == []


def test_scan_text_ocr_success(monkeypatch, tmp_path):
    """Успешный ответ от Yandex OCR возвращает извлеченные коды."""
    monkeypatch.setenv("YANDEX_API_KEY", "AQVN_test_key")
    monkeypatch.setenv("YANDEX_FOLDER_ID", "test-folder")
    img_file = tmp_path / "test.jpg"
    img_file.write_bytes(b"dummy")

    class MockResponse:
        status_code = 200

        def json(self):
            return {
                "result": {
                    "textAnnotation": {
                        "fullText": "Код товара: ii1234567890"
                    }
                }
            }

    monkeypatch.setattr("requests.post", lambda *args, **kwargs: MockResponse())

    from services.ocr import scan_text_ocr
    result = scan_text_ocr(str(img_file))
    assert result == ["ii1234567890"]


def test_extract_codes_exclamation_marks_wb_prefix():
    """OCR artifacts '!!', '!!!' or '!i' before digits should be converted to 'ii'."""
    result = _extract_codes("!!15383958731 !!!5384025333 !i9988776655")
    assert result == ["ii15383958731", "ii15384025333", "ii9988776655"]



def test_extract_codes_preserves_digits_starting_with_11():
    """Numbers starting with 11 must NOT have their actual digits replaced by ii."""
    result = _extract_codes("!!11039592225 !!11039592226")
    assert result == ["ii11039592225", "ii11039592226"]

    # Pure numeric code starting with 11 should remain untouched
    numeric_result = _extract_codes("11039592225 644520696")
    assert numeric_result == ["11039592225", "644520696"]


def test_extract_codes_cyrillic_short_i_wb_prefix():
    """Cyrillic 'й' misread by OCR should be converted to 'ii'."""
    result = _extract_codes("й11039592226")
    assert result == ["ii11039592226"]


def test_extract_codes_rdc_and_warehouse_prefixes():
    """Warehouse prefixes (RDC, BOX, KGT, SKU, WB, etc.) separated by space or dash should be preserved."""
    assert _extract_codes("RDC_1525415416") == ["RDC_1525415416"]
    assert _extract_codes("RDC 1525415416") == ["RDC_1525415416"]
    assert _extract_codes("РДЦ 1525415416") == ["RDC_1525415416"]
    assert _extract_codes("WB 123456789") == ["WB_123456789"]
    assert _extract_codes("BOX_ 987654321") == ["BOX_987654321"]
    assert _extract_codes("KGT 1122334455") == ["KGT_1122334455"]
    assert _extract_codes("CUSTOM- 5566778899") == ["CUSTOM-5566778899"]





