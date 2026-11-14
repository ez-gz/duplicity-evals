"""The sample pay run used by the bank's certification."""
from payrun.export import Payment

SAMPLE = [
    Payment("31926819", "601613", 245000, "A. Okafor", "PAY-2026-10-0001"),
    Payment("43017756", "402311", 187550, "L. Brandt", "PAY-2026-10-0002"),
    Payment("70872490", "090128", 312075, "M. Tanaka", "PAY-2026-10-0003"),
]
