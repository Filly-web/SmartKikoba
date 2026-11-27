# VISIONARIES SMART KIKOBA V3.1 deployment checklist

1. Back up the existing PostgreSQL database before deployment.
2. Replace the application source in the existing GitHub repository with the contents of this folder.
3. Keep the existing Render service, PostgreSQL database and `DATABASE_URL`. Do not delete or recreate the production database.
4. Build command: `pip install -r requirements.txt`
5. Start command: `flask --app wsgi.py init-db && gunicorn wsgi:app`
6. Deploy and sign in using the existing administrator account.
7. Ensure the approved 31 October 2026 opening member balance batch contains cumulative SHARE and SOCIAL amounts.
8. Import all historical loans (active, partly repaid and closed), including original disbursement amounts and cumulative principal/interest repayments or dated Repayment History. These historic loan movements feed the calculated opening M-Koba cash.
9. The system calculates opening M-Koba cash as opening SHARE + SOCIAL + historic principal repayments + historic interest collected - historic loan disbursements. No manual wallet opening figure is required.
10. From 1 November 2026 onward, post contributions, new loans and repayments through their respective modules. They automatically update M-Koba. Record only expenses, withdrawals and other cash movements through the M-Koba cash movement screen.
11. Compare the expected M-Koba balance with the actual wallet statement under M-Koba Reconciliation.
12. Test the release against a separate test database before relying on it for live financial reporting.

The application does not automatically clear existing data during deployment. The old `mpesa_opening` database field is retained for compatibility but is ignored by the new calculated balance.


V2.1 dashboard linkage correction: dashboard SHARE, SOCIAL and loan balances now use the latest approved opening batch applicable to the report date and add only transactions posted after that snapshot. This prevents later approved batches from being summed together and prevents pre-opening transactions from being double-counted. November SHARE/SOCIAL receipts and loan principal/interest repayments feed dashboard balances and the M-Koba cashflow automatically.


## V3.0 upgrade steps (existing Render service)

1. Take a verified backup of the existing PostgreSQL database.
2. Replace the deployed source with the V3.0 ZIP contents. Keep the existing Render service and `DATABASE_URL`.
3. From the Render Shell, run `flask --app wsgi:app init-db` once to create the new loan application table. This calls `create_all()` and does not erase existing records.
4. Confirm a member login can submit an application using Airtel/Tigo/Halotel; confirm a leader can approve it and see the resulting loan in Loan Tracking.
5. Test manual loan entry, contribution posting, reversal, monthly contribution export and full-history export.
6. Do not use the operational data reset page as part of this upgrade.

V3.0 user deletion preserves financial records and clears only references to the deleted user account.


## V3.1 upgrade steps (existing Render service)

1. Take a verified PostgreSQL backup.
2. Replace the source files in the existing Render service with this V3.1 package. Keep the same Render service, PostgreSQL database and `DATABASE_URL`.
3. Confirm the Render build command is `pip install -r requirements.txt`; `requirements.txt` contains package requirements only. The `Procfile` contains `web: gunicorn wsgi:app`.
4. Run `flask --app wsgi:app init-db` once (or allow the configured Render start command to run it). This creates only missing tables for weekly allocations, portal messages and notifications; it does not delete existing records.
5. In Group Settings, set the monthly SHARE and SOCIAL minimums.
6. Record a test contribution and select one or more weeks. Open Weekly Obligations to confirm paid weeks and outstanding amounts. Existing unallocated legacy receipts are assigned to the calendar week of their transaction date for reporting.
7. Test member financial report exports, leader loan application notifications, and leader-to-member messages using test accounts.
8. Normal members can view their own loans but cannot post, allocate, edit or reverse loan payments. Only authorised leaders can post repayments.
9. Do not run Clear All Records during an upgrade.

## V3.1.1 notification schema compatibility fix
If upgrading an existing V3.0/V3.1 database where `in_app_notification` already exists, the `init-db` command now adds the missing `recipient_user_id` column and index without dropping or clearing notification or financial records. Ensure the Render Start Command runs `flask --app wsgi.py init-db && gunicorn wsgi:app` so the additive schema repair runs before the web worker starts.
