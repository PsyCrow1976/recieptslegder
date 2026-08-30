from __future__ import annotations

import base64
import json
import re
from typing import Any

from openai import OpenAI

from app.config import settings
from app.services.hn_parser import ParsedReceipt, normalize_receipt

SCAN_PROMPT = """You are reading a Danish shop receipt photo (often a crumpled thermal till slip).

Extract a JSON object with exactly this shape:
{
  "vendor": string,
  "store_name": string or null,
  "store_address": string or null,
  "cvr": string or null,
  "date": "DD.MM.YYYY",
  "time": "HH:MM:SS",
  "kasse": string or null,
  "fakturanr": string or null,
  "payment_method": string or null,
  "barcode": string or null,
  "cashier": string or null,
  "total": "Danish amount with comma decimals, e.g. 1121,50",
  "vat": "Heraf moms, same format",
  "lines": [
    {
      "item_number": "varenr digits",
      "quantity": 1,
      "description": "varetekst as printed",
      "line_total": "Ialt amount with comma decimals"
    }
  ]
}

Rules:
- Harald Nyborg receipts have columns Varenr, Antal, Varetekst, Ialt.
- Keep duplicate SKUs as separate lines (do not merge).
- Danish amounts use comma as decimal separator (29,50 not 29.50).
- Date is Dato, time is Tid, register is Kasse, invoice is Fakturanr.
- Total is the I ALT line (often followed by BETALINGSKORT). VAT is Heraf moms.
- Cashier is the name after "Du blev betjent af".
- Prefer the printed numbers over guesses. If a field is unreadable, use null.
- Return JSON only, no markdown.
"""


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Vision model did not return JSON")
    return json.loads(text[start : end + 1])


def scan_receipt_image(image_bytes: bytes, content_type: str = "image/jpeg") -> tuple[ParsedReceipt, dict[str, Any]]:
    if not settings.xai_api_key:
        raise RuntimeError(
            "XAI_API_KEY is not set. Add a SpaceXAI (xAI) key to .env to scan receipt photos."
        )

    mime = content_type if content_type in {"image/jpeg", "image/png", "image/jpg"} else "image/jpeg"
    if mime == "image/jpg":
        mime = "image/jpeg"
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"

    client = OpenAI(api_key=settings.xai_api_key, base_url=settings.xai_base_url)
    response = client.responses.create(
        model=settings.xai_model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": data_url, "detail": "high"},
                    {"type": "input_text", "text": SCAN_PROMPT},
                ],
            }
        ],
    )
    raw_text = getattr(response, "output_text", None) or ""
    if not raw_text:
        # Fall back to walking output items
        chunks: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    chunks.append(text)
        raw_text = "\n".join(chunks)
    payload = _extract_json(raw_text)
    parsed = normalize_receipt(payload)
    return parsed, payload
