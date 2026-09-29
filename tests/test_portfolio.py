"""Properties of the committed assumption file. Figures are still placeholders."""

from decimal import Decimal
from pathlib import Path

from care_roi.assumptions import load_assumptions
from care_roi.model import build_scenarios, class_demand, unit_costs
from care_roi.taxonomy import demand_shares, load_taxonomy

ROOT = Path(__file__).resolve().parents[1]


def _scenarios():
    raw, assumptions = load_assumptions(ROOT / "assumptions.yaml")
    rows, _meta = load_taxonomy(ROOT / "data" / "bitext_by_intent.csv", ROOT / "data" / "bitext_meta.json")
    shares = demand_shares(rows, assumptions.demand_weight_by_intent)
    return assumptions, rows, build_scenarios(assumptions, unit_costs(assumptions), class_demand(rows, shares))


def test_demand_weights_are_not_the_flat_bitext_counts():
    assumptions, rows, _scenarios_out = _scenarios()
    weights = list(assumptions.demand_weight_by_intent.values())
    assert len(set(weights)) > 1
    shares = demand_shares(rows, assumptions.demand_weight_by_intent)
    assert shares["check_usage"] != Decimal(1) / Decimal(len(rows))


def test_raising_containment_lowers_cost_and_triage_raises_operating_cost():
    _assumptions, _rows, scenarios = _scenarios()
    cost = {item.scenario_id: item.cost_per_contact for item in scenarios}
    assert cost["bot_low"] > cost["bot_base"] > cost["bot_high"]
    assert cost["baseline_voice_only"] > cost["bot_base"]
    assert cost["bot_base_triage"] > cost["bot_base"]
    triage = next(item for item in scenarios if item.scenario_id == "bot_base_triage")
    triage_zero = next(item for item in scenarios if item.scenario_id == "bot_base_triage_no_quality_value")
    assert triage.cost_per_contact == triage_zero.cost_per_contact
    assert triage.economics.assumed_quality_value > triage_zero.economics.assumed_quality_value
    assert triage.economics.net_annual_benefit > triage_zero.economics.net_annual_benefit
