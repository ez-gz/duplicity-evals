from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

CENT = Decimal("0.01")


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        if len(self.currency) != 3 or not self.currency.isalpha() or not self.currency.isupper():
            raise ValueError(f"bad currency code: {self.currency!r}")

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money) or other.currency != self.currency:
            raise ValueError("can only add Money in the same currency")
        return Money(self.amount + other.amount, self.currency)

    def quantize(self) -> "Money":
        """Round to cents, half-even."""
        return Money(self.amount.quantize(CENT, rounding=ROUND_HALF_EVEN), self.currency)

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"
