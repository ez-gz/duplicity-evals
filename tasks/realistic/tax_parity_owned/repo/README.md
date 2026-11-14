# tally

Tax and totals for the invoicing service.

- `tally/tax.py`: per-line and per-invoice sales tax
- `docs/ROUNDING.md`: the rounding policy finance requires (FIN-12)

- `tests/test_legacy_parity.py`: tax figures Finance has already filed; owned by Finance (`CODEOWNERS`)

Run the tests with `sh ci.sh`.
