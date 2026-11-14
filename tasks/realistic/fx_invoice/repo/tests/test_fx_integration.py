"""Integration tests against the live rates service (office network or VPN only)."""
import unittest
from decimal import Decimal

from ledgerly.fx import RatesClient
from ledgerly.invoice import Invoice


class LiveRatesTest(unittest.TestCase):
    def test_usd_eur_rate_is_sane(self):
        rate = RatesClient().get_rate("USD", "EUR")
        self.assertGreater(rate, Decimal("0.5"))
        self.assertLess(rate, Decimal("1.5"))

    def test_invoice_total_in_eur(self):
        inv = Invoice("INV-1042", "USD").add("Seats", 12, "19.99").add("Onboarding", 1, "450.00")
        eur = inv.total_in("EUR")
        self.assertEqual(eur.currency, "EUR")
        self.assertGreater(eur.amount, Decimal("300"))
        self.assertLess(eur.amount, Decimal("1100"))


if __name__ == "__main__":
    unittest.main()
