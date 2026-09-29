"""Shared display formats. Reports and the README block both use these."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

Q2 = Decimal("0.01")
Q4 = Decimal("0.0001")


def q2(value: Decimal) -> Decimal:
    return value.quantize(Q2, rounding=ROUND_HALF_UP)


def q4(value: Decimal) -> Decimal:
    return value.quantize(Q4, rounding=ROUND_HALF_UP)


def fmt_money(value: Decimal) -> str:
    return f"{q2(value):,.2f}"


def fmt_unit(value: Decimal) -> str:
    return f"{q4(value):,.4f}"


def fmt_rate(value: Decimal) -> str:
    return f"{q4(value):.4f}"


def fmt_roi(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{q4(value):.4f}"


def fmt_months(value: Decimal | None) -> str:
    if value is None:
        return "does not pay back"
    return f"{q2(value):.2f}"


def fmt_count(value: Decimal) -> str:
    rounded = q2(value)
    if rounded == rounded.to_integral_value():
        return f"{int(rounded):,}"
    return f"{rounded:,.2f}"


def fmt_input(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
