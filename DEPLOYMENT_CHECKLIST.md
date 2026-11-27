# V1.5 deployment checklist

- [ ] Back up the existing PostgreSQL database.
- [ ] Deploy V1.5 to the existing Render service; keep the existing `DATABASE_URL`.
- [ ] Ensure the Start Command runs `flask --app wsgi.py init-db && gunicorn wsgi:app` so the new loan-import-review table is created. `db.create_all()` creates the new table without deleting existing tables or records.
- [ ] Sign in as Administrator and open **Administration → Loan Import Reviews**.
- [ ] Upload the historical loan workbook. If findings are raised, no loans will be posted until Administrator approval.
- [ ] Administrator reviews each finding and approves where appropriate.
- [ ] Re-upload the exact same Excel workbook after approval. Do not edit and re-save it between approval and posting.
- [ ] Verify the imported loan balances, partial instalment schedules, interest totals and M-Koba receipt references before using live records.

Structural errors such as unknown members, duplicate loan numbers, invalid dates, negative amounts and inconsistent payment splits remain rejected. Test against a separate database before production use.
