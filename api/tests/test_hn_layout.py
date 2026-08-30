from app.services.hn_layout import detect_vendor, parse_hn_ocr_text, parse_item_line, parse_ocr_document
from app.services.hn_parser import normalize_receipt

HERLEV = """
harald nyborg
-ALTID LAVE PRISER!
HERLEV HOVEDGADE 41
2730 HERLEV
www.harald-nyborg.dk
CVR nr. DK-3778 3315
Dato Tid Kasse Fakturanr.
24.08.2026 10:29:54 01 682696 KONTANT
Varenr Antal Varetekst Ialt
45359 1 MALERRULLESÆT 10 CM 28,00
45359 1 MALERRULLESÆT 10 CM 28,00
4024 1 DANALIM SEALFLEX HYBRID GRA 49,00
44256 1 AFFALDSSÆK 70X110CM 30MY 1 RL 10,00
37205 1 SKURESVAMP 10-PAK 3,25
3075 1 MALERRULLESPAND 8L 29,50
3075 1 MALERRULLESPAND 8L 29,50
I A L T BETALINGSKORT 177,25
Heraf moms 35,45
Tak for besøget - og på gensyn i
Harald Nyborg HERLEV
Du blev betjent af Alex
*81-240826-682696*
"""


def test_detect_harald_nyborg() -> None:
    assert detect_vendor(HERLEV)["slug"] == "harald-nyborg"
    assert detect_vendor("netto kvittering")["slug"] is None


def test_item_line_positions() -> None:
    item = parse_item_line("45359 1 MALERRULLESÆT 10 CM 28,00")
    assert item == {
        "item_number": "45359",
        "quantity": 1,
        "description": "MALERRULLESÆT 10 CM",
        "line_total": "28,00",
    }


def test_parse_herlev_layout() -> None:
    payload = parse_hn_ocr_text(HERLEV)
    parsed = normalize_receipt(payload)
    assert parsed.vendor_slug == "harald-nyborg"
    assert parsed.invoice_no == "682696"
    assert parsed.total_ore == 17725
    assert parsed.vat_ore == 3545
    assert parsed.lines_sum_ok
    assert parsed.vat_ok
    assert len(parsed.lines) == 7
    assert parsed.store_name and "Herlev" in parsed.store_name


def test_unknown_vendor_is_training() -> None:
    parsed, _payload, failed = parse_ocr_document("something that is not a known till")
    assert failed is True
    assert parsed.vendor_slug is None
