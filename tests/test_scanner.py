"""Тесты для сервиса сканирования штрих-кодов."""

from PIL import Image

from services.scanner import scan_barcodes


def test_scan_empty_image_returns_empty_list():
    """Пустое белое изображение не должно возвращать коды."""
    img = Image.new("RGB", (100, 100), "white")
    result = scan_barcodes(img)
    assert result == []


def test_scan_always_returns_list():
    """Результат всегда должен быть списком, даже при ошибке."""
    img = Image.new("RGB", (10, 10), "black")
    result = scan_barcodes(img)
    assert isinstance(result, list)


def test_scan_grayscale_image():
    """Grayscale изображение не должно вызывать ошибку."""
    img = Image.new("L", (200, 200), 128)
    result = scan_barcodes(img)
    assert isinstance(result, list)
