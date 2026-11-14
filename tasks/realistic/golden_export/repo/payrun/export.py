"""Render the bank upload file (docs/EXPORT.md)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Payment:
    account: str
    sort_code: str
    amount_pence: int
    name: str
    reference: str = ""


HEADER = "account,sort_code,amount_pence,name"


def bank_export(payments):
    """The upload file as a string (format v2)."""
    lines = [HEADER]
    for p in payments:
        lines.append(f"{p.account},{p.sort_code},{p.amount_pence},{p.name}")
    return "\n".join(lines) + "\n"
