# VISIONARIES SMART KIKOBA V3.1

Flask-based group savings and loan management portal. Currency: TZS. Production database: PostgreSQL on Render; local development defaults to SQLite.

## V1.7 changes
- Repayment History is optional; the Loan Register cumulative principal/interest paid figures can be imported without transaction-level receipt detail.
- Repayment History totals or principal/interest split differences are recorded as Administrator review findings, not immediate upload errors. The full workbook is held until approval.
- If history is absent or does not reconcile, the approved import posts only the cumulative Loan Register principal and interest totals once at 30 October 2026; it does not also post the non-reconciling detailed rows. This prevents duplicate cash/repayment recognition. Such summary postings are historical/unmatched for transaction-date M-Koba reconciliation.
- If Repayment History reconciles exactly, its dated payments and M-Koba references are posted individually.
- TZS input parsing accepts comma-separated amounts, optional TZS prefixes, blanks and a dash for zero. Invalid numeric cells produce a Decimal conversion error that is caught by the import's row-level exception handling (financial columns are validated before posting).

## V1.6 changes
- Administrator-set password/PIN field has no fixed 10-digit requirement; values remain securely hashed.

## V1.5 changes
- Partial instalment payments are accepted. The amount paid is allocated to interest and principal, then applied across the earliest scheduled instalments; the unpaid portion remains outstanding and its deadline continues to be tracked.
- Instalment-count inconsistencies, partial instalments, repayments that appear to cover a different number of instalments, and loans marked Closed with a remaining balance are recorded as review findings rather than automatically rejecting the whole workbook.
- If findings exist, the complete loan import is held and **no loans or transactions are posted**. The Administrator reviews the findings under **Administration → Loan Import Reviews** and approves or leaves them pending.
- After approval, the exact same Excel workbook must be uploaded again to post the batch. The workbook is fingerprinted; editing it after approval requires a fresh review. Structural/data-integrity failures (unknown members, duplicate loan numbers, negative/over-limit amounts, invalid dates and inconsistent repayment splits) remain hard errors and cannot be approved around.
- Each import remains atomic. The approval queue is stored in a new database table created by the existing `init-db` startup command; existing member and financial records are not deleted.

## V1.5 changes
- The historical loan import accepts **all loans** as at 30 October 2026, including fully paid/closed loans and active loans.
- Captures principal repaid and interest collected separately. The optional `Repayment History` sheet captures each actual receipt date, M-Koba transaction/receipt ID and total amount. Interest/principal components can be entered or left blank for automatic interest-first allocation. These dated receipts feed the M-Koba cash-flow reconciliation on their actual dates. If detailed history is unavailable for a loan, the importer posts its cumulative split at 30 October 2026 and retains the optional M-Koba reference.
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
- Added an Administrator-only **Clear group data** screen. It requires typing `CLEAR ALL GROUP DATA` and ticking a confirmation checkbox. It clears members, contributions, loans, loan instalments, opening batches, cash movements, M-Koba reconciliations and contribution periods. It retains administrator accounts and group settings; non-administrator accounts are deactivated and unlinked. It is not run automatically on deployment.
- Audit Trail functionality remains removed.

## Important accounting treatment
1. Upload the member contribution opening position dated **31 October 2026**.
2. Upload each outstanding loan with the loan register dated **30 October 2026**.
3. Do **not** enter aggregate loan principal or loan interest in the member opening-balance worksheet. The separate loan register creates each loan and its remaining balance. This prevents double counting. Keep the `Loan Principal` and `Loan Interest` columns at zero in the opening-balance sheet.
4. Enter each loan's total amount received up to 30 October 2026. Split it between `Interest Collected` and `Principal Repaid`; their sum must equal `Total Amount Paid`. The optional `Total Interest Charged` overrides the flat-rate calculation where the actual agreed interest differs. `Instalments Paid` is the count of fully settled instalments; fully settled loans must be marked `Closed` even if they were settled before the final scheduled date.
5. For transaction-date M-Koba reconciliation, optionally fill the `Repayment History` sheet with each actual receipt date, M-Koba transaction ID and amount. When the detailed rows reconcile to the Loan Register total and split, they are posted individually. If the sheet is absent or does not reconcile, the system creates an Administrator finding. After approval, it posts only the Loan Register cumulative interest and principal totals once on 30 October 2026; the detailed rows are not also posted. Summary-only loans are not matched by individual payment date and should be reconciled to M-Koba separately.
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


## V1.8 — M-Koba expected cash balance
- M-Koba is treated as the group's current wallet (same cash account as M-Pesa for this release). The dashboard displays one **Expected M-Koba Balance** for all user roles.
- The expected balance is calculated as: opening M-Koba wallet balance + posted cash inflows − posted cash outflows.
- Cash inflows include share contributions, social contributions, penalties collected, loan principal repayments and loan interest received. Cash outflows include loan disbursements and posted cash movements marked OUT (expenses, withdrawals and other payments). Other cash receipts are entered as CashMovement marked IN.
- The 31 October 2026 opening-balance upload now includes an opening M-Koba wallet balance field. Enter the actual wallet balance at that date; it is the starting cash balance for subsequent movements. The latest approved opening wallet snapshot on or before a report date is used as the base, and only movements dated after that snapshot are added, preventing pre-opening history from being counted twice.
- The dashboard does not calculate a separate net-asset/group-funds balance and does not subtract outstanding loans from wallet cash. Outstanding loans remain tracked separately in the loan module.
- M-Koba reconciliation compares the expected wallet cash balance with the actual M-Koba statement balance. Differences remain visible and are not auto-adjusted.


## V1.9 — Unified M-Koba cashbook and cash-flow control
- M-Koba is treated as the single group cash wallet (the same cash account as M-Pesa for now). The dashboard and reconciliation use one expected cash balance, not a net-assets calculation.
- Cash IN is generated automatically from SHARE, SOCIAL, PENALTY, loan principal repayments and loan interest receipts. Cash OUT is generated automatically from loan disbursements.
- Other expenses, withdrawals, other receipts and other payments are entered through the manual M-Koba cash movement screen. The screen explicitly warns users not to re-enter contribution or loan movements, preventing double counting. Category and direction are validated together.
- The M-Koba cash ledger combines system-generated contribution/loan transactions with manual cash movements in one date-ordered view.
- Reversed posted transactions are reflected in the opposite cash direction; the original reversed posting is not counted as active cash.
- The expected balance is opening M-Koba cash + all cash IN − all cash OUT. The latest approved opening snapshot is the starting point; transactions dated on or before that snapshot are excluded from subsequent movements because they are already represented in the opening wallet balance.
- Manual cash movements dated on or before the approved opening snapshot are rejected to prevent hidden or duplicated pre-opening cash activity. Include those amounts in the approved opening wallet balance instead.
- The dashboard, M-Koba ledger and M-Koba reconciliation all use the same cash-flow calculation. Outstanding loan balances are not deducted from wallet cash.

## V1.9 deployment note
This release changes the calculation and presentation of the M-Koba cash ledger only. It does not require dropping or recreating existing database tables and does not clear group records. Existing approved opening snapshots and existing transaction/cash-movement rows remain in place. Because this release now includes reversed transactions in the opposite cash direction, review reversals and compare the expected wallet balance with the M-Koba statement after deployment.

## V1.9 validation
- Python compilation and AST parsing passed.
- All Jinja templates parsed successfully.
- 17 targeted source-contract tests passed (loan import, partial-payment approval, optional repayment history and M-Koba cash-flow contracts).
- Full pytest collection was not possible because Flask is not installed in the packaging environment; the Flask runtime and live PostgreSQL/Render integration have not been tested here.


## V2.1 — M-Koba opening balance linked to opening contributions and historical loans
- Removed the manually entered opening M-Koba wallet amount. The application now calculates the opening wallet position from the approved 31 October 2026 opening member balances and the historical loan register.
- Opening cash starts with cumulative SHARE + SOCIAL contributions recorded in the approved opening balance batch.
- Every imported historical loan disbursement dated on/before 31 October is treated as cash OUT. Historical principal repayments and interest collected dated on/before 31 October are treated as cash IN. This includes active, partly repaid and fully closed loans.
- Formula: **Opening M-Koba cash = opening SHARE + SOCIAL + historical principal repayments + historical interest collected − historical loan disbursements.**
- From 1 November 2026 onward, all new SHARE/SOCIAL/paid-penalty receipts, loan disbursements, principal/interest repayments and manual other receipts/payments flow into the same M-Koba cash ledger and dashboard balance.
- The M-Koba ledger displays the opening contribution total and individual historical loan cash movements, then all subsequent movements. The dashboard, cash ledger and reconciliation use the same calculation.
- Outstanding loan balances, unpaid penalties and loan instalment counts are not cash and are not directly added to or deducted from the wallet. The opening template's `Unpaid Penalty` column remains a receivable/obligation measure, not cash collected. Penalties actually collected are cash IN when recorded as `PENALTY` transactions.
- Existing database tables are retained. The legacy `mpesa_opening` column is left in place for backward compatibility but is no longer used in the expected M-Koba calculation. No destructive migration or automatic data reset is required.

## V2.1 validation notes
Python syntax compilation, source-contract tests, workbook presence, template parsing where available, and ZIP integrity are checked. Full Flask/PostgreSQL/Render integration must still be tested against a separate test database before production use.


V2.1 dashboard linkage correction: dashboard SHARE, SOCIAL and loan balances now use the latest approved opening batch applicable to the report date and add only transactions posted after that snapshot. This prevents later approved batches from being summed together and prevents pre-opening transactions from being double-counted. November SHARE/SOCIAL receipts and loan principal/interest repayments feed dashboard balances and the M-Koba cashflow automatically.


## V3.0 — 360° Cooperative Management update

V3.1 retains the V2.1 financial models, opening balances, historical loan imports, transaction ledger, M-Koba calculations and manual leader loan entry. It adds:

- A responsive sidebar workspace with simplified financial navigation.
- Immediate posting for authorised contribution, loan, repayment and cash-movement entries; these do not wait for a separate posting approval. Loan applications remain a separate leader-decision workflow.
- A member loan application page for existing registered members, with Airtel, Tigo, Halotel, Vodacom, TTCL and Other network choices. Application submission does not create a loan.
- Leader review (Administrator, Chairman, Secretary or Treasurer). Approval creates the loan, repayment schedule and loan-disbursement transaction in Loan Tracking. Rejection requires a reason. Manual loan entry remains available.
- Monthly/date-range and full-history contribution reports in Excel and PDF, with member summary and transaction detail in Excel.
- Administrator user deletion. Financial records are retained; creator/reviewer references to a deleted account are set to null. The current account and last active administrator are protected.

### Deployment note for existing V2.1 databases

Back up the production database first. Deploy the V3.0 source to the existing Render service and keep its existing `DATABASE_URL`; do not delete or recreate the database. The new `loan_application` table must be created once using the existing CLI command:

```bash
flask --app wsgi:app init-db
```

The command uses `db.create_all()` to create missing tables and does not clear existing records. Do not run the separate operational-data reset function. Verify the database backup before deployment.

### Transaction control

Authorised operational entries are posted immediately (status `Posted`) and update the financial ledger. Reversals remain available to authorised roles and preserve the original record. Loan applications are not financial transactions until a leader approves them.

### Verification limitation

Python syntax compilation and template parsing should be completed before release. Full Flask integration tests require installing the packages in `requirements.txt`; this build environment had no network access to install Flask, so it could not run the live Flask application or database integration tests here.


## V3.1 additions
- Member financial reports now export a detailed financial position, posted transactions, loan position and opening balances; member exports are scoped to the logged-in member.
- Group settings support separate minimum monthly SHARE and SOCIAL amounts.
- Contributions can be allocated across one or more of four monthly weeks; weekly obligation view calculates each week's shortfall.
- In-app notifications cover new loan applications and member loan decisions.
- Leaders can send all-member or individual-member portal messages; members can read messages in the portal.
- Normal members retain view-only loan access; loan payment posting remains restricted to authorised leaders.

Run `flask --app wsgi:app init-db` after deployment to create the new V3.1 tables. This uses `db.create_all()` and does not drop or reset existing tables or records. Back up the production database first.

### Existing database notification schema repair
The `init-db` command includes an additive compatibility repair for existing `in_app_notification` tables missing `recipient_user_id`. It adds the column and index, and copies legacy `user_id` values where that column exists. It does not drop tables or clear records. Keep the Render start command as `flask --app wsgi.py init-db && gunicorn wsgi:app`.
