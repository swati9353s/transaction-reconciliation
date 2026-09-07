# Transaction Reconciliation

## Overview

Transaction Reconciliation is a Flask-based application that compares
transaction data from two different systems and identifies matching,
mismatching, and unmatched transactions.

The two systems may represent the same transaction using different column
names, date formats, and value formats. The application normalizes both
sources into a common transaction structure before performing reconciliation.

The application supports:

- Parsing ledger and statement CSV files
- Normalizing different source formats
- Matching transactions using transaction IDs
- Candidate matching for unmatched transactions
- Comparing transaction fields
- Amount and time tolerances
- Detecting unmatched transactions from both systems
- Detecting duplicate files
- Processing corrected files as new reconciliation runs
- Keeping previous reconciliation runs available
- Manual transaction matching
- Persistent resolution status
- Dashboard with reconciliation statistics
- Detailed transaction comparison
- Automated tests for reconciliation logic

---

## How to Run

### Prerequisites

- Python 3.x
- pip

### 1. Clone the repository

```bash
git clone https://github.com/swati9353s/transaction-reconciliation.git
cd transaction-reconciliation
```

### 2. Create a virtual environment

On Windows:

```bash
python -m venv venv
```

Activate the virtual environment:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

Open the URL in a browser.

### 5. Run tests

```bash
python -m pytest
```

The test suite covers parser logic, transaction comparison, matching
behaviour, route behaviour, and duplicate file handling.

---

## Input Files

The application currently uses two CSV files:

```text
data/ledger.csv
data/statement.csv
```

The two files can have different column names but represent the same
transaction information.

For example, the ledger may use:

```text
trade_id
executed_at
symbol
direction
qty
unit_price
total
status
```

while the statement may use:

```text
reference
executed_at
symbol
direction
qty
unit_price
total
status
```

The parser converts both formats into a common transaction representation.

---

# Architecture

The application is divided into separate components so that the core
reconciliation logic remains independent from the web interface and database.

```text
                    Ledger CSV
                        |
                        v
                  +-----------+
                  |   Parser  |
                  +-----------+
                        |
                        v
              Normalized Transactions
                        ^
                        |
                  +-----------+
                  |   Parser  |
                  +-----------+
                        ^
                        |
                  Statement CSV

                        |
                        v
                 +-------------+
                 |   Matching  |
                 +-------------+
                        |
                        v
                 +-------------+
                 | Comparison  |
                 +-------------+
                        |
                        v
              Reconciliation Results
                        |
                        v
                   +--------+
                   | SQLite |
                   +--------+
                        |
                        v
                     Web UI
```

### `app.py`

Responsible for:

- Creating the Flask application
- Configuring the database
- Initializing SQLAlchemy
- Creating database tables
- Registering reconciliation routes
- Rendering the dashboard
- Displaying reconciliation statistics

### `routes/reconciliation_routes.py`

Responsible for:

- Starting reconciliation runs
- Calculating file hashes
- Detecting duplicate files
- Parsing input files
- Saving transactions
- Running reconciliation
- Saving reconciliation results
- Displaying reconciliation results
- Displaying transaction details
- Handling manual matching

### `reconciliation/parser.py`

Responsible for parsing the ledger and statement files and converting them
into a common transaction format.

This keeps source-specific column names separate from the reconciliation
logic.

### `reconciliation/matching.py`

Responsible for identifying transactions that correspond to each other.

It performs automatic matching and identifies candidates for transactions
that could not be matched directly.

### `reconciliation/comparison.py`

Responsible for comparing two transactions after they have been matched.

The comparison logic is independent of Flask and the database, which makes it
easy to unit test.

### `models/models.py`

Contains the SQLAlchemy models used to persist:

- Reconciliation runs
- Transactions
- Reconciliation results
- Imported file information

---

# Matching Strategy

The reconciliation process follows multiple stages.

## 1. Normalize the Input

The ledger and statement may have different column names and formats.

Both files are converted into a common structure containing fields such as:

- External transaction ID
- Trade timestamp
- Instrument
- Side
- Quantity
- Price
- Gross amount
- State

This allows the matching and comparison logic to work independently of the
original file format.

---

## 2. Match Exact IDs

The first matching strategy is to match transactions using their transaction
IDs.

For example:

```text
Ledger:
trade_id = T-1001

Statement:
reference = T-1001
```

These transactions can be directly matched.

Exact ID matching is preferred because it provides the strongest indication
that both records represent the same transaction.

---

## 3. Identify Unmatched Transactions

Transactions that cannot be matched automatically are classified as:

```text
UNMATCHED_LEDGER
```

or:

```text
UNMATCHED_STATEMENT
```

Both directions are checked so that transactions missing from either system
are detected.

---

## 4. Candidate Matching

For unmatched transactions, the application identifies possible candidates
using additional transaction attributes.

Candidate matching considers:

- Opposite source
- Same instrument
- Same side
- Trade time within the configured tolerance
- Transaction is not cancelled

These candidates are displayed on the transaction detail page.

---

## 5. Manual Matching

If automatic matching cannot determine the correct transaction, the user can
review the candidates and manually select the appropriate transaction.

The manual decision is stored in the database and the reconciliation result
is marked as resolved.

---

# Comparison Strategy

After two transactions are matched, their fields are compared.

The comparison checks important transaction attributes including:

- Quantity
- Price
- Gross amount
- Trade time
- Instrument
- Side
- State

For example:

```text
Ledger:
Quantity     = 10
Price        = 100
Gross Amount = 1000

Statement:
Quantity     = 10
Price        = 100
Gross Amount = 1004
```

The amount difference is:

```text
1004 - 1000 = 4
```

Since the difference is within the configured tolerance, it is not treated as
a significant mismatch.

However:

```text
Ledger amount     = 1000
Statement amount  = 1200
```

would result in an amount difference being reported.

---

# Tolerances

The application uses tolerances because small differences between systems
can occur due to rounding, fees, processing delays, or clock differences.

## Amount Tolerance

```text
± $5
```

An amount difference of up to $5 is considered acceptable.

A difference greater than $5 is reported as a mismatch.

### Example

```text
Ledger amount:      $100
Statement amount:   $104
Difference:           $4
```

This is within tolerance.

```text
Ledger amount:      $100
Statement amount:   $120
Difference:          $20
```

This is outside tolerance and is reported as a difference.

---

## Time Tolerance

```text
± 30 minutes
```

The time tolerance is used when identifying possible candidate transactions.

For example:

```text
Ledger:     10:00
Statement:  10:20
```

These transactions can be considered candidates because they are within
30 minutes.

Transactions with a larger time difference are not considered candidates by
this rule.

---

# Why These Tolerances?

The tolerances were selected as practical values for the sample
reconciliation data.

Small differences between systems are expected in real reconciliation
scenarios because of:

- Rounding
- Fees
- Different processing times
- Clock differences

The purpose of the tolerance is to avoid treating every small difference as
an operational issue.

In a production system, these values should ideally be configurable based on
business requirements, transaction type, currency, and source system.

---

# Reconciliation Statuses

The application uses the following statuses.

## `MATCHED`

The transaction was automatically matched and no significant differences were
found.

## `MISMATCH`

A corresponding transaction was found, but one or more fields differ beyond
the configured tolerance.

## `UNMATCHED_LEDGER`

A transaction exists in the ledger but no corresponding statement transaction
could be found.

## `UNMATCHED_STATEMENT`

A transaction exists in the statement but no corresponding ledger transaction
could be found.

## `MANUALLY_MATCHED`

The transaction was manually matched by the user after reviewing possible
candidates.

---

# Resolution Status

Reconciliation results also maintain a resolution status.

Possible values are:

```text
UNRESOLVED
RESOLVED
```

A transaction that requires investigation remains unresolved until a manual
decision is made.

When a user manually matches a transaction, the application stores:

```text
status = MANUALLY_MATCHED
match_type = MANUAL
resolution_status = RESOLVED
```

The resolution timestamp is also stored.

---

# Database Design

The application uses four main database models.

## `ReconciliationRun`

Represents one execution of the reconciliation process.

It stores:

- Run ID
- Creation timestamp
- Ledger file name
- Statement file name

---

## `Transaction`

Stores normalized transactions from either source.

Important fields include:

- Run ID
- Source
- External transaction ID
- Trade timestamp
- Instrument
- Side
- Quantity
- Price
- Gross amount
- State

---

## `ReconciliationResult`

Stores the result of comparing transactions.

It contains:

- Run ID
- Ledger transaction ID
- Statement transaction ID
- Status
- Match type
- Differences
- Resolution status
- Resolution timestamp
- Creation timestamp

---

## `FileImport`

Stores information about imported files.

It contains:

- Run ID
- Filename
- SHA-256 file hash
- File type
- Creation timestamp

---

# Why SQLite?

SQLite was selected because this project is an MVP and is intended to be easy
to run locally.

Advantages include:

- No separate database server is required
- Very simple setup
- Lightweight
- Easy to test
- Suitable for the sample dataset
- Works well with SQLAlchemy

For a production reconciliation system with multiple users and larger
transaction volumes, PostgreSQL would be a better choice.

---

# Why Flask?

Flask was selected because it is lightweight and provides everything required
for this MVP.

Benefits include:

- Simple application structure
- Easy route handling
- Easy integration with SQLAlchemy
- Minimal configuration
- Allows the reconciliation logic to remain independent from the web layer

A larger framework was not necessary for the scope of this assignment.

---

# Duplicate Files

Duplicate files can arrive during daily processing.

To prevent identical files from creating unnecessary reconciliation runs, the
application calculates a SHA-256 hash for each input file.

For example:

```text
ledger.csv
    |
    v
SHA-256
    |
    v
File Hash
```

The hash is stored in the `FileImport` table.

When the same ledger and statement files are processed again, their hashes are
compared with previously imported files.

If both files have already been processed together, the existing
reconciliation run is reused instead of creating another run.

This makes the process idempotent for identical input files.

---

# Corrections

A corrected file is treated differently from an exact duplicate.

The application identifies files using their content hash.

For example:

```text
Original file
     |
     v
Hash A

Corrected file
     |
     v
Hash B
```

If the file content changes, its SHA-256 hash also changes.

Therefore, the corrected file creates a new reconciliation run.

The previous run is not deleted.

For example:

```text
Run #1
Original data

Run #2
Corrected data
```

This allows previous reconciliation results to remain discoverable while the
latest run represents the latest imported values.

The design therefore avoids overwriting historical reconciliation runs.

---

# Manual Resolution

Automatic matching may not always be able to determine the correct
transaction.

For an unmatched transaction, the user can open the transaction detail page.

The application searches for possible candidates based on:

- Opposite source
- Same instrument
- Same side
- Timestamp within 30 minutes
- Candidate is not cancelled

The candidates are displayed to the user.

The user can select:

```text
Match This Transaction
```

The application then:

1. Validates the selected transaction.
2. Ensures it belongs to the same reconciliation run.
3. Ensures it is from the opposite source.
4. Rejects cancelled transactions.
5. Associates the two transactions.
6. Re-runs the comparison.
7. Marks the result as manually matched.
8. Marks the resolution as resolved.
9. Stores the resolution timestamp.

This manual decision persists in the database.

---

# Cancelled Transactions

Cancelled transactions are not considered valid candidates for manual
matching.

This prevents a cancelled transaction from being incorrectly selected as the
counterpart of an unmatched transaction.

---

# Reconciliation Runs and History

Each reconciliation run is stored separately.

For example:

```text
Run #1
├── Original ledger
├── Original statement
└── Original reconciliation results

Run #2
├── Corrected ledger
├── Corrected statement
└── New reconciliation results
```

Previous runs remain available instead of being overwritten.

This provides historical visibility when corrected source files are received.

---

# User Interface

The application provides three main views.

## Dashboard

The dashboard displays:

- Latest reconciliation run
- Total results
- Matched transactions
- Mismatched transactions
- Unmatched transactions
- Manually resolved transactions
- Recent reconciliation runs
- Option to start a new reconciliation run

---

## Results Page

The results page displays the reconciliation results for a selected run.

It shows:

- Result ID
- Status
- Match type
- Differences
- Resolution status
- Action to inspect the result

Users can open an individual result to view more details.

---

## Transaction Detail Page

The transaction detail page displays the ledger and statement transaction
side by side.

The fields include:

- External ID
- Instrument
- Side
- Quantity
- Price
- Gross amount
- Trade time
- State

For unmatched transactions, possible manual candidates are also displayed.

---

# Testing

The project uses `pytest` for automated testing.

The tests are designed to verify the core reconciliation behaviour
independently from the browser.

## Parser Tests

Parser tests verify that the input CSV files are correctly converted into the
normalized transaction structure.

## Comparison Tests

Comparison tests cover:

- Exact matches
- Small amount differences
- Large amount differences
- Time tolerance
- Quantity differences

## Route Tests

Route tests cover application-level behaviour including duplicate file
handling.

## Running Tests

Run:

```bash
python -m pytest
```

The current test suite contains 11 tests.

Expected result:

```text
11 passed
```

---

# What Is Not Implemented

The following features are intentionally outside the current MVP.

## 1. Browser File Upload

The current implementation processes:

```text
data/ledger.csv
data/statement.csv
```

A future version would provide a browser interface where users can upload
ledger and statement files directly.

---

## 2. Authentication and Authorization

The application does not currently include:

- Login
- User accounts
- Roles
- Permissions
- Access control

A production application would require appropriate authentication and
authorization.

---

## 3. Scheduled Daily Runs

The current MVP starts reconciliation through the application.

Automated daily reconciliation using a scheduler or background worker is not
implemented.

---

## 4. Advanced Audit History

The application stores reconciliation runs and manual resolution timestamps,
but it does not currently maintain a complete event-by-event audit trail.

A production system should record information such as:

- User who made the change
- Previous value
- New value
- Time of change
- Reason for change
- Previous transaction association
- New transaction association

---

## 5. Advanced Candidate Scoring

Candidate matching currently uses filtering rules.

It does not yet provide a sophisticated weighted scoring system when multiple
possible candidates are found.

---

## 6. Multiple Third-Party Source Adapters

The current implementation focuses on the provided ledger and statement
formats.

Additional source formats would require additional parser/adapter logic.

---

## 7. Production Database

SQLite is used for the MVP.

A production deployment would use PostgreSQL or another production-grade
database.

---

## 8. Large-Scale Processing

The current implementation is designed for a small reconciliation dataset.

For very large files, additional optimizations would be required, such as:

- Streaming file processing
- Batch database inserts
- Database indexes
- Pagination
- Background processing
- Memory optimization

---

# What I Would Build Next

## 1. Better Candidate Scoring

Instead of only filtering candidates, I would introduce a scoring mechanism.

For example:

```text
Same transaction ID       High weight
Same instrument           High weight
Same side                 Medium weight
Similar quantity          Medium weight
Similar amount            Medium weight
Closest timestamp         Medium weight
```

Candidates could then be ranked from most likely to least likely.

This would make manual reconciliation faster when multiple candidates exist.

---

## 2. Complete Audit History

I would introduce a dedicated audit table that records every manual
resolution.

For example:

```text
Audit Record
------------
User
Action
Old Status
New Status
Old Transaction
New Transaction
Timestamp
Reason
```

This would make the system more suitable for financial operations where every
manual decision needs to be traceable.

---

## 3. Scheduled Runs

The reconciliation process could be automated to run every day.

A possible architecture would be:

```text
Scheduler
    |
    v
Background Worker
    |
    v
File Import
    |
    v
Reconciliation Engine
    |
    v
Database
    |
    v
Notification / Reporting
```

This would remove the need for manual execution of the reconciliation
process.

---

## 4. Third-Party Format Adapters

I would introduce an adapter-based architecture for supporting additional
source systems.

For example:

```text
Source A Adapter
Source B Adapter
Source C Adapter
       |
       v
Normalized Transaction
       |
       v
Reconciliation Engine
```

This would allow new file formats to be added without changing the core
matching and comparison logic.

---

## 5. PostgreSQL

For production use, I would migrate from SQLite to PostgreSQL.

This would provide better support for:

- Multiple concurrent users
- Larger datasets
- Production deployments
- Database indexing
- Transactions
- Reliability

---

## 6. Improved UI

Future UI improvements could include:

- Search by transaction ID
- Filter by status
- Filter by source
- Sorting
- Pagination
- Export reconciliation results
- Summary charts
- Bulk manual resolution

---

# Design Decisions Summary

| Decision | Reason |
|---|---|
| Flask | Lightweight and sufficient for the MVP |
| SQLite | Simple local database with no separate server |
| SQLAlchemy | Provides clean database abstraction |
| SHA-256 | Detects identical file contents reliably |
| Exact ID matching | Strongest available automatic matching signal |
| $5 amount tolerance | Allows small rounding/fee differences |
| 30-minute time tolerance | Allows clock and processing-time differences |
| Separate reconciliation runs | Preserves previous results |
| Manual resolution | Allows human decisions when automatic matching is uncertain |
| Normalized transactions | Keeps source-specific formats separate from reconciliation logic |
| Pytest | Provides simple automated testing |

---

# Assumptions

The following assumptions were made for this MVP:

1. Each input CSV contains one transaction per row.
2. The two input formats can be normalized into a common transaction
   structure.
3. Transaction IDs are the preferred way to identify the same transaction.
4. Small monetary differences can occur between systems.
5. Small timestamp differences can occur between systems.
6. Cancelled transactions should not be selected as manual candidates.
7. Previous reconciliation runs should remain available after corrections.
8. Manual decisions should persist in the database.
9. The supplied sample CSV files are used as the input for the current MVP.

---

# Limitations

This project is a take-home MVP and is not intended to be a production-ready
financial reconciliation platform.

The implementation prioritizes:

- Clear reconciliation logic
- Testability
- Simple architecture
- Persistent reconciliation results
- Duplicate detection
- Manual resolution
- Historical reconciliation runs

over:

- Scalability
- Authentication
- Advanced auditability
- Automated scheduling
- Production deployment
- Complex source integrations
- Large-scale data processing

---

# Future Production Architecture

A possible production architecture could look like:

```text
                       +----------------+
                       |      User      |
                       +-------+--------+
                               |
                               v
                       +---------------+
                       |    Web/API    |
                       +-------+-------+
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
         +---------------+           +---------------+
         | File Upload   |           |   Scheduler   |
         +-------+-------+           +-------+-------+
                 |                           |
                 +-------------+-------------+
                               |
                               v
                       +---------------+
                       |    Worker     |
                       +-------+-------+
                               |
                               v
                       +---------------+
                       | Reconciliation|
                       |    Engine     |
                       +-------+-------+
                               |
                               v
                       +---------------+
                       |  PostgreSQL   |
                       +-------+-------+
                               |
                    +----------+----------+
                    |                     |
                    v                     v
             +-------------+       +-------------+
             |   Reports   |       | Notifications|
             +-------------+       +-------------+
```

---

# Conclusion

This project provides a complete reconciliation MVP covering the main stages
of a transaction reconciliation workflow:

```text
Input Files
    ↓
Parsing
    ↓
Normalization
    ↓
Automatic Matching
    ↓
Field Comparison
    ↓
Reconciliation Results
    ↓
Manual Review
    ↓
Resolution
    ↓
Persistent History
```

The design keeps the core reconciliation logic separate from the Flask web
layer and database, making the system easier to test and extend.

The next major improvements for a production system would be:

- Better candidate scoring
- Complete audit history
- Scheduled processing
- Additional source adapters
- PostgreSQL
- Authentication and authorization
- Scalable file processing
- Improved reporting and UI
