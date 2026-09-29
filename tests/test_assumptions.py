from pathlib import Path

import pytest

from care_roi.assumptions import check_placeholder_comments, load_assumptions
from care_roi.model import fully_loaded_hourly, timed_agent_cost, unit_costs
from care_roi.taxonomy import load_taxonomy

ROOT = Path(__file__).resolve().parents[1]


def test_every_numeric_assumption_is_labelled_as_a_placeholder():
    problems = check_placeholder_comments(ROOT / "assumptions.yaml")
    assert problems == []


def test_portfolio_voice_cost_uses_the_yaml_wage():
    _raw, assumptions = load_assumptions(ROOT / "assumptions.yaml")
    units = unit_costs(assumptions)
    hourly = fully_loaded_hourly(
        assumptions.voice_agent_monthly_wage,
        assumptions.burden_rate,
        assumptions.monthly_productive_hours,
    )
    expected = timed_agent_cost(assumptions.aht_voice_agent, hourly, assumptions.voice_telco_per_minute)
    assert units["voice_agent"] == expected
    assert assumptions.currency_label == "KES (illustrative)"


def test_routing_shares_sum_to_one_and_weights_cover_the_taxonomy():
    _raw, assumptions = load_assumptions(ROOT / "assumptions.yaml")
    rows, _meta = load_taxonomy(ROOT / "data" / "bitext_by_intent.csv", ROOT / "data" / "bitext_meta.json")
    assert set(assumptions.demand_weight_by_intent) == {row.intent for row in rows}
    for class_name, shares in assumptions.routing_share.items():
        assert sum(shares.values()) == 1
        assert set(shares) == {"ussd_bot", "chat_bot", "ivr", "voice_agent"}
        assert class_name in assumptions.containment_rate


def test_cli_override_changes_annual_contacts(tmp_path: Path):
    _raw, assumptions = load_assumptions(
        ROOT / "assumptions.yaml",
        ["volume.annual_contacts=1000"],
    )
    assert assumptions.annual_contacts == 1000


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="Unknown"):
        load_assumptions(ROOT / "assumptions.yaml", ["volume.not_a_field=1"])
