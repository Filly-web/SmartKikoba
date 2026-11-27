from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text()
DASH = (ROOT / "templates" / "dashboard.html").read_text()
RECON = (ROOT / "templates" / "reconciliation.html").read_text()
OPENING = (ROOT / "templates" / "opening.html").read_text()

def test_dashboard_always_shows_expected_mkoba_balance():
    assert 'EXPECTED M-KOBA BALANCE' in DASH
    assert "cash=expected_mkoba(d)" in APP

def test_wallet_formula_includes_receipts_and_payments():
    assert '"SHARE","SOCIAL","PENALTY","LOAN_INTEREST","LOAN_PRINCIPAL"' in APP
    assert 't.category=="LOAN_DISBURSEMENT"' in APP
    assert 'm.direction=="IN"' in APP
    assert 'opening+inflows-outflows' in APP

def test_snapshot_excludes_earlier_movements_to_prevent_double_counting():
    assert 'Transaction.transaction_date>movement_start' in APP
    assert 'CashMovement.movement_date>movement_start' in APP

def test_opening_upload_captures_actual_mkoba_balance():
    assert 'name="mkoba_opening"' in OPENING
    assert 'mpesa_opening=money(request.form.get("mkoba_opening",0))' in APP

def test_reconciliation_uses_mkoba_language_and_flow_breakdown():
    assert 'M-Koba Reconciliation' in RECON
    assert 'cashflow.inflows' in RECON
    assert 'cashflow.outflows' in RECON
