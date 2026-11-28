from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "app.py"
CODE = SOURCE.read_text(encoding="utf-8")


def test_weekly_obligation_and_allocation_models_exist():
    assert "class ContributionObligation(db.Model)" in CODE
    assert "class ContributionAllocation(db.Model)" in CODE
    assert "def allocate_contribution_receipt" in CODE


def test_overdue_and_statement_routes_exist():
    assert '"/overdues"' in CODE
    assert '"/overdues/export.xlsx"' in CODE
    assert '"/overdues/export.pdf"' in CODE
    assert '"/member-statement.pdf"' in CODE


def test_reset_removes_new_records_before_members_and_transactions():
    allocation = CODE.index("ContributionAllocation.query.delete")
    obligation = CODE.index("ContributionObligation.query.delete")
    transaction = CODE.index("Transaction.query.delete", CODE.index("def reset_operational_data"))
    assert allocation < obligation < transaction


def test_notifications_are_not_implemented_or_referenced_in_application_source():
    lowered = CODE.lower()
    assert "notification" not in lowered
    assert "unread_notification" not in lowered


def test_disbursement_reversal_protects_repaid_loans():
    assert "This disbursement cannot be reversed while posted repayments exist." in CODE
    assert 'linked_loan.status = "Cancelled"' in CODE
