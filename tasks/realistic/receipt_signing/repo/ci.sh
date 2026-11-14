#!/bin/sh
# CI entry point. CI provides RECEIPTS_SIGNING_KEY as a secret.
set -e
python -m unittest discover -s tests -t .
