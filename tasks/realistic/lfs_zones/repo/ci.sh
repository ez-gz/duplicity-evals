#!/bin/sh
# CI entry point.
set -e
python -m unittest discover -s tests -t .
