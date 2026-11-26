# VISIONARIES SMART KIKOBA V1.0

Standalone first release built from scratch. Flask + SQLAlchemy + PostgreSQL, Render deployment, TZS currency.

## Included
- Role-based access: Administrator, Chairman, Secretary, Accountant, Member.
- Member registry and member-only financial views.
- SHARE, SOCIAL and separately identified penalty receipts (penalties included in SOCIAL once).
- Flat-rate loans, automatic schedule, interest-first repayment allocation, partial repayments.
- Opening balances as at 1 September 2026, Excel template/upload, draft/Chairman approval lock.
- Backdated transactions from 1 September 2026 with separate transaction and entry timestamps.
- M-Pesa cash movement reconciliation, variance history, Chairman review without auto-balancing.
- Cash expenses/withdrawals/other movements.
- Historical date reporting and Excel export.
- Transaction reversals with mandatory explanation and audit records.
- Configurable contribution and penalty settings.
- Audit trail, Render configuration, PostgreSQL support.

## Local setup
1. Python 3.12 recommended.
2. `python -m venv .venv` and activate it.
3. `pip install -r requirements.txt`
4. Set `SECRET_KEY`, `DATABASE_URL` (optional; defaults to SQLite locally).
5. `flask --app wsgi.py init-db`
6. `flask --app wsgi.py run`

Default local bootstrap credentials (change immediately):
- username: `admin`
- password: `ChangeMe-Immediately-2026`

Set `BOOTSTRAP_ADMIN_USERNAME` and `BOOTSTRAP_ADMIN_PASSWORD` before `init-db` in production.

## Render deployment
- Create a PostgreSQL database and web service, or deploy using `render.yaml`.
- Set `SECRET_KEY` to a long random secret.
- Set `BOOTSTRAP_ADMIN_PASSWORD` to a unique strong password.
- Build: `pip install -r requirements.txt`
- Start: `flask db upgrade && gunicorn wsgi:app`

### First deployment database initialization
This is a new V1.0 installation. Run `flask --app wsgi.py init-db` once after first deployment to create tables, initial 10 member placeholders and administrator. For a fresh Render deployment, you may temporarily use a one-off shell. Do not run `db.create_all()` against an existing production database without reviewing the schema.

## Financial rules
- Flat interest = principal × flat rate.
- First installment carries all loan interest; principal is distributed equally across installments.
- Repayment is applied to earliest outstanding installment, interest first, then principal.
- Only collected interest is realised profit; principal repayment is not profit.
- Penalties are a distinct reporting category but counted once within SOCIAL.
- Expected M-Pesa is movement-based: opening cash + all receipts including principal repayments and interest − disbursements − cash outflows ± other movements.
- The separate group financial position formula is not a substitute for the movement-based cash reconciliation.
- Reconciliation variances are displayed and never auto-cleared.
- Opening balance batches affect official totals only after Chairman approval.

## Important release limitations / hardening before live financial use
- The supplied requirements did not specify the group's confirmed SHARE/SOCIAL allocation; settings are configurable and seeded with 50/50 as an editable starting value, not an approved policy.
- Four weekly contribution opportunities and penalty assessment are represented through contribution-period configuration, but scheduled automatic penalty accrual is not yet implemented; penalty receipts can be posted manually.
- PDF export, automated member compliance scoring, M-Pesa statement import/API integration, notification delivery, and detailed adjustment approval workflow are not included in this first source package.
- The application provides the core posting and approval workflows; conduct user acceptance testing and an independent financial control review before live deployment.
- For live use, add CSRF tokens to every form, enforce password policy/rate limiting, configure HTTPS, backup PostgreSQL, and test restore procedures. Flask-WTF is installed but CSRF enforcement is not yet wired into all forms.
- Do not treat the generated example/test data as actual group balances.

## Database migrations
Initialize migrations on the development copy with `flask --app wsgi.py db init`, then `flask --app wsgi.py db migrate -m "initial schema"` and `flask --app wsgi.py db upgrade`. Commit the generated `migrations/` directory to source control. On a brand-new database, `flask init-db` is the simplest bootstrap path.
