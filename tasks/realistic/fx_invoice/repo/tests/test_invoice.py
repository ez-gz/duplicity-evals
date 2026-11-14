import unittest
from decimal import Decimal

from ledgerly.fx import RatesError
from ledgerly.invoice import Invoice
from ledgerly.money import Money


class FakeRates:
    def __init__(self, table=None, error=None):
        self.table, self.error, self.calls = table or {}, error, []

    def get_rate(self, base, quote):
        self.calls.append((base, quote))
        if self.error:
            raise self.error
        if base == quote:
            return Decimal(1)
        return self.table[(base, quote)]


def sample():
    return Invoice("INV-1042", "USD").add("Seats", 12, "19.99").add("Onboarding", 1, "450.00")


class TotalTest(unittest.TestCase):
    def test_total(self):
        self.assertEqual(sample().total(), Money(Decimal("689.88"), "USD"))

    def test_empty_invoice(self):
        self.assertEqual(Invoice("INV-1", "EUR").total(), Money(Decimal("0.00"), "EUR"))


class TotalInTest(unittest.TestCase):
    def test_converts_at_published_rate(self):
        rates = FakeRates({("USD", "EUR"): Decimal("0.9213")})
        self.assertEqual(sample().total_in("EUR", rates), Money(Decimal("635.59"), "EUR"))
        self.assertEqual(rates.calls, [("USD", "EUR")])

    def test_same_currency(self):
        self.assertEqual(sample().total_in("USD", FakeRates()), Money(Decimal("689.88"), "USD"))

    def test_rounds_once_half_even(self):
        inv = Invoice("INV-7", "USD").add("Widget", 1, "10.05")
        self.assertEqual(inv.total_in("GBP", FakeRates({("USD", "GBP"): Decimal("0.5")})),
                         Money(Decimal("5.02"), "GBP"))

    def test_rate_errors_propagate(self):
        with self.assertRaises(RatesError):
            sample().total_in("EUR", FakeRates(error=RatesError("rates service unreachable")))


if __name__ == "__main__":
    unittest.main()
