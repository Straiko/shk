"""Распознавание текста через Yandex Cloud OCR API."""

import base64
import logging
import os
import re
import requests

logger = logging.getLogger(__name__)

YANDEX_OCR_URL = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"


def scan_text_ocr(photo_path: str, api_key: str | None = None) -> list[str]:
    """Распознать текст с изображения через Yandex Cloud OCR."""
    api_key = os.getenv("YANDEX_API_KEY") or (api_key if api_key and api_key != "helloworld" else None)
    folder_id = os.getenv("YANDEX_FOLDER_ID")

    if not api_key:
        logger.error("YANDEX_API_KEY не задан!")
        return []

    try:
        with open(photo_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        headers = {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json",
        }
        if folder_id:
            headers["x-folder-id"] = folder_id

        mime_type = "PNG" if photo_path.lower().endswith(".png") else "JPEG"

        payload = {
            "mimeType": mime_type,
            "languageCodes": ["*"],
            "model": "page",
            "content": image_base64,
        }

        response = requests.post(YANDEX_OCR_URL, headers=headers, json=payload, timeout=10)

        if response.status_code != 200:
            logger.warning(
                "Yandex OCR вернул ошибку %d: %s",
                response.status_code,
                response.text[:250],
            )
            return []

        data = response.json()
        full_text = data.get("result", {}).get("textAnnotation", {}).get("fullText", "")
        if not full_text:
            return []

        logger.info(
            "Yandex OCR успешно распознал текст: %s",
            full_text[:60].replace("\n", " "),
        )
        return _extract_codes(full_text)

    except requests.Timeout:
        logger.warning("Yandex OCR API timeout")
    except Exception:
        logger.exception("Ошибка при обращении к Yandex OCR")

    return []


def _extract_codes(text: str) -> list[str]:
    """Извлечь коды из текста."""
    codes: list[str] = []
    for word in text.split():
        clean = word.strip(".,;:!?'\"()[]{}")
        clean = re.sub(r"^[iIl1]{2}(?=\d{5,}$)", "ii", clean, flags=re.IGNORECASE)
        if len(clean) > 4 and re.match(r"^[A-Za-z0-9_-]+$", clean):
            if any(c.isdigit() for c in clean):
                codes.append(clean)
    return codes
