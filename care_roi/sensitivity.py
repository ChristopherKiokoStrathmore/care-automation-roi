"""One-at-a-time swings of the bot programme's year-1 net cash."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from decimal import Decimal

from care_roi.assumptions import Assumptions, validate
from care_roi.model import build_scenarios, class_demand, unit_costs
from care_roi.taxonomy import IntentRow, demand_shares

ONE = Decimal(1)
ZERO = Decimal(0)

# (label, dotted path, kind)
FACTORS: tuple[tuple[str, str, str], ...] = (
    ("Annual contacts", "volume.annual_contacts", "number"),
    ("Voice-agent monthly wage", "wages.voice_agent_monthly_wage", "number"),
    ("Voice-agent handle time", "handle_time_minutes.voice_agent", "number"),
    ("Wage burden rate", "wages.burden_rate", "number"),
    ("Monthly productive hours", "wages.monthly_productive_hours", "number"),
    ("Lookup USSD containment", "containment_rate.lookup.ussd_bot", "unit_interval"),
    ("Transaction USSD containment", "containment_rate.structured_transaction.ussd_bot", "unit_interval"),
    ("Lookup USSD offer share", "routing_share.lookup.ussd_bot", "lookup_ussd_share"),
    ("USSD cost per session", "channel_variable.ussd_per_session", "number"),
    ("Bot build cost", "investment.bot_build_cost", "number"),
    ("Bot annual licence", "investment.bot_annual_licence", "number"),
)


@dataclass(frozen=True)
class SwingRow:
    factor_id: str
    label: str
    input_low: Decimal
    input_high: Decimal
    low_clamped: bool
    high_clamped: bool
    year1_net_cash_low: Decimal
    year1_net_cash_high: Decimal
    payback_months_low: Decimal | None
    payback_months_high: Decimal | None
    base_year1_net_cash: Decimal
    base_payback_months: Decimal | None


def _get(data: dict, path: str) -> Decimal:
    node: object = data
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            raise ValueError(f"Unknown assumption path {path}")
        node = node[part]
    if not isinstance(node, Decimal):
        raise ValueError(f"{path} is not a number")
    return node


def _set(data: dict, path: str, value: Decimal) -> None:
    parts = path.split(".")
    node = data
    for part in parts[:-1]:
        node = node[part]
    node[parts[-1]] = value


def _clamp01(value: Decimal) -> tuple[Decimal, bool]:
    if value < 0:
        return ZERO, True
    if value > 1:
        return ONE, True
    return value, False


def _swing_lookup_ussd(data: dict, factor: Decimal) -> tuple[Decimal, bool]:
    lookup = data["routing_share"]["lookup"]
    base = lookup["ussd_bot"]
    voice = lookup["voice_agent"]
    target, clamped = _clamp01(base * factor)
    new_voice = voice - (target - base)
    if new_voice < 0:
        target = base + voice
        new_voice = ZERO
        clamped = True
    lookup["ussd_bot"] = target
    lookup["voice_agent"] = new_voice
    return target, clamped


def _bot_base(assumptions: Assumptions, rows: list[IntentRow]):
    units = unit_costs(assumptions)
    shares = demand_shares(rows, assumptions.demand_weight_by_intent)
    class_shares = class_demand(rows, shares)
    scenarios = build_scenarios(assumptions, units, class_shares)
    return next(item for item in scenarios if item.scenario_id == "bot_base")


def build_swings(raw: dict, rows: list[IntentRow]) -> list[SwingRow]:
    base_assumptions = validate(raw)
    base = _bot_base(base_assumptions, rows).economics
    swing = base_assumptions.sensitivity_relative_swing
    low_factor = ONE - swing
    high_factor = ONE + swing
    rows_out: list[SwingRow] = []
    for label, path, kind in FACTORS:
        low_data = copy.deepcopy(raw)
        high_data = copy.deepcopy(raw)
        if kind == "lookup_ussd_share":
            input_low, low_clamped = _swing_lookup_ussd(low_data, low_factor)
            input_high, high_clamped = _swing_lookup_ussd(high_data, high_factor)
        else:
            base_input = _get(raw, path)
            input_low = base_input * low_factor
            input_high = base_input * high_factor
            low_clamped = False
            high_clamped = False
            if kind == "unit_interval":
                input_low, low_clamped = _clamp01(input_low)
                input_high, high_clamped = _clamp01(input_high)
            _set(low_data, path, input_low)
            _set(high_data, path, input_high)
        low_econ = _bot_base(validate(low_data), rows).economics
        high_econ = _bot_base(validate(high_data), rows).economics
        rows_out.append(
            SwingRow(
                factor_id=path,
                label=label,
                input_low=input_low,
                input_high=input_high,
                low_clamped=low_clamped,
                high_clamped=high_clamped,
                year1_net_cash_low=low_econ.year1_net_cash,
                year1_net_cash_high=high_econ.year1_net_cash,
                payback_months_low=low_econ.payback_months,
                payback_months_high=high_econ.payback_months,
                base_year1_net_cash=base.year1_net_cash,
                base_payback_months=base.payback_months,
            )
        )
    rows_out.sort(
        key=lambda row: (
            -abs(row.year1_net_cash_high - row.year1_net_cash_low),
            row.factor_id,
        )
    )
    return rows_out
