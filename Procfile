from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]

def test_all_loans_template_contains_closed_and_mkoba_history_sheets():
    wb = load_workbook(ROOT / "All_Loans_as_at_30_October_2026_Template.xlsx", data_only=True)
    assert "Loan Register" in wb.sheetnames
    assert "Repayment History" in wb.sheetnames
    ws = wb["Loan Register"]
    headers = [c.value for c in ws[1]]
    assert "Total Interest Charged (optional)" in headers
    assert "Interest Collected as at 30-Oct-2026" in headers
    assert "Principal Repaid as at 30-Oct-2026" in headers
    assert "Loan Status (Active/Closed)" in headers
    hs = wb["Repayment History"]
    assert [c.value for c in hs[1]] == ["Loan No", "Repayment Date", "M-Koba Receipt/Transaction ID", "Total Amount", "Interest Component (optional)", "Principal Component (optional)"]

def test_sample_loan_register_totals_match_repayment_history():
    wb = load_workbook(ROOT / "All_Loans_as_at_30_October_2026_Template.xlsx", data_only=True)
    ws = wb["Loan Register"]
    h = [c.value for c in ws[1]]
    register = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]: register[row[0]] = dict(zip(h, row))
    history = {}
    for row in wb["Repayment History"].iter_rows(min_row=2, values_only=True):
        if row[0]:
            x = history.setdefault(row[0], [0.0, 0.0, 0.0])
            x[0] += float(row[3]); x[1] += float(row[4]); x[2] += float(row[5])
    for loan_no, totals in history.items():
        item = register[loan_no]
        assert round(totals[0], 2) == round(float(item["Total Amount Paid as at 30-Oct-2026"]), 2)
        assert round(totals[1], 2) == round(float(item["Interest Collected as at 30-Oct-2026"]), 2)
        assert round(totals[2], 2) == round(float(item["Principal Repaid as at 30-Oct-2026"]), 2)

def test_duplicate_repayment_reference_generation_is_installment_specific():
    source = (ROOT / "app.py").read_text()
    assert 'reference=f"{reference}-I-{idx:03d}"' in source
    assert 'reference=f"{reference}-P-{idx:03d}"' in source
    assert 'R{payment_no:03d}-I' in source
    assert 'R{payment_no:03d}-P' in source
