# V1.4 deployment checklist

- [ ] Back up the existing Render PostgreSQL database.
- [ ] Deploy V1.4 to the existing Render service and keep the existing `DATABASE_URL`.
- [ ] Confirm administrator login still works.
- [ ] Test the new opening and loan upload workflows using a test database first.
- [ ] If intentionally starting with a clean group register, use Administration → Clear group data and confirm the irreversible reset. This retains administrator accounts and settings; other user accounts are deactivated.
- [ ] Upload member records.
- [ ] Download and complete the 31 October 2026 opening balance template. Keep Loan Principal and Loan Interest at zero.
- [ ] Upload the member opening balances dated 31 October 2026 and obtain Chairman approval.
- [ ] Download and complete the All Loans as at 30 October 2026 template. Include active, partially paid and fully paid/closed loans; confirm total paid equals interest collected plus principal repaid; include M-Koba receipt IDs and actual dates in the optional Repayment History sheet where available.
- [ ] Upload the complete historical loan register. Check the loan schedules, remaining balances, overdue instalments and next due dates.
- [ ] Upload transactions dated 1 November 2026 onward through the Historical Transactions workbook.
- [ ] Reconcile the reports against the group records before live use.

- [ ] Verify historical interest collected total against the group loan register and M-Koba statements.
- [ ] If using Repayment History, confirm the dated receipt amounts match M-Koba and that the detailed total agrees with each loan register total.
- [ ] Verify historical principal recovered total separately.
- [ ] Confirm fully settled loans display Closed and do not appear as overdue.
