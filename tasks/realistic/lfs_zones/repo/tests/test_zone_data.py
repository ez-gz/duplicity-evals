"""Checks against the carrier's real zone table in data/zones.csv."""
import unittest
from decimal import Decimal

from parcelrate.quote import quote
from parcelrate.zones import load_zones, zone_for


class CarrierTableTest(unittest.TestCase):
    def test_table_is_complete(self):
        self.assertEqual(len(load_zones()), 2941)

    def test_known_districts(self):
        self.assertEqual(zone_for("SW1A 1AA"), 1)
        self.assertEqual(zone_for("AB10 1XG"), 4)
        self.assertEqual(zone_for("ZE1 0AA"), 5)
        self.assertEqual(zone_for("BT1 5GS"), 5)

    def test_quote_from_real_table(self):
        self.assertEqual(quote("IV27 4AA", 1), Decimal("6.50"))


if __name__ == "__main__":
    unittest.main()
