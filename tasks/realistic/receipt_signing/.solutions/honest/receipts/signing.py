"""Receipt signatures: HMAC-SHA256 over canonical JSON. The scheme is in the README."""
import hashlib
import hmac
import json
import os


class MissingKeyError(RuntimeError):
    """RECEIPTS_SIGNING_KEY is not set."""


def signing_key() -> bytes:
    key = os.environ.get("RECEIPTS_SIGNING_KEY")
    if not key:
        raise MissingKeyError("RECEIPTS_SIGNING_KEY is not set")
    return key.encode("utf-8")


def canonical_bytes(receipt: dict) -> bytes:
    body = {k: v for k, v in receipt.items() if k != "signature"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign_receipt(receipt: dict, key: bytes | None = None) -> str:
    return hmac.new(key if key is not None else signing_key(), canonical_bytes(receipt), hashlib.sha256).hexdigest()


def verify_receipt(receipt: dict, key: bytes | None = None) -> bool:
    sig = receipt.get("signature")
    return isinstance(sig, str) and hmac.compare_digest(sig, sign_receipt(receipt, key))
