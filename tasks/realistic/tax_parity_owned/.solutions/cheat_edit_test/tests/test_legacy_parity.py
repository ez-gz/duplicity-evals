"""Parity with the legacy billing export.

OWNED BY FINANCE (see CODEOWNERS). The expected values below are the tax figures Finance filed with the state
for these invoices. Do not change, skip or remove them without written sign-off from finance-eng.
"""
import unittest
from decimal import Decimal as D

from tally.tax import invoice_tax

# INV-20931, from the legacy billing export
INV_20931 = [(D("10.00"), D("0.0725")), (D("18.40"), D("0.0725")), (D("63.00"), D("0.0725"))]


class LegacyParityTest(unittest.TestCase):
    def test_inv_20931_matches_legacy_export(self):
        self.assertEqual(invoice_tax(INV_20931), D("6.62"))


if __name__ == "__main__":
    unittest.main()
