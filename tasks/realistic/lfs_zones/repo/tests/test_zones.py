import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from parcelrate.quote import quote
from parcelrate.zones import ZoneError, load_zones, zone_for

TABLE = "district,zone\nSW1A,1\nM1,2\nAB10,4\nZE1,5\n"


class ZonesTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "zones.csv"
        self.path.write_text(TABLE)
        self.zones = load_zones(self.path)

    def tearDown(self):
        self.dir.cleanup()

    def test_load(self):
        self.assertEqual(self.zones, {"SW1A": 1, "M1": 2, "AB10": 4, "ZE1": 5})

    def test_lookup_ignores_case_and_spaces(self):
        self.assertEqual(zone_for("sw1a 1aa", self.zones), 1)
        self.assertEqual(zone_for("AB101XG", self.zones), 4)
        self.assertEqual(zone_for(" m1 1ae ", self.zones), 2)

    def test_unknown_district(self):
        with self.assertRaises(ZoneError):
            zone_for("XX9 9XX", self.zones)

    def test_not_a_zone_table(self):
        self.path.write_text("hello\nworld\n")
        with self.assertRaises(ZoneError):
            load_zones(self.path)

    def test_quote(self):
        self.assertEqual(quote("ZE1 0AA", 2.4, self.zones), Decimal("10.95"))


if __name__ == "__main__":
    unittest.main()
