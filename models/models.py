from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ReconciliationRun(db.Model):
    __tablename__ = "reconciliation_runs"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ledger_file = db.Column(db.String(255))
    statement_file = db.Column(db.String(255))


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)

    run_id = db.Column(
        db.Integer,
        db.ForeignKey("reconciliation_runs.id"),
        nullable=False
    )

    source = db.Column(db.String(20), nullable=False)
    external_id = db.Column(db.String(100), nullable=False)

    traded_at = db.Column(db.DateTime, nullable=False)
    instrument = db.Column(db.String(50), nullable=False)
    side = db.Column(db.String(10), nullable=False)

    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    gross_amount = db.Column(db.Float, nullable=False)

    state = db.Column(db.String(30), nullable=False)


class ReconciliationResult(db.Model):
    __tablename__ = "reconciliation_results"

    id = db.Column(db.Integer, primary_key=True)

    run_id = db.Column(
        db.Integer,
        db.ForeignKey("reconciliation_runs.id"),
        nullable=False
    )

    ledger_transaction_id = db.Column(
        db.Integer,
        db.ForeignKey("transactions.id"),
        nullable=True
    )

    statement_transaction_id = db.Column(
        db.Integer,
        db.ForeignKey("transactions.id"),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False
    )

    match_type = db.Column(
        db.String(30)
    )

    differences = db.Column(
        db.Text
    )

    resolution_status = db.Column(
        db.String(30),
        default="UNRESOLVED"
    )

    resolved_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class FileImport(db.Model):
    __tablename__ = "file_imports"

    id = db.Column(db.Integer, primary_key=True)

    run_id = db.Column(
        db.Integer,
        db.ForeignKey("reconciliation_runs.id"),
        nullable=False
    )

    filename = db.Column(db.String(255), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)
    file_type = db.Column(db.String(30), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )