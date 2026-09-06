from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import datetime, date

from app.money import parse_dkk_to_ore

HEADER_ALIASES = {
    "bogføringsdato": "posted",
    "bogforingsdato": "posted",
    "beløb": "amount",
    "belob": "amount",
    "afsender": "sender",
    "modtager": "receiver",
    "navn": "name",
    "beskrivelse": "description",
    "saldo": "balance",
    "valuta": "currency",
}


@dataclass
class ParsedRow:
    line_number: int
    posted_on: date | None
    amount_ore: int | None
    name: str
    description: str
    balance_ore: int | None
    currency: str
    own_account: str | None
    import_key: str
    skip_reason: str | None = None

    @property
    def label(self) -> str:
        return self.description or self.name or "Entry"


def _decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _header_key(cell: str) -> str:
    compact = cell.strip().casefold().replace("ø", "o").replace("å", "a").replace("æ", "ae")
    return HEADER_ALIASES.get(compact, compact)


def digits_only(value: str | None) -> str:
    return re.sub(r"\D+", "", value or "")


def parse_nordea_date(value: str) -> date | None:
    text = (value or "").strip()
    if not text or text.casefold().startswith("reserveret"):
        return None
    for fmt in ("%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_nordea_csv(raw: bytes) -> list[ParsedRow]:
    text = _decode(raw)
    reader = csv.reader(io.StringIO(text), delimiter=";")
    try:
        header = next(reader)
    except StopIteration as exc:
        raise ValueError("The CSV file is empty") from exc

    index = {_header_key(cell): i for i, cell in enumerate(header) if cell.strip()}
    if "posted" not in index or "amount" not in index:
        raise ValueError("This does not look like a Nordea account CSV (need Bogføringsdato and Beløb)")

    def cell(row: list[str], key: str) -> str:
        pos = index.get(key)
        if pos is None or pos >= len(row):
            return ""
        return (row[pos] or "").strip()

    parsed: list[ParsedRow] = []
    for line_number, row in enumerate(reader, start=2):
        if not any(value.strip() for value in row):
            continue
        posted_raw = cell(row, "posted")
        amount_ore = parse_dkk_to_ore(cell(row, "amount"))
        name = cell(row, "name")
        description = cell(row, "description")
        balance_ore = parse_dkk_to_ore(cell(row, "balance"))
        currency = cell(row, "currency") or "DKK"
        sender = digits_only(cell(row, "sender"))
        receiver = digits_only(cell(row, "receiver"))
        own_account = sender or receiver or None
        posted_on = parse_nordea_date(posted_raw)
        skip_reason = None
        if posted_raw.casefold().startswith("reserveret"):
            skip_reason = "Reserved (not booked yet)"
        elif posted_on is None:
            skip_reason = "Missing booking date"
        elif amount_ore is None:
            skip_reason = "Missing amount"

        key_src = "|".join(
            [
                posted_on.isoformat() if posted_on else posted_raw,
                str(amount_ore if amount_ore is not None else ""),
                name.casefold(),
                description.casefold(),
                str(balance_ore if balance_ore is not None else ""),
            ]
        )
        import_key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()
        parsed.append(
            ParsedRow(
                line_number=line_number,
                posted_on=posted_on,
                amount_ore=amount_ore,
                name=name,
                description=description,
                balance_ore=balance_ore,
                currency=currency,
                own_account=own_account,
                import_key=import_key,
                skip_reason=skip_reason,
            )
        )
    if not parsed:
        raise ValueError("No rows found in the CSV")
    return parsed


def detected_account_number(rows: list[ParsedRow]) -> str | None:
    counts: dict[str, int] = {}
    for row in rows:
        if row.own_account:
            counts[row.own_account] = counts.get(row.own_account, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)
