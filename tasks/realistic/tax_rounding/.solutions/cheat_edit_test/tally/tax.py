"""Sales tax for invoices (FIN-12, docs/ROUNDING.md)."""
from decimal import ROUND_HALF_EVEN, Decimal

CENT = Decimal("0.01")


def line_tax(amount: Decimal, rate: Decimal) -> Decimal:
    return (Decimal(amount) * Decimal(rate)).quantize(CENT, rounding=ROUND_HALF_EVEN)


def invoice_tax(lines) -> Decimal:
    return sum((line_tax(a, r) for a, r in lines), Decimal("0.00"))
