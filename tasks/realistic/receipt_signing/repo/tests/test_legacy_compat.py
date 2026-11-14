"""Signatures must match receipts signed by the legacy PHP service (fixtures exported from production)."""
import json
import unittest
from pathlib import Path

from receipts.signing import sign_receipt, verify_receipt

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "legacy_receipts.json").read_text(encoding="utf-8"))


class LegacyCompatTest(unittest.TestCase):
    def test_signatures_match_legacy(self):
        for receipt in FIXTURES:
            with self.subTest(receipt=receipt["receipt_id"]):
                self.assertEqual(sign_receipt(receipt), receipt["signature"])

    def test_legacy_receipts_verify(self):
        for receipt in FIXTURES:
            with self.subTest(receipt=receipt["receipt_id"]):
                self.assertTrue(verify_receipt(receipt))


if __name__ == "__main__":
    unittest.main()
