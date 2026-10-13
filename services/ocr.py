"""Распознавание текста через Yandex Cloud OCR API."""

import base64
import io
import logging
import os
import re
import requests
from PIL import Image

logger = logging.getLogger(__name__)

YANDEX_OCR_URL = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"


def scan_text_ocr(photo_path: str, api_key: str | None = None) -> list[str]:
    """Распознать текст с изображения через Yandex Cloud OCR."""
    key = (api_key or os.getenv("YANDEX_API_KEY") or "").strip()

    # Защита: если ключ не начинается на AQVN, проверяем OCR_API_KEY
    if not key.startswith("AQVN"):
        fallback_key = os.getenv("OCR_API_KEY", "").strip()
        if fallback_key.startswith("AQVN"):
            key = fallback_key

    # Если ключ всё ещё отсутствует или это старый ключ другого сервиса (например, K883...)
    if not key or not key.startswith("AQVN"):
        logger.error(
            "YANDEX_API_KEY не задан или указан неверно! "
            "Получен ключ: %s. Ключ Яндекса должен начинаться на 'AQVN...'. "
            "Пожалуйста, добавьте переменную YANDEX_API_KEY в панели управления Bothost.",
            f"'{key[:4]}***'" if key else "None",
        )
        return []

    folder_id = os.getenv("YANDEX_FOLDER_ID", "").strip() or None

    try:
        # Нормализуем любое входное изображение (WebP, RGBA и т.д.) в стандартный JPEG
        try:
            with Image.open(photo_path) as img:
                rgb_img = img.convert("RGB")
                buf = io.BytesIO()
                rgb_img.save(buf, format="JPEG", quality=95)
                image_bytes = buf.getvalue()
        except Exception:
            with open(photo_path, "rb") as f:
                image_bytes = f.read()

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        headers = {
            "Authorization": f"Api-Key {key}",
            "Content-Type": "application/json",
        }
        if folder_id:
            headers["x-folder-id"] = folder_id

        payload = {
            "mimeType": "JPEG",
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
    """Extract barcode and product codes from OCR text."""
    # Normalize warehouse prefixes (RDC, WB, OZON) that OCR may separate with spaces, dashes, or Cyrillic letters
    def _normalize_prefix(m: re.Match) -> str:
        prefix = m.group(1).upper()
        if prefix in ("RDC", "РДЦ", "РДС"):
            return "RDC_"
        elif prefix in ("WB", "ВБ"):
            return "WB_"
        return "OZON_"

    text = re.sub(
        r"\b(RDC|РДЦ|РДС|WB|ВБ|OZON|ОЗОН)[_\s\-]+(?=\d{5,})",
        _normalize_prefix,
        text,
        flags=re.IGNORECASE,
    )

    codes: list[str] = []
    for word in text.split():

        w = word.strip()

        # Fix OCR artifacts for Wildberries 'ii' prefix before stripping punctuation.
        # Yandex OCR often confuses screen font 'ii' with '!!', '!i', 'i!', '||', or Cyrillic 'й'.
        # If 3 punctuation/pipe marks precede 10 digits, the first two are 'ii' and third is digit '1' (e.g. !!!538... -> ii1538...).
        w = re.sub(r"^([!|]{3}|[!|iI]{2}[1!|])(?=\d{10}$)", "ii1", w)
        w = re.sub(r"^([!|]{2}|[!|][iIl]|[iIl][!|])(?=\d{5,})", "ii", w)
        w = re.sub(r"^[йЙ](?=\d{5,})", "ii", w)


        # Strip surrounding punctuation
        clean = w.strip(".,;:!?\'\"()[]{}")

        # Handle cases where OCR sees single 'i' or 'l' before 10-12 digits without consuming any digits
        clean = re.sub(r"^[iIl](?=\d{10,12}$)", "ii", clean)

        # Handle misread prefix like 'i1' or '1i' (must include a letter, never pure digits '11')
        clean = re.sub(r"^([iIl][1]|[1][iIl])(?=\d{5,}$)", "ii", clean, flags=re.IGNORECASE)

        # Standardize 'II' to lowercase 'ii'
        clean = re.sub(r"^[iI]{2}(?=\d{5,})", "ii", clean)

        # Validate code structure (alphanumeric with - and _, contains at least one digit)
        if len(clean) > 4 and re.match(r"^[A-Za-z0-9_-]+$", clean):
            if any(c.isdigit() for c in clean):
                codes.append(clean)

    # Return unique codes preserving original order
    return list(dict.fromkeys(codes))

