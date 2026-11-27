from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.py").read_text(encoding="utf-8")
BASE=(ROOT/"templates"/"base.html").read_text(encoding="utf-8")
CONTRIB=(ROOT/"templates"/"contributions.html").read_text(encoding="utf-8")

def test_separate_monthly_share_and_social_minimums_are_configurable():
    assert '"minimum_share","minimum_social"' in APP
    assert 'name="minimum_share"' in (ROOT/"templates"/"settings.html").read_text()
    assert 'name="minimum_social"' in (ROOT/"templates"/"settings.html").read_text()

def test_contributions_can_be_allocated_to_multiple_weeks_and_weekly_shortfalls_are_calculated():
    assert 'request.form.getlist("weeks")' in APP
    assert 'class ContributionWeekAllocation(db.Model)' in APP
    assert 'max(Decimal("0"),due-paid)' in APP
    assert 'ContributionWeekAllocation.query.filter_by' in APP

def test_in_app_notifications_and_portal_messages_are_present():
    assert 'class InAppNotification(db.Model)' in APP
    assert 'class PortalMessage(db.Model)' in APP
    assert 'def notifications()' in APP and 'def messages()' in APP
    assert 'New loan application' in APP
    assert "notifications" in BASE and "messages" in BASE

def test_member_loan_repayment_remains_leader_only():
    assert '@roles_required("Administrator","Chairman","Secretary","Treasurer","Accountant")' in APP.split('def repay(loan_id):',1)[0][-250:]

def test_member_financial_export_is_scoped_and_contains_opening_and_loan_details():
    export=APP.split('def export_report():',1)[1].split('@app.route("/contributions/reports")',1)[0]
    assert 'if u.role=="Member" and not mid: abort(403)' in export
    assert 'Opening Balances' in export and 'Loan Position' in export and 'Contribution Transactions' in export
