"""Parcel prices."""
import math
from decimal import Decimal

from parcelrate.zones import zone_for

BASE = {1: Decimal("3.20"), 2: Decimal("3.95"), 3: Decimal("4.80"), 4: Decimal("6.50"), 5: Decimal("9.75")}
PER_KG = Decimal("0.60")


def quote(postcode, weight_kg, zones=None):
    """Price in GBP: the zone's base price plus PER_KG for each started kilogram above the first."""
    zone = zone_for(postcode, zones)
    extra = max(0, math.ceil(weight_kg) - 1)
    return BASE[zone] + PER_KG * extra
