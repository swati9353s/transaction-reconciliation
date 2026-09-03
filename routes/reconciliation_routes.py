from datetime import datetime
import hashlib

from flask import (
    Blueprint,
    redirect,
    url_for,
    render_template,
)

from models.models import (
    db,
    ReconciliationRun,
    Transaction,
    ReconciliationResult,
    FileImport,
)

from reconciliation.parser import (
    parse_ledger,
    parse_statement,
)

from reconciliation.matching import reconcile
from reconciliation.comparison import compare_transactions


reconciliation_bp = Blueprint(
    "reconciliation",
    __name__,
)


# =========================================================
# FILE HASHING
# =========================================================

def calculate_file_hash(path):
    """
    Calculate SHA-256 hash for a file.

    The hash allows us to identify whether a file is exactly
    the same as a previously processed file.
    """

    sha256 = hashlib.sha256()

    with open(path, "rb") as file:

        for chunk in iter(
            lambda: file.read(4096),
            b"",
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


# =========================================================
# START A NEW RECONCILIATION RUN
# =========================================================

@reconciliation_bp.route("/run")
def run_reconciliation():

    ledger_path = "data/ledger.csv"
    statement_path = "data/statement.csv"

    # -----------------------------------------------------
    # Calculate file hashes
    # -----------------------------------------------------

    ledger_hash = calculate_file_hash(
        ledger_path
    )

    statement_hash = calculate_file_hash(
        statement_path
    )

    # -----------------------------------------------------
    # Check whether these exact files were already
    # processed together in a previous run.
    # -----------------------------------------------------

    previous_ledger_import = (
        FileImport.query
        .filter_by(
            file_hash=ledger_hash,
            file_type="LEDGER",
        )
        .order_by(FileImport.id.desc())
        .first()
    )

    previous_statement_import = (
        FileImport.query
        .filter_by(
            file_hash=statement_hash,
            file_type="STATEMENT",
        )
        .order_by(FileImport.id.desc())
        .first()
    )

    # -----------------------------------------------------
    # Exact duplicate
    # -----------------------------------------------------

    if (
        previous_ledger_import
        and previous_statement_import
        and previous_ledger_import.run_id
        == previous_statement_import.run_id
    ):

        return redirect(
            url_for(
                "reconciliation.results",
                run_id=previous_ledger_import.run_id,
            )
        )

    # -----------------------------------------------------
    # Create a new reconciliation run.
    #
    # If a file was corrected, its hash will be different,
    # so a new run is created while previous history remains.
    # -----------------------------------------------------

    run = ReconciliationRun(
        ledger_file=ledger_path,
        statement_file=statement_path,
    )

    db.session.add(run)
    db.session.commit()

    # -----------------------------------------------------
    # Record file imports
    # -----------------------------------------------------

    ledger_import = FileImport(
        run_id=run.id,
        filename=ledger_path,
        file_hash=ledger_hash,
        file_type="LEDGER",
    )

    statement_import = FileImport(
        run_id=run.id,
        filename=statement_path,
        file_hash=statement_hash,
        file_type="STATEMENT",
    )

    db.session.add(ledger_import)
    db.session.add(statement_import)

    db.session.commit()

    # -----------------------------------------------------
    # Parse input files
    # -----------------------------------------------------

    ledger_transactions = parse_ledger(
        ledger_path
    )

    statement_transactions = parse_statement(
        statement_path
    )

    # -----------------------------------------------------
    # Store ledger transactions
    # -----------------------------------------------------

    ledger_db_transactions = []

    for tx in ledger_transactions:

        db_tx = Transaction(
            run_id=run.id,
            source="LEDGER",
            external_id=tx["external_id"],
            traded_at=tx["traded_at"],
            instrument=tx["instrument"],
            side=tx["side"],
            quantity=tx["quantity"],
            price=tx["price"],
            gross_amount=tx["gross_amount"],
            state=tx["state"],
        )

        db.session.add(db_tx)

        ledger_db_transactions.append(
            db_tx
        )

    # -----------------------------------------------------
    # Store statement transactions
    # -----------------------------------------------------

    statement_db_transactions = []

    for tx in statement_transactions:

        db_tx = Transaction(
            run_id=run.id,
            source="STATEMENT",
            external_id=tx["external_id"],
            traded_at=tx["traded_at"],
            instrument=tx["instrument"],
            side=tx["side"],
            quantity=tx["quantity"],
            price=tx["price"],
            gross_amount=tx["gross_amount"],
            state=tx["state"],
        )

        db.session.add(db_tx)

        statement_db_transactions.append(
            db_tx
        )

    db.session.commit()

    # -----------------------------------------------------
    # Run automatic reconciliation
    # -----------------------------------------------------

    results = reconcile(
        ledger_transactions,
        statement_transactions,
    )

    # -----------------------------------------------------
    # Save reconciliation results
    # -----------------------------------------------------

    for result in results:

        ledger_tx_id = None
        statement_tx_id = None

        # -------------------------------------------------
        # Find corresponding DB ledger transaction
        # -------------------------------------------------

        if result["ledger"] is not None:

            for db_tx in ledger_db_transactions:

                if (
                    db_tx.external_id
                    == result["ledger"]["external_id"]
                ):
                    ledger_tx_id = db_tx.id
                    break

        # -------------------------------------------------
        # Find corresponding DB statement transaction
        # -------------------------------------------------

        if result["statement"] is not None:

            for db_tx in statement_db_transactions:

                if (
                    db_tx.external_id
                    == result["statement"]["external_id"]
                ):
                    statement_tx_id = db_tx.id
                    break

        db_result = ReconciliationResult(
            run_id=run.id,
            ledger_transaction_id=ledger_tx_id,
            statement_transaction_id=statement_tx_id,
            status=result["status"],
            match_type=result["match_type"],
            differences=str(
                result["differences"]
            ),
            resolution_status="UNRESOLVED",
        )

        db.session.add(db_result)

    db.session.commit()

    # -----------------------------------------------------
    # Show results
    # -----------------------------------------------------

    return redirect(
        url_for(
            "reconciliation.results",
            run_id=run.id,
        )
    )


# =========================================================
# RESULTS PAGE
# =========================================================

@reconciliation_bp.route(
    "/results/<int:run_id>"
)
def results(run_id):

    run = ReconciliationRun.query.get_or_404(
        run_id
    )

    results = (
        ReconciliationResult.query
        .filter_by(run_id=run_id)
        .order_by(ReconciliationResult.id)
        .all()
    )

    return render_template(
        "results.html",
        run=run,
        results=results,
    )


# =========================================================
# RESULT DETAIL PAGE
# =========================================================

@reconciliation_bp.route(
    "/result/<int:result_id>"
)
def detail(result_id):

    result = ReconciliationResult.query.get_or_404(
        result_id
    )

    ledger = None
    statement = None

    # -----------------------------------------------------
    # Load ledger transaction
    # -----------------------------------------------------

    if result.ledger_transaction_id:

        ledger = Transaction.query.get(
            result.ledger_transaction_id
        )

    # -----------------------------------------------------
    # Load statement transaction
    # -----------------------------------------------------

    if result.statement_transaction_id:

        statement = Transaction.query.get(
            result.statement_transaction_id
        )

    candidates = []

    # =====================================================
    # UNMATCHED LEDGER
    # =====================================================

    if (
        result.status == "UNMATCHED_LEDGER"
        and ledger
    ):

        all_candidates = (
            Transaction.query
            .filter(
                Transaction.run_id
                == result.run_id,
                Transaction.source
                == "STATEMENT",
                Transaction.state
                != "CANCELLED",
            )
            .all()
        )

        for candidate in all_candidates:

            time_difference = abs(
                (
                    candidate.traded_at
                    - ledger.traded_at
                ).total_seconds()
            )

            if (
                candidate.instrument
                == ledger.instrument
                and candidate.side
                == ledger.side
                and time_difference
                <= 30 * 60
            ):
                candidates.append(
                    candidate
                )

    # =====================================================
    # UNMATCHED STATEMENT
    # =====================================================

    elif (
        result.status
        == "UNMATCHED_STATEMENT"
        and statement
    ):

        all_candidates = (
            Transaction.query
            .filter(
                Transaction.run_id
                == result.run_id,
                Transaction.source
                == "LEDGER",
                Transaction.state
                != "CANCELLED",
            )
            .all()
        )

        for candidate in all_candidates:

            time_difference = abs(
                (
                    candidate.traded_at
                    - statement.traded_at
                ).total_seconds()
            )

            if (
                candidate.instrument
                == statement.instrument
                and candidate.side
                == statement.side
                and time_difference
                <= 30 * 60
            ):
                candidates.append(
                    candidate
                )

    # -----------------------------------------------------
    # Render detail page
    # -----------------------------------------------------

    return render_template(
        "detail.html",
        result=result,
        ledger=ledger,
        statement=statement,
        candidates=candidates,
    )


# =========================================================
# MANUAL MATCH
# =========================================================

@reconciliation_bp.route(
    "/result/<int:result_id>/match/<int:transaction_id>",
    methods=["POST"],
)
def manual_match(
    result_id,
    transaction_id,
):

    result = ReconciliationResult.query.get_or_404(
        result_id
    )

    selected_transaction = (
        Transaction.query.get_or_404(
            transaction_id
        )
    )

    # -----------------------------------------------------
    # Validate same reconciliation run
    # -----------------------------------------------------

    if (
        selected_transaction.run_id
        != result.run_id
    ):

        return "Invalid transaction", 400

    # -----------------------------------------------------
    # Cancelled transactions cannot be matched
    # -----------------------------------------------------

    if (
        selected_transaction.state
        == "CANCELLED"
    ):

        return (
            "Cannot match a cancelled transaction",
            400,
        )

    # =====================================================
    # UNMATCHED LEDGER
    # =====================================================

    if result.status == "UNMATCHED_LEDGER":

        Transaction.query.get_or_404(
            result.ledger_transaction_id
        )

        if (
            selected_transaction.source
            != "STATEMENT"
        ):

            return (
                "Invalid statement transaction",
                400,
            )

        result.statement_transaction_id = (
            selected_transaction.id
        )

    # =====================================================
    # UNMATCHED STATEMENT
    # =====================================================

    elif result.status == "UNMATCHED_STATEMENT":

        Transaction.query.get_or_404(
            result.statement_transaction_id
        )

        if (
            selected_transaction.source
            != "LEDGER"
        ):

            return (
                "Invalid ledger transaction",
                400,
            )

        result.ledger_transaction_id = (
            selected_transaction.id
        )

    else:

        return (
            "Only unmatched transactions can be "
            "manually matched",
            400,
        )

    # -----------------------------------------------------
    # Load both transactions
    # -----------------------------------------------------

    ledger = Transaction.query.get(
        result.ledger_transaction_id
    )

    statement = Transaction.query.get(
        result.statement_transaction_id
    )

    # -----------------------------------------------------
    # Convert DB objects to dictionaries
    # -----------------------------------------------------

    ledger_data = {
        "external_id": ledger.external_id,
        "traded_at": ledger.traded_at,
        "instrument": ledger.instrument,
        "side": ledger.side,
        "quantity": ledger.quantity,
        "price": ledger.price,
        "gross_amount": ledger.gross_amount,
        "state": ledger.state,
    }

    statement_data = {
        "external_id": statement.external_id,
        "traded_at": statement.traded_at,
        "instrument": statement.instrument,
        "side": statement.side,
        "quantity": statement.quantity,
        "price": statement.price,
        "gross_amount": statement.gross_amount,
        "state": statement.state,
    }

    # -----------------------------------------------------
    # Compare manually matched transactions
    # -----------------------------------------------------

    differences = compare_transactions(
        ledger_data,
        statement_data,
    )

    # -----------------------------------------------------
    # Store manual resolution
    # -----------------------------------------------------

    result.status = "MANUALLY_MATCHED"

    result.match_type = "MANUAL"

    result.differences = str(
        differences
    )

    result.resolution_status = "RESOLVED"

    result.resolved_at = datetime.utcnow()

    db.session.commit()

    # -----------------------------------------------------
    # Show updated result
    # -----------------------------------------------------

    return redirect(
        url_for(
            "reconciliation.detail",
            result_id=result.id,
        )
    )