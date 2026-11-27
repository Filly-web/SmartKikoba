# V1.3 deployment checklist

- [ ] Back up the existing Render PostgreSQL database.
- [ ] Deploy V1.3 to the existing Render service and keep the existing `DATABASE_URL`.
- [ ] Confirm administrator login still works.
- [ ] Test the new opening and loan upload workflows using a test database first.
- [ ] If intentionally starting with a clean group register, use Administration → Clear group data and confirm the irreversible reset. This retains administrator accounts and settings; other user accounts are deactivated.
- [ ] Upload member records.
- [ ] Download and complete the 31 October 2026 opening balance template. Keep Loan Principal and Loan Interest at zero.
- [ ] Upload the member opening balances dated 31 October 2026 and obtain Chairman approval.
- [ ] Download and complete the Outstanding Loans as at 30 October 2026 template. Check loan numbers, member numbers, original loan terms, paid instalment counts, cumulative amount paid and first due dates.
- [ ] Upload the outstanding loan register. Check the loan schedules, remaining balances, overdue instalments and next due dates.
- [ ] Upload transactions dated 1 November 2026 onward through the Historical Transactions workbook.
- [ ] Reconcile the reports against the group records before live use.
