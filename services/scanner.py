"""Сканирование штрих-кодов и QR-кодов с изображений."""

import logging
from PIL import Image, ImageEnhance, ImageOps
import zxingcpp

logger = logging.getLogger(__name__)


def scan_barcodes(img: Image.Image) -> list[zxingcpp.Barcode]:
    """
    Сканировать штрих-коды и 2D-коды (DataMatrix, QR, Code128 и т.д.) с изображения.

    Делает несколько попыток с разными фильтрами и алгоритмами бинаризации:
    1. Оригинал
    2. Автоконтраст (растягивание динамического диапазона бледной лазерной гравировки)
    3. Высокий контраст
    4. Повышенная резкость
    5. Увеличение x2
    6. Центральный кроп (для мелких кодов в центре кадра)
    7. Бинаризатор GlobalHistogram (эффективен для белых крышек/контрастных зон)
    """
    try:
        if img.mode != "RGB":
            img = img.convert("RGB")
        gray = img.convert("L")
        w, h = img.size

        # Базовые варианты обработки изображения
        attempts = [
            img,
            ImageOps.autocontrast(gray).convert("RGB"),
            ImageEnhance.Contrast(gray).enhance(2.0).convert("RGB"),
            ImageEnhance.Sharpness(gray).enhance(3.0).convert("RGB"),
            img.resize((w * 2, h * 2), Image.Resampling.LANCZOS),
        ]

        # Центральный кроп для изоляции кода от краев кадра
        if w > 150 and h > 150:
            cx1, cy1 = int(w * 0.15), int(h * 0.15)
            cx2, cy2 = int(w * 0.85), int(h * 0.85)
            crop_center = img.crop((cx1, cy1, cx2, cy2))
            crop_gray = crop_center.convert("L")
            attempts.append(crop_center)
            attempts.append(ImageOps.autocontrast(crop_gray).convert("RGB"))

        # Стандартный проход с LocalAverage бинаризатором
        for attempt_img in attempts:
            results = zxingcpp.read_barcodes(attempt_img)
            if results:
                return results

        # Повторный проход с GlobalHistogram бинаризатором (лучше читает матричные коды на крышках)
        for attempt_img in attempts[:4]:
            results = zxingcpp.read_barcodes(attempt_img, binarizer=zxingcpp.Binarizer.GlobalHistogram)
            if results:
                return results

    except Exception:
        logger.exception("Ошибка сканирования штрих-кода")

    return []
