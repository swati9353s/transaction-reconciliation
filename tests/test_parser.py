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

def test_file_hash_changes_when_file_changes(tmp_path):
    from routes.reconciliation_routes import calculate_file_hash

    file_path = tmp_path / "test.csv"

    file_path.write_text("id,amount\n1,100\n", encoding="utf-8")

    first_hash = calculate_file_hash(file_path)

    file_path.write_text("id,amount\n1,200\n", encoding="utf-8")

    second_hash = calculate_file_hash(file_path)

    assert first_hash != second_hash

def test_same_file_content_produces_same_hash(tmp_path):
    from routes.reconciliation_routes import calculate_file_hash

    file_path = tmp_path / "test.csv"

    file_path.write_text(
        "id,amount\n1,100\n",
        encoding="utf-8",
    )

    first_hash = calculate_file_hash(file_path)
    second_hash = calculate_file_hash(file_path)

    assert first_hash == second_hash