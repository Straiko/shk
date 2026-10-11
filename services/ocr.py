"""OCR распознавание текста через OCR.space API."""

import re
import logging
import requests

logger = logging.getLogger(__name__)

OCR_API_URL = "https://api.ocr.space/parse/image"


def scan_text_ocr(photo_path: str, api_key: str) -> list[str]:
    """
    Распознать текст с изображения через OCR.space API.
    При сбое Engine 2 делает автоматический fallback на Engine 1.
    """
    # Пробуем движки по очереди: сначала 2, при ошибке 503/таймауте — 1
    for engine in ("2", "1"):
        try:
            with open(photo_path, "rb") as f:
                response = requests.post(
                    OCR_API_URL,
                    files={"file": f},
                    data={
                        "apikey": api_key,
                        "language": "eng",
                        "OCREngine": engine,
                        "scale": "true",  # улучшает читаемость мелких цифр и ШК
                    },
                    timeout=15,
                )

            if response.status_code == 503:
                logger.warning(
                    "OCR Engine %s вернул 503 (сервис перегружен). Пробуем резервный вариант...",
                    engine,
                )
                continue

            if response.status_code != 200:
                logger.warning(
                    "OCR API вернул статус %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return []

            result = response.json()
            if result.get("IsErroredOnProcessing"):
                error_details = result.get("ErrorMessage", ["Неизвестная ошибка"])
                logger.warning("OCR.space внутренняя ошибка: %s", error_details)
                continue

            if not result.get("ParsedResults"):
                return []

            text = result["ParsedResults"][0].get("ParsedText", "")
            codes = _extract_codes(text)
            if codes:
                return codes

        except requests.Timeout:
            logger.warning("OCR API timeout на Engine %s", engine)
        except Exception:
            logger.exception("OCR API непредвиденная ошибка на Engine %s", engine)

    return []


def _extract_codes(text: str) -> list[str]:
    """Извлечь коды из распознанного текста с фильтрацией мусора."""
    codes: list[str] = []

    for word in text.split():
        clean = word.strip(".,;:!?'\"()[]{}")
        # Автоисправление частой ошибки OCR: путает 'i'/'l'/'1'
        clean = re.sub(r"^[iIl1]{2}(?=\d{5,}$)", "ii", clean, flags=re.IGNORECASE)

        # Фильтр: только английские буквы, цифры, - и _
        if len(clean) > 4 and re.match(r"^[A-Za-z0-9_-]+$", clean):
            if any(c.isdigit() for c in clean):
                codes.append(clean)

    return codes
