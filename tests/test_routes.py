import io

from app import create_app
from models.models import db, ReconciliationRun


def test_duplicate_files_do_not_create_new_run(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": (
            "sqlite:///" + str(tmp_path / "test.db")
        ),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
    })

    with app.app_context():
        db.drop_all()
        db.create_all()

    client = app.test_client()

    ledger_csv = """trade_id,traded_at,instrument,side,quantity,price,gross_amount,state
T-1,2025-01-01T10:00:00Z,BTC-USD,BUY,1,100,100,SETTLED
"""

    statement_csv = """reference,executed_at,symbol,direction,qty,unit_price,total,status
T-1,2025-01-01 10:00:00,BTC-USD,B,1,100,100,SETTLED
"""

    response = client.post(
        "/run",
        data={
            "ledger_file": (
                io.BytesIO(ledger_csv.encode()),
                "ledger.csv",
            ),
            "statement_file": (
                io.BytesIO(statement_csv.encode()),
                "statement.csv",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302

    with app.app_context():
        assert ReconciliationRun.query.count() == 1

    response = client.post(
        "/run",
        data={
            "ledger_file": (
                io.BytesIO(ledger_csv.encode()),
                "ledger.csv",
            ),
            "statement_file": (
                io.BytesIO(statement_csv.encode()),
                "statement.csv",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302

    with app.app_context():
        assert ReconciliationRun.query.count() == 1

def test_corrected_file_creates_new_run(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": (
            "sqlite:///" + str(tmp_path / "test.db")
        ),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
    })

    with app.app_context():
        db.drop_all()
        db.create_all()

    client = app.test_client()

    ledger_csv = """trade_id,traded_at,instrument,side,quantity,price,gross_amount,state
T-1,2025-01-01T10:00:00Z,BTC-USD,BUY,1,100,100,SETTLED
"""

    statement_csv = """reference,executed_at,symbol,direction,qty,unit_price,total,status
T-1,2025-01-01 10:00:00,BTC-USD,B,1,100,100,SETTLED
"""

    # First upload
    response = client.post(
        "/run",
        data={
            "ledger_file": (
                io.BytesIO(ledger_csv.encode()),
                "ledger.csv",
            ),
            "statement_file": (
                io.BytesIO(statement_csv.encode()),
                "statement.csv",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302

    with app.app_context():
        assert ReconciliationRun.query.count() == 1

    # Correct the ledger
    corrected_ledger_csv = """trade_id,traded_at,instrument,side,quantity,price,gross_amount,state
T-1,2025-01-01T10:00:00Z,BTC-USD,BUY,1,110,110,SETTLED
"""

    # Upload corrected ledger
    response = client.post(
        "/run",
        data={
            "ledger_file": (
                io.BytesIO(corrected_ledger_csv.encode()),
                "ledger.csv",
            ),
            "statement_file": (
                io.BytesIO(statement_csv.encode()),
                "statement.csv",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302

    with app.app_context():
        assert ReconciliationRun.query.count() == 2