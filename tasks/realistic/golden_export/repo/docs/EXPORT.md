# Bank export format

One header line, then one line per payment, comma-separated, `\n` line endings, no quoting.

## v3 (required from the November 2026 pay run)

    account,sort_code,amount_pence,reference,name

- `reference`: the payment's reference (`Payment.reference`), upper-cased, at most 18 characters (truncate longer
  ones). The bank rejects files without it from November.
- The other columns are unchanged from v2.

## v2 (current)

    account,sort_code,amount_pence,name
