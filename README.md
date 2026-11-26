# VISIONARIES SMART KIKOBA V2.0 — upgrade package

Flask + SQLAlchemy + Flask-Migrate application, SQLite for local development and PostgreSQL for Render. Currency: TZS.

## Inspecting and preserving V1 data
The supplied V1.0 archive contains Flask source, templates, Excel templates and deployment configuration. It does **not** contain a database dump or production PostgreSQL credentials, so the production schema/data could not be inspected directly. No production database was accessed or modified.

The included Alembic baseline is additive and non-destructive: it calls SQLAlchemy `create_all(checkfirst=True)` to create missing tables and deliberately does not drop tables on downgrade. It does not alter existing columns. Before applying to the live Render database, take a PostgreSQL backup and compare the live schema with the V1 models.

## Included in this V2 package
- Existing V1 modules retained: members, contributions, flat-rate loans and schedules, opening balances, cash movements, M-Pesa reconciliation, reports, users, settings, reversals and audit trail.
- Real member names are required; the ten fabricated placeholder members from the old bootstrap routine have been removed. New member numbers can be generated automatically.
- Member Excel import template, import validation, member editing and deactivate/reactivate actions.
- Downloadable loan receipt PDF and repayment schedule PDF.
- Individual member statement PDF with server-side member ownership checks.
- Group meetings, minutes, attendance and resolutions.
- CSV M-Pesa statement intake with duplicate transaction-code checks, member matching and manual allocation of unmatched rows.
- Period-filtered cashbook view.
- Additive migration baseline and Render deployment files.

## Local installation
1. Install Python 3.12.
2. `python -m venv .venv` and activate it.
3. `pip install -r requirements.txt`
4. Set `SECRET_KEY` and optionally `DATABASE_URL`. By default the app uses `sqlite:///kikoba_dev.db`.
5. `flask --app wsgi.py db upgrade`
6. `flask --app wsgi.py init-db`
7. `flask --app wsgi.py run`

Set `BOOTSTRAP_ADMIN_USERNAME` and a strong `BOOTSTRAP_ADMIN_PASSWORD` before initialization. Change bootstrap credentials immediately. Do not use the documented development fallback password in production.

## Render deployment
- Attach the existing PostgreSQL database to the existing Render service; do not create a replacement database if the intention is to retain production records.
- Set a strong `SECRET_KEY`, `BOOTSTRAP_ADMIN_USERNAME`, and `BOOTSTRAP_ADMIN_PASSWORD`.
- Build command: `pip install -r requirements.txt`
- Start command: `flask db upgrade && gunicorn wsgi:app`
- Back up PostgreSQL before the first upgrade and verify the deployed service's `DATABASE_URL`.

## Important limitations — not yet a complete production financial system
This package is an incremental V2 upgrade, not a certification that every item in the development brief is complete. In particular:
- The supplied archive had no database dump, so production schema compatibility and data preservation could not be verified against the actual live database.
- Existing loan engine remains flat-rate and monthly-date based; reducing-balance calculations, weekly/biweekly schedules, formal loan approval workflow, restructuring approvals and full repayment receipt PDFs remain to be implemented.
- Loan receipt PDF is generated for an already-recorded loan; it currently displays the creating/authorised role generically rather than maintaining a separate multi-signatory approval record.
- Member/loan/cashbook/reporting modules do not yet cover all requested financial statements (income & expenditure, full balance sheet, trial balance, aging buckets and month-end close).
- M-Pesa CSV importer accepts common column aliases but requires adaptation to the exact Safaricom statement export; imported matches are not automatically posted to member ledgers. API integration, settlement confirmation and robust reconciliation rules are not included.
- Member bulk upload currently supports Excel `.xlsx`; contribution transaction bulk import, configurable contribution frequency engine and controlled approval for every correction need further work.
- Email/SMS delivery, in-app notification centre, disciplinary register, meeting document attachments, group logo configuration, advanced configurable permissions, password reset/rate limiting, and comprehensive CSRF protection are not complete.
- PDF/Excel exports are provided for selected statements/reports only; several requested report variants remain outstanding.

## Financial controls inherited from V1
- Flat interest = principal × flat rate.
- First installment carries all loan interest; principal is distributed equally.
- Repayment is allocated to the earliest outstanding installment, interest first, then principal.
- Only collected interest is realised profit; principal repayment is not profit.
- Penalties are a separate reporting category but counted once within SOCIAL.
- M-Pesa movement reconciliation records variances; it does not auto-clear differences.
- Opening balance batches require Chairman approval.

## Testing
Run `pytest -q` after installing requirements. The existing financial logic tests are retained. This build was syntax-checked, but full integration tests could not be executed in the build environment because Flask/Flask-SQLAlchemy/Flask-Migrate are not installed here. Complete UAT against a restored PostgreSQL backup before production use.
