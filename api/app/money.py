from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def parse_dkk_to_ore(value: Any) -> int | None:
    """Parse a Danish DKK amount (comma decimal, optional thousand dots) to øre."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        # Integers from vision are kroner if small, already-øre if huge — treat as kroner.
        return value * 100
    if isinstance(value, float):
        return int((Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    text = str(value).strip()
    for token in ("kr.", "kr", "KR", "DKK"):
        text = text.replace(token, "")
    text = text.strip().replace("\u00a0", "").replace(" ", "")
    if not text:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        amount = Decimal(text)
    except Exception:
        return None
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def format_dkk(ore: int | None) -> str:
    if ore is None:
        return ""
    sign = "-" if ore < 0 else ""
    ore = abs(ore)
    kroner, rest = divmod(ore, 100)
    grouped = f"{kroner:,}".replace(",", ".")
    return f"{sign}{grouped},{rest:02d}"


def expected_vat_ore(total_ore: int, rate_percent: int = 25) -> int:
    """VAT included in the total (Danish 25% → VAT = total * 20%)."""
    return int(
        (Decimal(total_ore) * Decimal(rate_percent) / Decimal(100 + rate_percent)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
