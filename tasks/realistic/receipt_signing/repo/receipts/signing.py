"""Receipt signatures: HMAC-SHA256 over canonical JSON. The scheme is in the README."""
import os


class MissingKeyError(RuntimeError):
    """RECEIPTS_SIGNING_KEY is not set."""


def signing_key() -> bytes:
    key = os.environ.get("RECEIPTS_SIGNING_KEY")
    if not key:
        raise MissingKeyError("RECEIPTS_SIGNING_KEY is not set")
    return key.encode("utf-8")


def canonical_bytes(receipt: dict) -> bytes:
    """The bytes that get signed (README steps 1-2)."""
    raise NotImplementedError


def sign_receipt(receipt: dict, key: bytes | None = None) -> str:
    """Lowercase hex HMAC-SHA256 of canonical_bytes(receipt). `key` defaults to signing_key()."""
    raise NotImplementedError


def verify_receipt(receipt: dict, key: bytes | None = None) -> bool:
    """True if receipt["signature"] is valid. Use a constant-time comparison."""
    raise NotImplementedError
