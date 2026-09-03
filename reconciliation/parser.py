import csv
from datetime import datetime


def parse_ledger(path):
    transactions = []

    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            transactions.append({
                "external_id": row["trade_id"],
                "traded_at": parse_datetime(row["traded_at"]),
                "instrument": row["instrument"],
                "side": normalize_side(row["side"]),
                "quantity": float(row["quantity"]),
                "price": float(row["price"]),
                "gross_amount": float(row["gross_amount"]),
                "state": row["state"].strip().upper(),
            })

    return transactions


def parse_statement(path):
    transactions = []

    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            transactions.append({
                "external_id": row["reference"],
                "traded_at": parse_datetime(row["executed_at"]),
                "instrument": row["symbol"],
                "side": normalize_side(row["direction"]),
                "quantity": float(row["qty"]),
                "price": float(row["unit_price"]),
                "gross_amount": float(row["total"]),
                "state": row["status"].strip().upper(),
            })

    return transactions


def normalize_side(side):
    mapping = {
        "BUY": "BUY",
        "B": "BUY",
        "SELL": "SELL",
        "S": "SELL",
    }

    return mapping.get(
        side.strip().upper(),
        side.strip().upper()
    )


def parse_datetime(value):
    value = value.strip()

    # Handle ISO format with Z
    if value.endswith("Z"):
        value = value[:-1]

    # Try ISO format first
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    # Handle other common formats
    formats = [
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y %I:%M:%S %p",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Unsupported datetime format: '{value}'"
    )