from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text()


def test_dashboard_uses_one_latest_applicable_opening_batch():
    assert 'snapshot = mkoba_snapshot(report_date)' in APP
    assert 'OpeningBalance.query.filter_by(batch_id=snapshot.id)' in APP
    assert 'OpeningBalance.query.join(OpeningBatch).filter(OpeningBatch.status=="Approved")' not in APP


def test_dashboard_adds_only_transactions_after_opening_snapshot():
    assert 'q = txn_query(report_date, member_id)' in APP
    assert 'q = q.filter(Transaction.transaction_date > snapshot.opening_date)' in APP
    assert 'Opening balances already include all member balances through the snapshot date.' in APP


def test_share_social_and_loan_repayments_flow_into_dashboard_totals():
    totals_block = APP.split('def totals(as_at=None, member_id=None):', 1)[1].split('\ndef loan_outstanding', 1)[0]
    assert 'if t.category=="SHARE": data["share"] += money(t.amount)' in totals_block
    assert 'elif t.category=="SOCIAL": data["social"] += money(t.amount)' in totals_block
    assert 'elif t.category=="LOAN_PRINCIPAL": data["loan_principal"] -= money(t.amount)' in totals_block
    assert 'elif t.category=="LOAN_INTEREST": data["loan_interest"] -= money(t.amount)' in totals_block


def test_mkoba_cash_ledger_includes_post_snapshot_share_social_and_loan_receipts():
    ledger = APP.split('def mkoba_cash_ledger(as_at):', 1)[1].split('\ndef mkoba_cashflow', 1)[0]
    assert 'Transaction.transaction_date > movement_start' in ledger
    assert '"SHARE", "SOCIAL", "PENALTY", "LOAN_INTEREST", "LOAN_PRINCIPAL"' in APP
