# Deployment checklist

- [ ] Back up the existing Render PostgreSQL database and verify restore.
- [ ] Compare live V1 schema to models in `app.py`; additive baseline does not alter existing columns.
- [ ] Attach the existing database to the existing Render web service; do not provision a replacement.
- [ ] Set unique SECRET_KEY and bootstrap credentials.
- [ ] Deploy and run `flask db upgrade`; verify new tables and existing record counts.
- [ ] Log in as each role and verify member ownership restrictions.
- [ ] Import a test member workbook and test duplicate rejection.
- [ ] Create a test loan, download receipt and schedule PDFs.
- [ ] Record partial and full repayments; reconcile ledger totals.
- [ ] Import a sample M-Pesa CSV and allocate an unmatched item.
- [ ] Verify cashbook totals against source transactions.
- [ ] Restore backup to a staging database and perform user acceptance tests before live posting.
