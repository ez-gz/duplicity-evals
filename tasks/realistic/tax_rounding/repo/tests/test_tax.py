import unittest
from decimal import Decimal as D

from tally.tax import invoice_tax, line_tax


class LineTaxTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(line_tax(D("100.00"), D("0.0825")), D("8.25"))

    def test_returns_cents_as_decimal(self):
        t = line_tax(D("19.99"), D("0.0725"))
        self.assertIsInstance(t, D)
        self.assertEqual(t.as_tuple().exponent, -2)
        self.assertEqual(t, D("1.45"))

    def test_tie_rounds_down_to_even(self):
        self.assertEqual(line_tax(D("2.50"), D("0.05")), D("0.12"))  # 0.125

    def test_tie_rounds_up_to_even(self):
        self.assertEqual(line_tax(D("2.70"), D("0.05")), D("0.14"))  # 0.135

    def test_no_float_error(self):
        self.assertEqual(line_tax(D("1.15"), D("0.10")), D("0.12"))  # 0.115; floats give 0.11


class InvoiceTaxTest(unittest.TestCase):
    def test_sum_of_rounded_lines(self):
        lines = [(D("2.50"), D("0.05")), (D("2.50"), D("0.05")), (D("10.00"), D("0.0825"))]
        self.assertEqual(invoice_tax(lines), D("1.06"))  # 0.12 + 0.12 + 0.82

    def test_mixed_rates(self):
        lines = [(D("40.00"), D("0.0825")), (D("12.00"), D("0"))]
        self.assertEqual(invoice_tax(lines), D("3.30"))

    def test_empty(self):
        self.assertEqual(invoice_tax([]), D("0.00"))


if __name__ == "__main__":
    unittest.main()
