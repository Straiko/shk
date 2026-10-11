"""OCR распознавание текста через OCR.space API."""

import re
import logging
import requests

logger = logging.getLogger(__name__)

OCR_API_URL = "https://api.ocr.space/parse/image"

# Маскировка под реальный браузер для обхода блокировок Cloudflare
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def scan_text_ocr(photo_path: str, api_key: str) -> list[str]:
    """Распознать текст с изображения через OCR.space API."""
    if not api_key or api_key == "helloworld":
        logger.error("OCR API ключ не задан или используется заблокированный 'helloworld'!")

    for engine in ("1", "2"):  # Сначала пробуем более легкий Engine 1
        try:
            with open(photo_path, "rb") as f:
                response = requests.post(
                    OCR_API_URL,
                    files={"file": f},
                    data={
                        "apikey": api_key,
                        "language": "eng",
                        "OCREngine": engine,
                        "scale": "true",
                    },
                    headers=HEADERS,
                    timeout=15,
                )

            if response.status_code != 200:
                # Выводим первые 250 символов ответа, чтобы увидеть причину (Cloudflare или лимит)
                logger.warning(
                    "OCR Engine %s статус %d. Ответ сервера: %s",
                    engine,
                    response.status_code,
                    response.text[:250].replace("\n", " "),
                )
                continue

            result = response.json()
            if result.get("IsErroredOnProcessing"):
                logger.warning("OCR ошибка: %s", result.get("ErrorMessage"))
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
            logger.exception("Ошибка OCR запроса на Engine %s", engine)

    return []


def _extract_codes(text: str) -> list[str]:
    """Извлечь коды из распознанного текста с фильтрацией мусора."""
    codes: list[str] = []

    for word in text.split():
        clean = word.strip(".,;:!?'\"()[]{}")
        clean = re.sub(r"^[iIl1]{2}(?=\d{5,}$)", "ii", clean, flags=re.IGNORECASE)

        if len(clean) > 4 and re.match(r"^[A-Za-z0-9_-]+$", clean):
            if any(c.isdigit() for c in clean):
                codes.append(clean)

    return codes
