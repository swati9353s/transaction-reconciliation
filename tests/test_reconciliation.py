from datetime import datetime

from reconciliation.comparison import (
    compare_transactions,
    is_candidate_match,
)


def make_transaction(
    amount=100,
    minutes=0,
    quantity=1,
):
    return {
        "external_id": "T-1",
        "traded_at": datetime(2025, 1, 1, 10, minutes),
        "instrument": "BTC-USD",
        "side": "BUY",
        "quantity": quantity,
        "price": 100,
        "gross_amount": amount,
        "state": "SETTLED",
    }


def test_exact_match():
    ledger = make_transaction()
    statement = make_transaction()

    differences = compare_transactions(
        ledger,
        statement,
    )

    assert differences == {}


def test_small_amount_difference_allowed():
    ledger = make_transaction(amount=100)
    statement = make_transaction(amount=104)

    differences = compare_transactions(
        ledger,
        statement,
    )

    assert "amount" not in differences


def test_large_amount_difference():
    ledger = make_transaction(amount=100)
    statement = make_transaction(amount=120)

    differences = compare_transactions(
        ledger,
        statement,
    )

    assert "amount" in differences


def test_time_difference_within_tolerance():
    ledger = make_transaction(minutes=0)
    statement = make_transaction(minutes=20)

    assert is_candidate_match(
        ledger,
        statement,
    )


def test_quantity_difference():
    ledger = make_transaction(quantity=1)
    statement = make_transaction(quantity=2)

    differences = compare_transactions(
        ledger,
        statement,
    )

    assert "quantity" in differences