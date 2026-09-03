from datetime import timedelta


AMOUNT_TOLERANCE = 5.00
TIME_TOLERANCE = timedelta(minutes=30)
QUANTITY_TOLERANCE = 0.0001


def compare_transactions(ledger, statement):
    differences = {}

    if ledger["instrument"] != statement["instrument"]:
        differences["instrument"] = {
            "ledger": ledger["instrument"],
            "statement": statement["instrument"],
        }

    if ledger["side"] != statement["side"]:
        differences["side"] = {
            "ledger": ledger["side"],
            "statement": statement["side"],
        }

    quantity_difference = abs(
        ledger["quantity"] - statement["quantity"]
    )

    if quantity_difference > QUANTITY_TOLERANCE:
        differences["quantity"] = {
            "ledger": ledger["quantity"],
            "statement": statement["quantity"],
            "difference": quantity_difference,
        }

    amount_difference = abs(
        ledger["gross_amount"] - statement["gross_amount"]
    )

    if amount_difference > AMOUNT_TOLERANCE:
        differences["amount"] = {
            "ledger": ledger["gross_amount"],
            "statement": statement["gross_amount"],
            "difference": amount_difference,
        }

    time_difference = abs(
        ledger["traded_at"] - statement["traded_at"]
    )

    if time_difference > TIME_TOLERANCE:
        differences["time"] = {
            "ledger": ledger["traded_at"].isoformat(),
            "statement": statement["traded_at"].isoformat(),
            "difference_seconds": time_difference.total_seconds(),
        }

    return differences


def is_candidate_match(ledger, statement):
    if ledger["instrument"] != statement["instrument"]:
        return False

    if ledger["side"] != statement["side"]:
        return False

    if abs(
        ledger["quantity"] - statement["quantity"]
    ) > QUANTITY_TOLERANCE:
        return False

    time_difference = abs(
        ledger["traded_at"] - statement["traded_at"]
    )

    return time_difference <= TIME_TOLERANCE