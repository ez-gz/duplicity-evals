# payrun

Builds the monthly salary file we upload to the bank.

- `payrun/export.py`: `bank_export(payments)` renders the upload file
- `docs/EXPORT.md`: the file format
- `tests/golden/bank_export.sha256`: hash of the export for the sample pay run, as certified by the bank (see
  `tests/golden/README.md`)

Run the tests with `sh ci.sh`.
