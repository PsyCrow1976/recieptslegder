import json
from pathlib import Path

from app.money import expected_vat_ore, format_dkk, parse_dkk_to_ore
from app.services.hn_parser import normalize_receipt

FIXTURES = Path(__file__).parent / "fixtures" / "hn_receipts.json"


def test_parse_danish_amounts() -> None:
    assert parse_dkk_to_ore("7,50") == 750
    assert parse_dkk_to_ore("1.121,50") == 112150
    assert parse_dkk_to_ore("1121,50") == 112150
    assert parse_dkk_to_ore("29,50") == 2950
    assert parse_dkk_to_ore(28.00) == 2800
    assert parse_dkk_to_ore("3,25") == 325
    assert format_dkk(112150) == "1.121,50"
    assert expected_vat_ore(112150) == 22430
    assert expected_vat_ore(15600) == 3120
    assert expected_vat_ore(17725) == 3545


def test_training_receipt_totals() -> None:
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert len(fixtures) == 6
    for fixture in fixtures:
        parsed = normalize_receipt(fixture["parse"])
        assert parsed.vendor_slug == "harald-nyborg"
        assert parsed.store_name == fixture["expected_store"]
        assert parsed.invoice_no == fixture["expected_invoice"]
        assert parsed.total_ore == fixture["expected_total_ore"]
        assert parsed.vat_ore == fixture["expected_vat_ore"]
        assert parsed.lines_sum_ok is True or abs(parsed.lines_sum_ore - parsed.total_ore) <= 1
        assert parsed.vat_ok is True
        assert len(parsed.lines) == fixture["expected_line_count"]
        skus = [line.item_number for line in parsed.lines]
        for sku in fixture["must_contain_skus"]:
            assert sku in skus
