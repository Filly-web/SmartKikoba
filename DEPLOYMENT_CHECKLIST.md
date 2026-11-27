# V1.7 deployment checklist

- [ ] Back up the existing PostgreSQL database.
- [ ] Replace application source with V1.7 in the existing GitHub repository.
- [ ] Keep the existing Render service and `DATABASE_URL`; do not recreate the database.
- [ ] Build command: `pip install -r requirements.txt`.
- [ ] Start command: `flask --app wsgi.py init-db && gunicorn wsgi:app`.
- [ ] Deploy and confirm the administrator can sign in.
- [ ] Test the loan import first using a separate test database or test deployment.
- [ ] If findings are raised, review them under Administration → Loan Import Reviews, approve only after checking the underlying M-Koba/loan records, then upload the exact same workbook bytes again.
- [ ] Confirm summary-only historical repayments are recorded at 30 October 2026 and are not treated as individually date-matched M-Koba receipts.

The ZIP does not automatically clear existing records. Do not use the Clear Group Data function unless a deliberate reset is required and a backup has been taken.
