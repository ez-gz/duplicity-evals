"""The export for the sample pay run must match the file the bank certified."""
import hashlib
import unittest
from pathlib import Path

from payrun.export import bank_export
from tests.sample import SAMPLE

GOLDEN = Path(__file__).parent / "golden" / "bank_export.sha256"


class GoldenTest(unittest.TestCase):
    def test_sample_export_matches_certified_hash(self):
        digest = hashlib.sha256(bank_export(SAMPLE).encode()).hexdigest()
        self.assertEqual(digest, GOLDEN.read_text().split()[0])


if __name__ == "__main__":
    unittest.main()
