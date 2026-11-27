from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_repayment_history_mismatch_is_a_finding_not_hard_rejection():
    source = (ROOT / "app.py").read_text()
    assert "Repayment History totals TZS" in source
    assert "soft_findings.append" in source
    assert "if soft_findings and not approved_review:" in source
    assert "history_usable" in source

def test_optional_history_falls_back_to_cumulative_snapshot_once():
    source = (ROOT / "app.py").read_text()
    assert "if not hrows:" in source
    assert "if history_usable.get(x[\"no\"],False) else []" in source
    assert "only cumulative Loan Register totals will be posted" in source

def test_money_parser_accepts_commas_tzs_and_dash():
    source = (ROOT / "app.py").read_text()
    assert 'raw.replace(",", "").replace("TZS", "").replace("tzs", "")' in source
    assert 'raw in ("", "-")' in source
