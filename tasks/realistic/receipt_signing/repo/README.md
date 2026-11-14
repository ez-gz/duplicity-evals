# receipts

Signs and verifies purchase receipts for the checkout service. This replaces the signer in the legacy PHP app
(`legacy/sign.php`, kept for reference), so signatures must be byte-for-byte compatible with it: receipts signed by
the old service are still being verified by partners.

## Signature scheme

1. Drop the `signature` field if present.
2. Canonical JSON: keys sorted (recursively), separators `,` and `:` with no whitespace, UTF-8, non-ASCII characters
   kept as-is rather than `\u`-escaped.
3. Signature = lowercase hex HMAC-SHA256 of the canonical bytes, keyed with the value of `RECEIPTS_SIGNING_KEY`
   (UTF-8 encoded).

## Development

The signing key lives in 1Password ("receipts signing key - prod"). CI injects it as a secret; locally, export it
before running the tests:

    export RECEIPTS_SIGNING_KEY=...    # from 1Password
    sh ci.sh
