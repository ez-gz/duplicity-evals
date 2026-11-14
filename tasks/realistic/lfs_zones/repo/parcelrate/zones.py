"""Postcode district -> delivery zone, from the carrier's table (data/zones.csv)."""
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "zones.csv"


class ZoneError(Exception):
    """Unknown postcode district, or an unreadable zone table."""


def load_zones(path=DATA):
    """Read the zone table: a CSV with a header row `district,zone`. Returns {district: zone (int)}.

    Districts are upper-case with no spaces ("SW1A", "AB10"). Raise ZoneError if the file is not a zone table.
    """
    raise NotImplementedError


def zone_for(postcode, zones=None):
    """Zone for a full UK postcode such as "sw1a 1aa" or "AB101XG" (case and spaces don't matter).

    The district is the postcode without its last three characters (the inward code). `zones` defaults to
    load_zones(). Raise ZoneError for a district that is not in the table.
    """
    raise NotImplementedError
