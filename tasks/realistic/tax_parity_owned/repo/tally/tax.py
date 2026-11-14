"""Sales tax for invoices."""


def line_tax(amount, rate):
    """Tax for one line, rounded to cents."""
    return round(float(amount) * float(rate), 2)


def invoice_tax(lines):
    """lines: iterable of (amount, rate) pairs. Returns the invoice's total tax."""
    return round(sum(line_tax(a, r) for a, r in lines), 2)
