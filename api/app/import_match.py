from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from typing import Any

from app.nordea_csv import ParsedRow

PAY_PREFIXES = (
    "vipps mobilepay",
    "mobilepay",
    "zettle-*",
    "zettle-",
    "zettle",
    "nets ",
    "visa ",
    "mastercard ",
)


def fold(text: str) -> str:
    raw = (text or "").casefold().replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    nfkd = unicodedata.normalize("NFKD", raw)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", fold(text))


def strip_pay_prefix(text: str) -> str:
    folded = fold(text).strip()
    for prefix in PAY_PREFIXES:
        if folded.startswith(prefix):
            return text[len(prefix) :].lstrip(" -*")
    return text


def vendor_texts(row: ParsedRow) -> list[str]:
    values: list[str] = []
    for raw in (row.description, row.name, strip_pay_prefix(row.description), strip_pay_prefix(row.name)):
        text = (raw or "").strip()
        if text and text not in values:
            values.append(text)
    return values


@dataclass
class NameMatch:
    id: str
    name: str
    score: float
    kind: str  # exact | close | contains


def _score_against(candidate: str, target_name: str) -> tuple[float, str] | None:
    cand_c = compact(candidate)
    tgt_c = compact(target_name)
    if not cand_c or not tgt_c:
        return None
    if cand_c == tgt_c:
        return 1.0, "exact"
    if len(tgt_c) >= 4 and tgt_c in cand_c:
        return 0.9, "contains"
    if len(cand_c) >= 4 and cand_c in tgt_c:
        return 0.88, "contains"
    ratio = SequenceMatcher(None, cand_c, tgt_c).ratio()
    if ratio >= 0.82:
        return round(ratio, 3), "close"
    return None


def best_vendor_match(row: ParsedRow, vendors: list[Any]) -> NameMatch | None:
    best: NameMatch | None = None
    for vendor in vendors:
        for text in vendor_texts(row):
            scored = _score_against(text, vendor.name)
            if not scored:
                continue
            score, kind = scored
            if best is None or score > best.score:
                best = NameMatch(id=str(vendor.id), name=vendor.name, score=score, kind=kind)
    return best


def best_category_match(row: ParsedRow, categories: list[Any]) -> NameMatch | None:
    best: NameMatch | None = None
    haystack = " ".join(vendor_texts(row))
    for category in categories:
        scored = _score_against(haystack, category.name)
        if not scored:
            continue
        score, kind = scored
        if best is None or score > best.score:
            best = NameMatch(id=str(category.id), name=category.name, score=score, kind=kind)
    return best


def suggested_vendor_name(row: ParsedRow) -> str:
    for text in vendor_texts(row):
        cleaned = strip_pay_prefix(text).strip() or text
        if cleaned:
            return cleaned[:200]
    return row.label[:200]


def account_number_matches(stored: str | None, detected: str | None) -> bool:
    left = compact(stored or "")
    right = compact(detected or "")
    if not left or not right:
        return False
    return left == right or left.endswith(right) or right.endswith(left)
