# VISIONARIES SMART KIKOBA V1.3

Flask-based group savings and loan management portal. Currency: TZS. Production database: PostgreSQL on Render; local development defaults to SQLite.

## V1.3 changes
- Opening member balances can be uploaded as at **31 October 2026**.
- Existing outstanding loans can be uploaded separately as at **30 October 2026**, one loan per Excel row.
- Loan upload captures original loan date, original principal, flat interest rate, total instalments, fully paid instalments, cumulative amount paid to 30 October, and first due date.
- The application builds the remaining monthly instalment schedule, allocates historic paid amounts to the earliest instalments (interest first), and records the historic loan disbursement and payment movements.
- Loan pages show remaining instalments, overdue instalments, next due date and paid/overdue/future status for every instalment. Loan receipts continue to show the full schedule and current outstanding balances.
- New historical contributions, loans and repayments after the 31 October opening date are uploaded through the historical workbook (from 1 November 2026 onward).
- Added an Administrator-only **Clear group data** screen. It requires typing `CLEAR ALL GROUP DATA` and ticking a confirmation checkbox. It clears members, contributions, loans, loan instalments, opening batches, cash movements, M-Pesa reconciliations and contribution periods. It retains administrator accounts and group settings; non-administrator accounts are deactivated and unlinked. It is not run automatically on deployment.
- Audit Trail functionality remains removed.

## Important accounting treatment
1. Upload the member contribution opening position dated **31 October 2026**.
2. Upload each outstanding loan with the loan register dated **30 October 2026**.
3. Do **not** enter aggregate loan principal or loan interest in the member opening-balance worksheet. The separate loan register creates each loan and its remaining balance. This prevents double counting. Keep the `Loan Principal` and `Loan Interest` columns at zero in the opening-balance sheet.
4. Enter the actual cumulative amount received up to 30 October 2026 in the loan register. `Instalments Paid` means the number of completely settled instalments. A partial payment after those complete instalments is included in `Amount Paid`. The amount paid must be consistent with the number of fully paid instalments.
5. After the opening position is approved, upload contributions, new loans and repayments dated 1 November 2026 onward using the Historical Transactions workbook. Use unique transaction references and the same loan number on loan and repayment rows.

## Local setup
1. Python 3.12 or later recommended.
2. `python -m venv .venv` and activate it.
3. `pip install -r requirements.txt`
4. Set `SECRET_KEY`, `DATABASE_URL` (optional locally).
5. Set `BOOTSTRAP_ADMIN_USERNAME` and `BOOTSTRAP_ADMIN_PASSWORD` for first-time database setup.
6. `flask --app wsgi.py init-db`
7. `flask --app wsgi.py run`

## Render deployment
- Keep the existing Render service, PostgreSQL database and `DATABASE_URL`. Do not delete or recreate the production database.
- Build command: `pip install -r requirements.txt`
- Start command: `flask --app wsgi.py init-db && gunicorn wsgi:app`
- `init-db` creates missing tables and creates an administrator only if the configured username does not already exist. It does not clear or reset existing records.

## Clearing the old portal data
The ZIP does not automatically wipe the live database. After deploying and signing in as Administrator, open **Administration → Clear group data**, review the list of records to be deleted, type the exact phrase `CLEAR ALL GROUP DATA`, tick the checkbox and submit. Take a PostgreSQL backup first. The reset is permanent. It retains administrator login(s) and group settings; all non-administrator accounts are deactivated.

## Validation status
Python syntax compilation and ZIP integrity are checked during packaging. A live Flask/PostgreSQL test cannot be claimed unless run against a configured test database. Test this release against a separate test database before clearing or loading live group records.
