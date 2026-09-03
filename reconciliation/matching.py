from .comparison import (
    compare_transactions,
    is_candidate_match,
)


def reconcile(ledger_transactions, statement_transactions):
    results = []

    matched_statement_ids = set()

    active_ledger = [
        tx
        for tx in ledger_transactions
        if tx["state"] != "CANCELLED"
    ]

    active_statement = [
        tx
        for tx in statement_transactions
        if tx["state"] != "CANCELLED"
    ]

    for ledger in active_ledger:
        statement = next(
            (
                tx for tx in active_statement
                if tx["external_id"] == ledger["external_id"]
                and id(tx) not in matched_statement_ids
            ),
            None,
        )

        match_type = "EXACT_ID"

        if statement is None:
            statement = next(
                (
                    tx for tx in active_statement
                    if id(tx) not in matched_statement_ids
                    and is_candidate_match(ledger, tx)
                ),
                None,
            )
            match_type = "CANDIDATE"

        if statement is None:
            results.append({
                "status": "UNMATCHED_LEDGER",
                "ledger": ledger,
                "statement": None,
                "differences": {},
                "match_type": None,
            })
            continue

        matched_statement_ids.add(id(statement))

        differences = compare_transactions(
            ledger,
            statement,
        )

        if differences:
            status = "MISMATCH"
        else:
            status = "MATCHED"

        results.append({
            "status": status,
            "ledger": ledger,
            "statement": statement,
            "differences": differences,
            "match_type": match_type,
        })

    for statement in active_statement:
        if id(statement) not in matched_statement_ids:
            results.append({
                "status": "UNMATCHED_STATEMENT",
                "ledger": None,
                "statement": statement,
                "differences": {},
                "match_type": None,
            })

    return results