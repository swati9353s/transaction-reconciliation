from reconciliation.parser import parse_ledger, parse_statement


def test_parse_ledger():
    transactions = parse_ledger("data/ledger.csv")

    assert len(transactions) == 9

    assert transactions[0]["external_id"] == "T-1001"
    assert transactions[0]["side"] == "BUY"
    assert transactions[0]["quantity"] == 0.50

    assert transactions[-1]["external_id"] == "T-1009"


def test_parse_statement():
    transactions = parse_statement("data/statement.csv")

    assert len(transactions) == 8

    assert transactions[0]["external_id"] == "T-1001"
    assert transactions[0]["side"] == "BUY"