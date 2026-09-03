# Transaction Reconciliation

A Flask-based transaction reconciliation application that compares transaction records from two systems, identifies matches and mismatches, and allows users to manually resolve unmatched transactions.

## Features

- Upload ledger and statement CSV files
- Normalize different field names and values
- Automatically match transactions
- Handle small differences using configurable tolerances
- Detect unmatched transactions from either system
- Show detailed field-level differences
- Suggest possible manual matches
- Manually resolve unmatched transactions
- Track reconciliation runs in SQLite
- Detect duplicate file uploads using SHA-256 hashes
- Create a new reconciliation run when corrected files are uploaded
- Preserve previous reconciliation runs
- Ignore cancelled transactions
- Automated tests using pytest

## Technology Stack

- Python 3.11
- Flask
- Flask-SQLAlchemy
- SQLite
- Jinja2
- HTML/CSS
- pytest

## Project Structure

```text
transaction-reconciliation/
│
├── app.py
├── models/
│   └── models.py
│
├── reconciliation/
│   ├── comparison.py
│   ├── matching.py
│   └── parser.py
│
├── routes/
│   └── reconciliation_routes.py
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── results.html
│   └── detail.html
│
├── tests/
│   ├── test_parser.py
│   ├── test_reconciliation.py
│   └── test_routes.py
│
├── data/
│   ├── ledger.csv
│   └── statement.csv
│
├── requirements.txt
└── README.md