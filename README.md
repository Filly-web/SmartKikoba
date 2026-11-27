# VISIONARIES SMART KIKOBA V1.5

Flask-based group savings and loan management portal. Currency: TZS. Production database: PostgreSQL on Render; local development defaults to SQLite.

## V1.5 changes
- Partial instalment payments are accepted. The amount paid is allocated to interest and principal, then applied across the earliest scheduled instalments; the unpaid portion remains outstanding and its deadline continues to be tracked.
- Instalment-count inconsistencies, partial instalments, repayments that appear to cover a different number of instalments, and loans marked Closed with a remaining balance are recorded as review findings rather than automatically rejecting the whole workbook.
- If findings exist, the complete loan import is held and **no loans or transactions are posted**. The Administrator reviews the findings under **Administration → Loan Import Reviews** and approves or leaves them pending.
- After approval, the exact same Excel workbook must be uploaded again to post the batch. The workbook is fingerprinted; editing it after approval requires a fresh review. Structural/data-integrity failures (unknown members, duplicate loan numbers, negative/over-limit amounts, invalid dates and inconsistent repayment splits) remain hard errors and cannot be approved around.
- Each import remains atomic. The approval queue is stored in a new database table created by the existing `init-db` startup command; existing member and financial records are not deleted.

## V1.5 changes
- The historical loan import accepts **all loans** as at 30 October 2026, including fully paid/closed loans and active loans.
- Captures principal repaid and interest collected separately. The optional `Repayment History` sheet captures each actual receipt date, M-Koba transaction/receipt ID and total amount. Interest/principal components can be entered or left blank for automatic interest-first allocation. These dated receipts feed the M-Pesa movement reconciliation on their actual dates. If detailed history is unavailable for a loan, the importer posts its cumulative split at 30 October 2026 and retains the optional M-Koba reference.
- Fully repaid loans are retained with Closed status; interest collected is posted to the LOAN_INTEREST category and principal recovery to LOAN_PRINCIPAL.
- Fixes duplicate transaction references when a repayment spans multiple instalments. Each generated transaction now has a unique instalment-specific reference.
- Validates the complete workbook before posting and commits the import atomically; duplicate loan numbers/references and inconsistent amounts reject the whole upload.
- The importer remains backward-compatible with the previous V1.3 Outstanding Loans template headers.

## V1.3 changes
- Opening member balances can be uploaded as at **31 October 2026**.
- Existing outstanding loans can be uploaded separately as at **30 October 2026**, one loan per Excel row.
- Loan upload captures original loan date, original principal, flat interest rate, optional actual total interest charged, total instalments, fully paid instalments, cumulative amount paid to 30 October, and first due date.
- The application builds the remaining monthly instalment schedule, allocates historic paid amounts to the earliest instalments (interest first), and records the historic loan disbursement and payment movements.
- Loan pages show remaining instalments, overdue instalments, next due date and paid/overdue/future status for every instalment. Loan receipts continue to show the full schedule and current outstanding balances.
- New historical contributions, loans and repayments after the 31 October opening date are uploaded through the historical workbook (from 1 November 2026 onward).
- Added an Administrator-only **Clear group data** screen. It requires typing `CLEAR ALL GROUP DATA` and ticking a confirmation checkbox. It clears members, contributions, loans, loan instalments, opening batches, cash movements, M-Pesa reconciliations and contribution periods. It retains administrator accounts and group settings; non-administrator accounts are deactivated and unlinked. It is not run automatically on deployment.
- Audit Trail functionality remains removed.

## Important accounting treatment
1. Upload the member contribution opening position dated **31 October 2026**.
2. Upload each outstanding loan with the loan register dated **30 October 2026**.
3. Do **not** enter aggregate loan principal or loan interest in the member opening-balance worksheet. The separate loan register creates each loan and its remaining balance. This prevents double counting. Keep the `Loan Principal` and `Loan Interest` columns at zero in the opening-balance sheet.
4. Enter each loan's total amount received up to 30 October 2026. Split it between `Interest Collected` and `Principal Repaid`; their sum must equal `Total Amount Paid`. The optional `Total Interest Charged` overrides the flat-rate calculation where the actual agreed interest differs. `Instalments Paid` is the count of fully settled instalments; fully settled loans must be marked `Closed` even if they were settled before the final scheduled date.
5. For transaction-date M-Koba reconciliation, fill the optional `Repayment History` sheet with each actual receipt date, M-Koba transaction ID and amount. The rows for each loan must add up to the loan register's total paid amount. Interest/principal components may be left blank for automatic interest-first allocation, or entered as a pair. If detailed receipt history is unavailable for a loan, leave it out of that sheet; the system records its cumulative interest and principal totals on 30 October 2026. Those summary-only loans will not be matched by individual payment date.
6. After the opening position is approved, upload contributions, new loans and repayments dated 1 November 2026 onward using the Historical Transactions workbook. Use unique transaction references and the same loan number on loan and repayment rows.

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
Python syntax compilation, source-contract checks and ZIP integrity are checked during packaging. A live Flask/PostgreSQL test cannot be claimed unless run against a configured test database. Test this release against a separate test database before clearing or loading live group records.

### Administrator-set passwords / PINs (V1.6)

The Users & Roles screen no longer imposes a 10-character/digit minimum on the initial password/PIN field. The administrator can set a non-empty password/PIN of the required length; the value is stored as a Werkzeug password hash, not in plain text. Users enter the same value on the login screen. Choose a strong, non-obvious PIN/password and do not reuse personal banking PINs.
