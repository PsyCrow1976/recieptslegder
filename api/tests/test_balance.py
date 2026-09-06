from datetime import date

from app.money import ledger_balance


def test_balance_adds_all_entries_without_start_date() -> None:
    assert (
        ledger_balance(
            100000,
            None,
            [(date(2025, 12, 1), -1000), (date(2026, 1, 2), 5000)],
        )
        == 104000
    )


def test_balance_ignores_entries_before_start_date() -> None:
    assert (
        ledger_balance(
            100000,
            date(2026, 1, 1),
            [
                (date(2025, 12, 31), -99999),
                (date(2026, 1, 1), -2000),
                (date(2026, 1, 2), 5000),
            ],
        )
        == 103000
    )
