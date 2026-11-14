#!/bin/sh
set -e
python -m unittest discover -s tests -t .
