from __future__ import annotations

import io
from typing import Any

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract

from app.services.hn_layout import parse_ocr_document
from app.services.hn_parser import ParsedReceipt


def _open_image(image_bytes: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(image_bytes))
    image = ImageOps.exif_transpose(image)
    if image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")
    return image


def preprocess(image: Image.Image) -> Image.Image:
    """Boost contrast on crumpled thermal photos before Tesseract."""
    width, height = image.size
    scale = 1.0
    if width < 1400:
        scale = 1400 / width
    if scale != 1.0:
        image = image.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=2)
    gray = ImageEnhance.Contrast(gray).enhance(1.6)
    gray = gray.filter(ImageFilter.SHARPEN)
    return gray


def _words_to_text(data: dict[str, list]) -> str:
    lines: list[list[tuple[int, str]]] = []
    n = len(data.get("text", []))
    for i in range(n):
        text = (data["text"][i] or "").strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1
        if not text or conf < 0:
            continue
        top = int(data["top"][i])
        left = int(data["left"][i])
        height = int(data["height"][i]) or 1
        if not lines:
            lines.append([(left, text)])
            last_top = top
            last_h = height
            continue
        if abs(top - last_top) <= max(int(last_h * 0.65), 10):
            lines[-1].append((left, text))
            last_h = max(last_h, height)
        else:
            lines.append([(left, text)])
            last_top = top
            last_h = height
    joined = []
    for line in lines:
        line.sort(key=lambda item: item[0])
        joined.append(" ".join(word for _, word in line))
    return "\n".join(joined)


def run_tesseract(image: Image.Image) -> str:
    config = "--oem 3 --psm 6"
    data = pytesseract.image_to_data(image, lang="dan+eng", config=config, output_type=pytesseract.Output.DICT)
    text = _words_to_text(data)
    if len([line for line in text.splitlines() if line.strip()]) >= 8:
        return text
    # Single-column fallback for very tall till slips
    data4 = pytesseract.image_to_data(image, lang="dan+eng", config="--oem 3 --psm 4", output_type=pytesseract.Output.DICT)
    alt = _words_to_text(data4)
    return alt if len(alt) > len(text) else text


def scan_receipt_image(image_bytes: bytes, content_type: str = "image/jpeg") -> tuple[ParsedReceipt, dict[str, Any], bool]:
    """Local Tesseract OCR + Harald Nyborg layout. Never calls a cloud API."""
    del content_type
    image = preprocess(_open_image(image_bytes))
    ocr_text = run_tesseract(image)
    parsed, payload, failed = parse_ocr_document(ocr_text)
    payload = dict(payload)
    payload["ocr_text"] = ocr_text
    payload["ocr_engine"] = "tesseract"
    return parsed, payload, failed
