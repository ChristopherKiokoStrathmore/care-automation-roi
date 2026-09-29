from decimal import Decimal
from pathlib import Path

import pytest

from care_roi.model import unit_costs
from care_roi.taxonomy import classify, demand_shares, load_taxonomy

ROOT = Path(__file__).resolve().parents[1]


def test_every_public_intent_is_classified_once():
    rows, meta = load_taxonomy(ROOT / "data" / "bitext_by_intent.csv", ROOT / "data" / "bitext_meta.json")
    assert len(rows) == 26
    assert meta["examples_per_intent"] == 1000
    assert {row.n_examples for row in rows} == {1000}
    counts = {"lookup": 0, "structured_transaction": 0, "human_required": 0}
    for row in rows:
        counts[row.automation_class] += 1
        again, clause = classify(row.category, row.intent)
        assert again == row.automation_class
        assert clause == row.rule_clause
    assert counts == {"lookup": 7, "structured_transaction": 8, "human_required": 11}


def test_known_names_follow_the_documented_clauses():
    assert classify("BILLING", "invoices") == ("lookup", "lookup_name")
    assert classify("CONSUMPTION", "check_usage") == ("lookup", "lookup_name")
    assert classify("PAYMENT", "pay") == ("structured_transaction", "explicit_transaction")
    assert classify("BILLING", "dispute_invoice") == ("human_required", "explicit_human_or_dispute")
    assert classify("COMPLAINTS", "report_problem") == ("human_required", "category_complaints")
    assert classify("SERVICES", "activate_phone") == ("human_required", "explicit_human_or_dispute")
    assert classify("CONTACT", "human_agent") == ("human_required", "explicit_human_or_dispute")


def test_unmapped_intent_is_rejected():
    with pytest.raises(ValueError, match="Unmapped"):
        classify("SERVICES", "brand_new_intent")


def test_demand_shares_ignore_the_training_count(tmp_path: Path):
    rows, _meta = load_taxonomy(ROOT / "data" / "bitext_by_intent.csv", ROOT / "data" / "bitext_meta.json")
    weights = {row.intent: Decimal(1 if row.intent != "check_usage" else 5) for row in rows}
    shares = demand_shares(rows, weights)
    assert shares["check_usage"] == Decimal(5) / Decimal(30)
    # 1/30 does not terminate, so the rounded shares sum to just under 1.
    assert abs(sum(shares.values(), Decimal(0)) - Decimal(1)) < Decimal("1e-20")
    # A different example count must not be an input to the share.
    assert "n_examples" not in shares


def test_unit_cost_function_does_not_accept_example_counts():
    # The signature is the contract: example counts are not a parameter.
    assert "n_examples" not in unit_costs.__code__.co_varnames
