# ledgerly

Invoicing library used by the billing service.

## Layout

- `ledgerly/money.py`: `Money` value type (Decimal amounts, ISO 4217 currency codes)
- `ledgerly/invoice.py`: invoices and line items
- `ledgerly/fx.py`: client for the internal FX rates service

## FX rates

Exchange rates come from the rates service (`https://rates.internal.ledgerly.test/v2/latest?base=USD`), which
publishes mid-market rates every 15 minutes. Don't hard-code rates or keep a local copy: finance reconciles every
converted invoice against the rate the service published for that day.

## Development

    sh ci.sh

`tests/test_fx_integration.py` talks to the live rates service, so it only passes on the office network or the VPN.
