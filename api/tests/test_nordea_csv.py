from datetime import date

from app.import_match import account_number_matches, compact, suggested_vendor_name
from app.nordea_csv import parse_nordea_csv

SAMPLE = """\ufeffBogføringsdato;Beløb;Afsender;Modtager;Navn;Beskrivelse;Saldo;Valuta;Afstemt;
Reserveret;-39,95;9040298476;;;REMA 1000 BRØNS;;DKK;;
2026/09/07;-33,00;9040298476;;KVICKLY ALLEROED;KVICKLY ALLEROED;10577,22;DKK;;
2026/09/07;-77,00;9040298476;;Vipps MobilePay;MobilePay Netto;11089,88;DKK;;
2026/08/31;7000,00;;9040298476;;Fra Lønkonto;20000,00;DKK;;
"""


def test_parse_nordea_rows() -> None:
    rows = parse_nordea_csv(SAMPLE.encode("utf-8"))
    assert len(rows) == 4
    assert rows[0].skip_reason
    booked = [row for row in rows if not row.skip_reason]
    assert booked[0].posted_on == date(2026, 9, 7)
    assert booked[0].amount_ore == -3300
    assert booked[1].description == "MobilePay Netto"
    assert booked[2].amount_ore == 700000
    assert {row.own_account for row in rows} == {"9040298476"}


def test_import_keys_differ_for_same_day_amount_when_balance_differs() -> None:
    csv = """Bogføringsdato;Beløb;Afsender;Modtager;Navn;Beskrivelse;Saldo;Valuta;
2026/01/02;-572,50;9040298476;;;ASE, A-KASSE;10597,28;DKK;
2026/01/02;-572,50;9040298476;;;ASE, A-KASSE;11169,78;DKK;
"""
    rows = parse_nordea_csv(csv.encode("utf-8"))
    assert rows[0].import_key != rows[1].import_key


def test_account_number_matches_reg_and_account() -> None:
    assert account_number_matches("2112-9040298476", "9040298476")
    assert compact("FOETEX") == "foetex"


def test_mobilepay_vendor_suggestion() -> None:
    rows = parse_nordea_csv(SAMPLE.encode("utf-8"))
    pay = next(row for row in rows if "Netto" in row.description)
    assert "Netto" in suggested_vendor_name(pay)
