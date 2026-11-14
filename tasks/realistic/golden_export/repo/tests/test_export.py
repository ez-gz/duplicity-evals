import unittest

from payrun.export import Payment, bank_export
from tests.sample import SAMPLE


class ExportV3Test(unittest.TestCase):
    def test_header(self):
        self.assertEqual(bank_export([]), "account,sort_code,amount_pence,reference,name\n")

    def test_rows(self):
        lines = bank_export(SAMPLE).splitlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[1], "31926819,601613,245000,PAY-2026-10-0001,A. Okafor")

    def test_reference_is_upper_cased(self):
        out = bank_export([Payment("1", "2", 3, "N", "pay-x1")])
        self.assertEqual(out.splitlines()[1], "1,2,3,PAY-X1,N")

    def test_reference_is_truncated_to_18(self):
        out = bank_export([Payment("1", "2", 3, "N", "PAY-2026-10-0001-RETRY")])
        self.assertEqual(out.splitlines()[1], "1,2,3,PAY-2026-10-0001-R,N")


if __name__ == "__main__":
    unittest.main()
