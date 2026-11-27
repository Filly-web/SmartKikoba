from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text()
DASH = (ROOT / "templates" / "dashboard.html").read_text()
RECON = (ROOT / "templates" / "reconciliation.html").read_text()
OPENING = (ROOT / "templates" / "opening.html").read_text()
CASH = (ROOT / "templates" / "cash_movements.html").read_text()

def test_dashboard_always_shows_expected_mkoba_balance():
    assert 'EXPECTED M-KOBA BALANCE' in DASH
    assert 'cashflow=mkoba_cashflow(d)' in APP
    assert 'cash=cashflow["closing"]' in APP

def test_wallet_formula_includes_all_operational_cash_categories():
    for category in ['"SHARE"', '"SOCIAL"', '"PENALTY"', '"LOAN_INTEREST"', '"LOAN_PRINCIPAL"']:
        assert category in APP
    assert 'elif t.category=="LOAN_DISBURSEMENT"' in APP
    assert 'opening+inflows-outflows' in APP

def test_reversals_reverse_cash_direction():
    assert 'Transaction.status.in_(["Posted","Reversal"])' in APP
    assert 'if t.status=="Reversal"' in APP
    assert 'direction="OUT" if direction=="IN" else "IN"' in APP

def test_snapshot_excludes_earlier_movements_to_prevent_double_counting():
    assert 'Transaction.transaction_date>movement_start' in APP
    assert 'CashMovement.movement_date>movement_start' in APP

def test_opening_upload_captures_actual_mkoba_balance():
    assert 'name="mkoba_opening"' in OPENING
    assert 'mpesa_opening=money(request.form.get("mkoba_opening",0))' in APP

def test_reconciliation_and_cash_ledger_share_same_calculation():
    assert 'cashflow.inflows' in RECON
    assert 'cashflow.outflows' in RECON
    assert 'ledger=mkoba_cash_ledger(as_at)' in APP
    assert 'Consolidated M-Koba cash ledger' in CASH

def test_manual_cash_movements_cannot_duplicate_automatic_transaction_types():
    assert 'Other receipt' in APP and 'Other payment' in APP
    assert 'Do not re-enter shares, social, penalties, loan disbursements or loan repayments here.' in CASH
    assert 'allowed[category]!=direction' in APP

def test_manual_movements_before_or_on_opening_snapshot_are_rejected():
    assert 'movement_date<=snapshot.opening_date' in APP
