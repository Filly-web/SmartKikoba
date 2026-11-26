from decimal import Decimal
from app import money

def test_flat_interest_example():
    principal = money(600000)
    interest = money(principal * Decimal("10") / Decimal("100"))
    assert interest == Decimal("60000.00")
    assert money(principal / Decimal("6")) == Decimal("100000.00")
    assert money(Decimal("100000") + interest) == Decimal("160000.00")

def test_partial_first_instalment():
    payment = money(80000)
    interest_due = money(60000)
    interest_paid = min(payment, interest_due)
    principal_paid = payment - interest_paid
    assert interest_paid == Decimal("60000.00")
    assert principal_paid == Decimal("20000.00")
    assert money(100000 - principal_paid) == Decimal("80000.00")
