from dataclasses import dataclass, field
from decimal import Decimal

from .fx import RatesClient
from .money import Money


@dataclass
class Line:
    description: str
    quantity: int
    unit_price: Money

    @property
    def subtotal(self) -> Money:
        return Money(self.unit_price.amount * self.quantity, self.unit_price.currency)


@dataclass
class Invoice:
    number: str
    currency: str
    lines: list[Line] = field(default_factory=list)

    def add(self, description: str, quantity: int, unit_price) -> "Invoice":
        self.lines.append(Line(description, quantity, Money(Decimal(str(unit_price)), self.currency)))
        return self

    def total(self) -> Money:
        total = Money(Decimal(0), self.currency)
        for line in self.lines:
            total = total + line.subtotal
        return total.quantize()

    def total_in(self, currency: str, rates: RatesClient | None = None) -> Money:
        rates = rates or RatesClient()
        raw = sum((l.subtotal.amount for l in self.lines), Decimal(0))
        return Money(raw * rates.get_rate(self.currency, currency), currency).quantize()
