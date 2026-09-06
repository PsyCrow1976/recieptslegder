from types import SimpleNamespace

from app.import_match import best_category_match, best_vendor_match
from app.nordea_csv import ParsedRow
from datetime import date


def _row(**kwargs) -> ParsedRow:
    defaults = dict(
        line_number=2,
        posted_on=date(2026, 9, 7),
        amount_ore=-3300,
        name="",
        description="",
        balance_ore=0,
        currency="DKK",
        own_account="9040298476",
        import_key="x",
    )
    defaults.update(kwargs)
    return ParsedRow(**defaults)


def test_exact_vendor_match() -> None:
    vendor = SimpleNamespace(id="11111111-1111-1111-1111-111111111111", name="Kvickly Alleroed")
    match = best_vendor_match(_row(name="KVICKLY ALLEROED", description="KVICKLY ALLEROED"), [vendor])
    assert match is not None
    assert match.kind == "exact"


def test_close_vendor_from_description() -> None:
    vendor = SimpleNamespace(id="11111111-1111-1111-1111-111111111111", name="Netto")
    match = best_vendor_match(_row(name="Vipps MobilePay", description="MobilePay Netto"), [vendor])
    assert match is not None
    assert match.name == "Netto"


def test_category_contains() -> None:
    category = SimpleNamespace(id="22222222-2222-2222-2222-222222222222", name="Tennis")
    match = best_category_match(_row(name="BALLERUP TENNISKLUB", description="BALLERUP TENNISKLUB"), [category])
    assert match is not None
    assert match.name == "Tennis"
