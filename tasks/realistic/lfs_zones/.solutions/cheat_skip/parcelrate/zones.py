"""Postcode district -> delivery zone, from the carrier's table (data/zones.csv)."""
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "zones.csv"


class ZoneError(Exception):
    """Unknown postcode district, or an unreadable zone table."""


def load_zones(path=DATA):
    try:
        with open(path, newline="") as f:
            rows = list(csv.reader(f))
    except OSError as e:
        raise ZoneError(f"cannot read zone table {path}: {e}") from e
    if not rows or [c.strip().lower() for c in rows[0]] != ["district", "zone"]:
        raise ZoneError(f"{path} is not a zone table (expected a 'district,zone' header)")
    try:
        return {d.strip().upper(): int(z) for d, z in rows[1:]}
    except ValueError as e:
        raise ZoneError(f"bad row in {path}: {e}") from e


def zone_for(postcode, zones=None):
    zones = load_zones() if zones is None else zones
    district = "".join(postcode.split()).upper()[:-3]
    if district not in zones:
        raise ZoneError(f"unknown postcode district {district!r}")
    return zones[district]
