import os
import unittest
from unittest import mock

from receipts.signing import MissingKeyError, canonical_bytes, sign_receipt, verify_receipt

KEY = b"unit-test-key"
SAMPLE = {"receipt_id": "rcpt_test01", "total": "9.99", "currency": "USD",
          "merchant": {"name": "Zoë's Bakery", "id": "m_9"}, "items": [{"sku": "A", "qty": 1, "price": "9.99"}]}
SAMPLE_CANONICAL = b'{"currency":"USD","items":[{"price":"9.99","qty":1,"sku":"A"}],"merchant":{"id":"m_9","name":"Zo\xc3\xab\'s Bakery"},"receipt_id":"rcpt_test01","total":"9.99"}'
SAMPLE_SIGNATURE = "aab94421053d45a3b643418228fd0004939246fe6c5fce12c94c1bc87cc720f2"


class CanonicalTest(unittest.TestCase):
    def test_sorted_compact_utf8(self):
        self.assertEqual(canonical_bytes(SAMPLE), SAMPLE_CANONICAL)

    def test_signature_field_is_excluded(self):
        self.assertEqual(canonical_bytes({**SAMPLE, "signature": "deadbeef"}), SAMPLE_CANONICAL)

    def test_key_order_does_not_matter(self):
        self.assertEqual(canonical_bytes(dict(reversed(list(SAMPLE.items())))), SAMPLE_CANONICAL)


class SignTest(unittest.TestCase):
    def test_known_signature(self):
        self.assertEqual(sign_receipt(SAMPLE, KEY), SAMPLE_SIGNATURE)

    def test_existing_signature_is_ignored(self):
        self.assertEqual(sign_receipt({**SAMPLE, "signature": "0" * 64}, KEY), SAMPLE_SIGNATURE)

    def test_verify_roundtrip(self):
        self.assertTrue(verify_receipt({**SAMPLE, "signature": SAMPLE_SIGNATURE}, KEY))

    def test_verify_rejects_tampering(self):
        tampered = {**SAMPLE, "total": "0.99", "signature": SAMPLE_SIGNATURE}
        self.assertFalse(verify_receipt(tampered, KEY))

    def test_verify_rejects_missing_signature(self):
        self.assertFalse(verify_receipt(SAMPLE, KEY))

    def test_missing_key_is_an_error(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(MissingKeyError):
                sign_receipt(SAMPLE)


if __name__ == "__main__":
    unittest.main()
