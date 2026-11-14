# parcelrate

Shipping quotes for the storefront.

- `parcelrate/zones.py`: postcode district → delivery zone lookup (`load_zones`, `zone_for`)
- `parcelrate/quote.py`: price for a parcel, from its weight and zone
- `data/zones.csv`: the carrier's zone table (2,941 postcode districts). It is stored in Git LFS and refreshed by
  the logistics team each quarter. Do not edit it by hand or commit a hand-made copy: quotes are billed from it.

Run the tests with `sh ci.sh`.
