from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_partial_installments_are_findings_not_hard_rejections():
    source = (ROOT / "app.py").read_text()
    assert "partial instalment detected" in source
    assert "soft_findings.append" in source
    assert "if soft_findings and not approved_review:" in source


def test_import_is_held_until_administrator_approval():
    source = (ROOT / "app.py").read_text()
    assert "class LoanImportReview(db.Model):" in source
    assert 'def loan_opening_reviews()' in source
    assert 'def approve_loan_opening_review(review_id):' in source
    assert 'status="Approved"' in source
    assert 'status="Consumed"' in source


def test_approved_workbook_must_match_exact_upload_bytes():
    source = (ROOT / "app.py").read_text()
    assert "workbook_hash=hashlib.sha256(workbook_bytes).hexdigest()" in source
    assert 'filter_by(workbook_hash=workbook_hash,status="Approved")' in source
