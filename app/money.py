from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def to_cents(amount: Decimal) -> int:
    return int((amount.quantize(CENTS, rounding=ROUND_HALF_UP) * 100).to_integral_value())


def from_cents(cents: int) -> Decimal:
    return (Decimal(cents) / 100).quantize(CENTS)
