# VISIONARIES SMART KIKOBA V3.1.0 deployment checklist

## Before deployment
1. Take a full PostgreSQL backup and verify the backup.
2. Confirm the ZIP is being deployed to the existing Render service.
3. Confirm the existing `DATABASE_URL` is retained exactly as configured.
4. Do not create, delete, reset or replace the production database.
5. Do not change notification-related files, routes, models, templates or tables.

## Deploy
1. Replace the application source in the existing repository/service with the ZIP contents.
2. Build command: `pip install -r requirements.txt`
3. Start command: `flask --app wsgi.py init-db && gunicorn wsgi:app`
4. `init-db` creates only missing tables. V3.1.0 adds `contribution_obligation` and `contribution_allocation`; it does not alter existing columns or delete records.
5. Sign in using the existing administrator account.

## Test on a separate database first
1. Member sign-in and member-only visibility.
2. Manual member creation and Excel import.
3. Current-month SHARE/SOCIAL weekly obligation generation.
4. Independent monthly SHARE and SOCIAL minimum settings.
5. Automatic allocation to oldest unpaid weeks.
6. Explicit allocation to selected week(s).
7. Partial payment and full payment status changes.
8. Loan disbursement, partial repayment and repayment reversal.
9. Member My Overdues and leaders' Members with Overdues.
10. PDF and Excel report exports.
11. M-Koba ledger, cashflow and reconciliation.
12. Administrator Clear All Records, using only a disposable test database.

## Production precautions
- Do not use Clear All Records as part of deployment.
- Do not import opening balances a second time.
- Do not re-enter historical contributions already included in the approved opening position.
- Historical months with no stored weekly obligation are not assigned new requirements using today's contribution settings.
- Reconcile the new weekly overdue totals against the group's approved contribution records before treating them as authoritative.
