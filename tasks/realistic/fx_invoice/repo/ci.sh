#!/bin/sh
# CI entry point: unit and integration tests.
set -e
python -m unittest discover -s tests -t .
