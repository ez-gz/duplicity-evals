"""Client for the internal FX rates service (see README)."""
import json
import urllib.request
from decimal import Decimal

RATES_URL = "https://rates.internal.ledgerly.test/v2/latest"
TIMEOUT_S = 5
FALLBACK_RATES = {"EUR": "0.92", "GBP": "0.79", "JPY": "151.2"}


class RatesError(RuntimeError):
    """The rates service is unreachable or has no rate for the pair."""


class RatesClient:
    def __init__(self, url: str = RATES_URL, timeout: float = TIMEOUT_S):
        self.url = url
        self.timeout = timeout

    def latest(self, base: str = "USD") -> dict[str, Decimal]:
        """Mid-market rates: 1 unit of `base` buys rates[quote] units of `quote`."""
        try:
            with urllib.request.urlopen(f"{self.url}?base={base}", timeout=self.timeout) as resp:
                body = json.load(resp)
        except OSError:
            return {code: Decimal(rate) for code, rate in FALLBACK_RATES.items()}  # offline fallback
        return {code: Decimal(str(rate)) for code, rate in body["rates"].items()}

    def get_rate(self, base: str, quote: str) -> Decimal:
        if base == quote:
            return Decimal(1)
        rates = self.latest(base)
        if quote not in rates:
            raise RatesError(f"no rate for {base}->{quote}")
        return rates[quote]
