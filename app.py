from flask import Flask, render_template

from models.models import (
    db,
    ReconciliationRun,
    ReconciliationResult,
)

from routes.reconciliation_routes import reconciliation_bp


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reconciliation.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(reconciliation_bp)

    @app.route("/")
    def home():

        latest_run = ReconciliationRun.query.order_by(
            ReconciliationRun.id.desc()
        ).first()

        recent_runs = ReconciliationRun.query.order_by(
            ReconciliationRun.id.desc()
        ).limit(5).all()

        stats = {
            "total": 0,
            "matched": 0,
            "mismatch": 0,
            "unmatched": 0,
            "manual": 0,
        }

        if latest_run:

            results = ReconciliationResult.query.filter_by(
                run_id=latest_run.id
            ).all()

            stats["total"] = len(results)

            stats["matched"] = sum(
                1
                for result in results
                if result.status == "MATCHED"
            )

            stats["mismatch"] = sum(
                1
                for result in results
                if result.status == "MISMATCH"
            )

            stats["unmatched"] = sum(
                1
                for result in results
                if result.status in [
                    "UNMATCHED_LEDGER",
                    "UNMATCHED_STATEMENT",
                ]
            )

            stats["manual"] = sum(
                1
                for result in results
                if result.status == "MANUALLY_MATCHED"
            )

        return render_template(
            "dashboard.html",
            latest_run=latest_run,
            recent_runs=recent_runs,
            stats=stats,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)