from app.money import format_dkk, parse_dkk_to_ore


def test_parse_danish_amount() -> None:
    assert parse_dkk_to_ore("1.234,50") == 123450
    assert parse_dkk_to_ore("-89,95 kr") == -8995
    assert parse_dkk_to_ore(10) == 1000


def test_format_dkk() -> None:
    assert format_dkk(123450) == "1.234,50"
    assert format_dkk(-8995) == "-89,95"
    assert format_dkk(0) == "0,00"
