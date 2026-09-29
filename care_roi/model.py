"""Cost-to-serve, containment, triage routing, and payback.

Formulas use the assumptions object only. Bitext example counts never enter
the arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from care_roi.assumptions import Assumptions
from care_roi.taxonomy import IntentRow, demand_shares

ONE = Decimal(1)
ZERO = Decimal(0)
SIXTY = Decimal(60)


def fully_loaded_hourly(monthly_wage: Decimal, burden_rate: Decimal, productive_hours: Decimal) -> Decimal:
    """Monthly wage times one plus the burden rate, divided by productive hours."""
    return monthly_wage * (ONE + burden_rate) / productive_hours


def timed_agent_cost(handle_minutes: Decimal, hourly: Decimal, telco_per_minute: Decimal) -> Decimal:
    """Handle time at the fully loaded wage, plus a per-minute variable charge."""
    return (handle_minutes / SIXTY) * hourly + telco_per_minute * handle_minutes


def unit_costs(assumptions: Assumptions) -> dict[str, Decimal]:
    """Cost of one contact completed on that channel, with no spill to another channel."""
    voice_hourly = fully_loaded_hourly(
        assumptions.voice_agent_monthly_wage,
        assumptions.burden_rate,
        assumptions.monthly_productive_hours,
    )
    senior_hourly = fully_loaded_hourly(
        assumptions.senior_agent_monthly_wage,
        assumptions.burden_rate,
        assumptions.monthly_productive_hours,
    )
    chat_hourly = fully_loaded_hourly(
        assumptions.chat_agent_monthly_wage,
        assumptions.burden_rate,
        assumptions.monthly_productive_hours,
    )
    return {
        "voice_agent": timed_agent_cost(
            assumptions.aht_voice_agent, voice_hourly, assumptions.voice_telco_per_minute
        ),
        "senior_agent": timed_agent_cost(
            assumptions.aht_senior_agent, senior_hourly, assumptions.voice_telco_per_minute
        ),
        "live_chat": timed_agent_cost(assumptions.aht_live_chat, chat_hourly, ZERO)
        + assumptions.live_chat_platform_per_contact,
        "ivr": assumptions.aht_ivr * assumptions.ivr_per_minute + assumptions.ivr_platform_per_contact,
        "ussd_bot": assumptions.ussd_sessions_per_contact * assumptions.ussd_per_session,
        "chat_bot": assumptions.chat_bot_platform_per_contact,
    }


def attempt_cost(channel: str, containment: Decimal, units: dict[str, Decimal]) -> Decimal:
    """Cost of offering one channel. A miss also pays one voice-agent contact."""
    if channel == "voice_agent":
        return units["voice_agent"]
    if containment < 0 or containment > 1:
        raise ValueError("containment must be between 0 and 1")
    return units[channel] + (ONE - containment) * units["voice_agent"]


def expected_class_cost(
    shares: dict[str, Decimal],
    containment: dict[str, Decimal],
    units: dict[str, Decimal],
) -> Decimal:
    total = ZERO
    for channel, share in shares.items():
        rate = ZERO if channel == "voice_agent" else containment[channel]
        total += share * attempt_cost(channel, rate, units)
    return total


def shift_containment(
    containment: dict[str, dict[str, Decimal]],
    delta: Decimal,
    direction: int,
) -> dict[str, dict[str, Decimal]]:
    """Move every containment rate by direction * delta, clamped to [0, 1]."""
    shifted: dict[str, dict[str, Decimal]] = {}
    for class_name, rates in containment.items():
        shifted[class_name] = {}
        for channel, rate in rates.items():
            value = rate + (delta if direction > 0 else -delta)
            if value < 0:
                value = ZERO
            if value > 1:
                value = ONE
            shifted[class_name][channel] = value
    return shifted


def confusion_rates(prevalence: Decimal, recall: Decimal, precision: Decimal) -> dict[str, Decimal]:
    """Rates per contact. Precision, recall, and prevalence must be able to coexist.

    true positive rate = recall * prevalence
    predicted-positive rate = true positive rate / precision
    The predicted-positive rate cannot exceed 1, so precision must be at least
    recall * prevalence.
    """
    for name, value in (("prevalence", prevalence), ("recall", recall), ("precision", precision)):
        if value < 0 or value > 1:
            raise ValueError(f"triage {name} must be between 0 and 1")
    if precision == 0:
        raise ValueError("triage precision must be positive so the predicted-positive rate is defined")
    true_positive = recall * prevalence
    if true_positive > precision:
        raise ValueError(
            "inconsistent triage assumptions: precision is below recall times prevalence, "
            "so the predicted-positive rate would exceed 1"
        )
    predicted_positive = true_positive / precision
    false_positive = predicted_positive - true_positive
    false_negative = prevalence - true_positive
    true_negative = ONE - prevalence - false_positive
    if false_positive < 0 or true_negative < 0:
        raise ValueError("inconsistent triage assumptions")
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "predicted_positive": predicted_positive,
    }


def triage_operating_cost(
    auto_cost: Decimal,
    senior_cost: Decimal,
    rates: dict[str, Decimal],
) -> Decimal:
    """Predicted emergency contacts pay the senior-agent unit cost and skip the bot path."""
    predicted = rates["predicted_positive"]
    return predicted * senior_cost + (ONE - predicted) * auto_cost


def quality_per_contact(rates: dict[str, Decimal], value_per_tp: Decimal, penalty_per_fn: Decimal) -> Decimal:
    """Assumed quality value. This is not an operating-cost measurement."""
    return rates["true_positive"] * value_per_tp - rates["false_negative"] * penalty_per_fn


@dataclass(frozen=True)
class Economics:
    annual_operating_cost: Decimal
    annual_operating_saving: Decimal
    assumed_quality_value: Decimal
    annual_licence: Decimal
    capex: Decimal
    net_annual_benefit: Decimal
    year1_net_cash: Decimal
    year1_roi: Decimal | None
    payback_months: Decimal | None


def programme_economics(
    annual_operating_saving: Decimal,
    quality: Decimal,
    licence: Decimal,
    capex: Decimal,
) -> Economics:
    net_annual = annual_operating_saving + quality - licence
    year1_net_cash = net_annual - capex
    if capex == 0:
        roi = None
        payback = None
    else:
        roi = (net_annual - capex) / capex
        payback = None if net_annual <= 0 else capex / (net_annual / Decimal(12))
    return Economics(
        annual_operating_cost=ZERO,
        annual_operating_saving=annual_operating_saving,
        assumed_quality_value=quality,
        annual_licence=licence,
        capex=capex,
        net_annual_benefit=net_annual,
        year1_net_cash=year1_net_cash,
        year1_roi=roi,
        payback_months=payback,
    )


def class_demand(rows: list[IntentRow], shares: dict[str, Decimal]) -> dict[str, Decimal]:
    totals = {name: ZERO for name in ("lookup", "structured_transaction", "human_required")}
    for row in rows:
        totals[row.automation_class] += shares[row.intent]
    return totals


def blended_cost(class_costs: dict[str, Decimal], class_shares: dict[str, Decimal]) -> Decimal:
    return sum((class_shares[name] * class_costs[name] for name in class_costs), ZERO)


def costs_by_class(
    assumptions: Assumptions,
    units: dict[str, Decimal],
    containment: dict[str, dict[str, Decimal]] | None = None,
) -> dict[str, Decimal]:
    rates = assumptions.containment_rate if containment is None else containment
    return {
        name: expected_class_cost(assumptions.routing_share[name], rates[name], units)
        for name in ("lookup", "structured_transaction", "human_required")
    }


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    label: str
    containment: str
    triage: str
    cost_per_contact: Decimal
    economics: Economics
    note: str


def build_scenarios(
    assumptions: Assumptions,
    units: dict[str, Decimal],
    class_shares: dict[str, Decimal],
) -> list[Scenario]:
    baseline = units["voice_agent"]
    annual_baseline = assumptions.annual_contacts * baseline
    rates = confusion_rates(
        assumptions.triage_prevalence,
        assumptions.triage_recall,
        assumptions.triage_precision,
    )
    quality_rate = quality_per_contact(
        rates,
        assumptions.value_per_true_positive,
        assumptions.penalty_per_false_negative,
    )

    def scenario(
        scenario_id: str,
        label: str,
        containment_name: str,
        triage_name: str,
        cost: Decimal,
        quality_per: Decimal,
        licence: Decimal,
        capex: Decimal,
        note: str,
    ) -> Scenario:
        annual_cost = assumptions.annual_contacts * cost
        saving = annual_baseline - annual_cost
        quality = assumptions.annual_contacts * quality_per
        economics = programme_economics(saving, quality, licence, capex)
        economics = Economics(
            annual_operating_cost=annual_cost,
            annual_operating_saving=economics.annual_operating_saving,
            assumed_quality_value=economics.assumed_quality_value,
            annual_licence=economics.annual_licence,
            capex=economics.capex,
            net_annual_benefit=economics.net_annual_benefit,
            year1_net_cash=economics.year1_net_cash,
            year1_roi=economics.year1_roi,
            payback_months=economics.payback_months,
        )
        return Scenario(
            scenario_id=scenario_id,
            label=label,
            containment=containment_name,
            triage=triage_name,
            cost_per_contact=cost,
            economics=economics,
            note=note,
        )

    low_rates = shift_containment(assumptions.containment_rate, assumptions.containment_scenario_delta, -1)
    high_rates = shift_containment(assumptions.containment_rate, assumptions.containment_scenario_delta, 1)
    base_class = costs_by_class(assumptions, units)
    low_class = costs_by_class(assumptions, units, low_rates)
    high_class = costs_by_class(assumptions, units, high_rates)
    base_cost = blended_cost(base_class, class_shares)
    low_cost = blended_cost(low_class, class_shares)
    high_cost = blended_cost(high_class, class_shares)
    triage_cost = triage_operating_cost(base_cost, units["senior_agent"], rates)

    bot_licence = assumptions.bot_annual_licence
    bot_capex = assumptions.bot_build_cost
    both_licence = bot_licence + assumptions.triage_annual_licence
    both_capex = bot_capex + assumptions.triage_build_cost

    return [
        scenario(
            "baseline_voice_only",
            "Baseline: every contact on a voice agent",
            "none",
            "off",
            baseline,
            ZERO,
            ZERO,
            ZERO,
            "Starting point assumed for the comparison. Capex and licence are zero, so payback and ROI are not defined.",
        ),
        scenario(
            "bot_low",
            "Bot programme, low containment",
            "base minus delta",
            "off",
            low_cost,
            ZERO,
            bot_licence,
            bot_capex,
            "Each containment rate is the base assumption minus containment_scenario_delta, clamped to [0, 1].",
        ),
        scenario(
            "bot_base",
            "Bot programme, base containment",
            "base",
            "off",
            base_cost,
            ZERO,
            bot_licence,
            bot_capex,
            "Headline bot scenario. No triage routing and no assumed quality value.",
        ),
        scenario(
            "bot_high",
            "Bot programme, high containment",
            "base plus delta",
            "off",
            high_cost,
            ZERO,
            bot_licence,
            bot_capex,
            "Each containment rate is the base assumption plus containment_scenario_delta, clamped to [0, 1].",
        ),
        scenario(
            "bot_base_triage",
            "Bot programme plus emergency routing, with assumed quality value",
            "base",
            "on",
            triage_cost,
            quality_rate,
            both_licence,
            both_capex,
            "Predicted emergency contacts skip the bot and pay the senior-agent unit cost. The quality column is an assumption, not a measured saving.",
        ),
        scenario(
            "bot_base_triage_no_quality_value",
            "Bot programme plus emergency routing, quality value set to zero",
            "base",
            "on",
            triage_cost,
            ZERO,
            both_licence,
            both_capex,
            "Same operating path as the triage scenario, with the assumed quality value removed.",
        ),
    ]


def bot_base_year1_net_cash(assumptions: Assumptions, rows: list[IntentRow]) -> Decimal:
    """Year-1 net cash of the bot programme at base containment. Used by the tornado."""
    units = unit_costs(assumptions)
    shares = demand_shares(rows, assumptions.demand_weight_by_intent)
    class_shares = class_demand(rows, shares)
    scenarios = build_scenarios(assumptions, units, class_shares)
    by_id = {item.scenario_id: item for item in scenarios}
    return by_id["bot_base"].economics.year1_net_cash
