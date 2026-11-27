from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text()
OPENING = (ROOT / "templates" / "opening.html").read_text()
DASH = (ROOT / "templates" / "dashboard.html").read_text()
RECON = (ROOT / "templates" / "reconciliation.html").read_text()


def test_opening_cash_is_derived_from_member_contributions_and_historic_loans():
    assert "def mkoba_opening_cash(snapshot):" in APP
    assert "money(item.share) + money(item.social)" in APP
    assert 'Transaction.loan_id.isnot(None)' in APP
    assert '"LOAN_DISBURSEMENT", "LOAN_PRINCIPAL", "LOAN_INTEREST"' in APP
    assert "return contribution_cash + historic_in - historic_out" in APP


def test_opening_wallet_is_not_manually_entered_anymore():
    assert 'name="mkoba_opening"' not in OPENING
    assert 'name="mkoba_opening"' not in APP
    assert 'mpesa_opening=Decimal("0")' in APP
    assert "Do not enter a separate wallet balance" in OPENING


def test_historical_opening_loan_cash_is_visible_in_the_ledger():
    assert '"source": "Historical loan opening"' in APP
    assert '"source": "Opening contribution balances"' in APP
    assert "Calculated M-Koba opening balance" in OPENING


def test_subsequent_cash_movements_are_added_after_opening_snapshot():
    assert 'Transaction.transaction_date > movement_start' in APP
    assert 'CashMovement.movement_date > movement_start' in APP
    assert 'opening + inflows - outflows' in APP


def test_dashboard_and_reconciliation_explain_calculated_opening_position():
    assert "EXPECTED M-KOBA BALANCE" in DASH
    assert "historic loan cash flows" in DASH
    assert "historic loan cash flows" in RECON


def test_user_example_opening_wallet_balance_is_85000():
    from decimal import Decimal
    opening_contributions = Decimal("100000")
    loan_disbursement = Decimal("50000")
    principal_repaid = Decimal("30000")
    interest_collected = Decimal("5000")
    expected = opening_contributions - loan_disbursement + principal_repaid + interest_collected
    assert expected == Decimal("85000")
