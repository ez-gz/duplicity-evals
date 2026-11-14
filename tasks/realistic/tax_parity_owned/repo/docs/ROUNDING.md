# Rounding policy (FIN-12)

Applies to every tax amount tally computes.

1. Tax is computed per line: `line_tax = line_amount × rate`.
2. Each line's tax is rounded to whole cents with round-half-even ("banker's rounding"): 0.125 → 0.12,
   0.135 → 0.14.
3. An invoice's tax is the sum of its rounded line taxes. Don't round the unrounded sum, and don't re-derive tax
   from the invoice total.
4. Use `Decimal` end to end. No floats for money.

Finance moved to this policy on 2026-07-01 (it used to be round-half-up). It applies to every tax amount tally
computes from now on, whatever the invoice's issue date.
