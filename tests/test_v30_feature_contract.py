from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_existing_member_loan_application_and_leader_approval_are_present():
    assert "class LoanApplication(db.Model)" in APP
    assert '@app.route("/loan-applications", methods=["GET", "POST"])' in APP
    assert '@roles_required("Administrator","Chairman","Secretary","Treasurer")' in APP
    assert 'category="LOAN_DISBURSEMENT"' in APP
    assert 'a.status="Approved"' in APP and 'a.status="Rejected"' in APP


def test_contribution_reports_support_date_range_and_both_formats():
    assert '/contributions/reports/export.xlsx' in APP
    assert '/contributions/reports/export.pdf' in APP
    assert 'def contribution_report_rows(start=None, end=None, member_id=None)' in APP
    assert 'Transaction.transaction_date>=start' in APP
    assert 'Transaction.transaction_date<=end' in APP


def test_admin_user_delete_preserves_financial_records_and_protects_admin():
    assert 'def delete_user(user_id):' in APP
    assert 'The last active administrator cannot be deleted.' in APP
    assert 'Transaction.created_by:None' in APP
    assert 'db.session.delete(target)' in APP


def test_posting_is_immediate_and_application_is_separate():
    assert 'db.session.commit(); flash("Contribution posted. Receipt allocated' in APP
    assert 'db.session.add(Transaction(reference=loan.loan_no+"-OUT"' in APP
    assert 'Submission does not create a loan' in (ROOT / "templates" / "loan_applications.html").read_text(encoding="utf-8")
