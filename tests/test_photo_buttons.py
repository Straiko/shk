"""Tests for inline barcode buttons and keyboard generation."""

from handlers.photo import _build_codes_keyboard, _format_reply, _LONG_CODE_CACHE


def test_format_reply_single_code():
    """Single code format should only display the code."""
    reply = _format_reply(["12345678"], "12345678")
    assert "✅ Найдено:" in reply
    assert "<code>12345678</code>" in reply
    assert "Нажмите кнопку" not in reply


def test_format_reply_multiple_codes():
    """Multiple codes format should prompt user with button instruction."""
    codes = ["123456", "789012"]
    reply = _format_reply(codes, "789012")
    assert "🔍 Найдено" in reply
    assert "• <code>123456</code>" in reply
    assert "• <code>789012</code>" in reply
    assert "Нажмите кнопку ниже" in reply


def test_build_codes_keyboard_short_codes():
    """Short codes should use direct callback_data gen_bc:."""
    codes = ["12345678", "ABC98765"]
    markup = _build_codes_keyboard(codes)

    assert len(markup.keyboard) >= 1
    # Check all created buttons
    all_buttons = [btn for row in markup.keyboard for btn in row]
    assert len(all_buttons) == 2

    assert all_buttons[0].callback_data == "gen_bc:12345678"
    assert "12345678" in all_buttons[0].text

    assert all_buttons[1].callback_data == "gen_bc:ABC98765"
    assert "ABC98765" in all_buttons[1].text


def test_build_codes_keyboard_long_code_overflow():
    """Long codes exceeding 50 bytes should use hash cache callback_data."""
    long_code = "https://example.com/very/long/url/with/many/parameters/code12345678901234567890"
    markup = _build_codes_keyboard([long_code])

    all_buttons = [btn for row in markup.keyboard for btn in row]
    assert len(all_buttons) == 1
    btn = all_buttons[0]

    assert btn.callback_data.startswith("gen_bch:")
    # Ensure byte length stays strictly within Telegram's 64-byte limit
    assert len(btn.callback_data.encode("utf-8")) < 64

    # Verify code is saved in cache
    code_hash = btn.callback_data.replace("gen_bch:", "")
    assert _LONG_CODE_CACHE[code_hash] == long_code
    assert "..." in btn.text
