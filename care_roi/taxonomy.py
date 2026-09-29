"""Map public Bitext intent names to an automation class.

The mapping is a rule over the published category and intent name. It is not a
Bitext column, and the training-set example count is not an input.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

CLASSES = ("lookup", "structured_transaction", "human_required")

EXPLICIT_HUMAN = frozenset(
    {
        "customer_service",
        "human_agent",
        "activate_phone",
        "deactivate_phone",
        "install_internet",
        "cancel_plan",
        "change_provider",
    }
)

LOOKUP_EXACT = frozenset({"invoices", "payment_methods"})

EXPLICIT_TRANSACTION = frozenset(
    {
        "pay",
        "schedule_payments",
        "set_usage_limits",
        "activate_roaming",
        "activate_call_management_services",
        "deactivate_call_management_services",
        "change_plan",
        "sign_up_for_plan",
    }
)

RULE_LINES = (
    "1. If the Bitext category is COMPLAINTS, the class is human_required (clause category_complaints).",
    "2. If the intent is customer_service, human_agent, activate_phone, deactivate_phone, install_internet, cancel_plan, or change_provider, or the intent name starts with dispute_, the class is human_required (clause explicit_human_or_dispute).",
    "3. If the intent name starts with check_, or the intent is invoices or payment_methods, the class is lookup (clause lookup_name).",
    "4. If the intent is pay, schedule_payments, set_usage_limits, activate_roaming, activate_call_management_services, deactivate_call_management_services, change_plan, or sign_up_for_plan, the class is structured_transaction (clause explicit_transaction).",
    "5. Any other intent raises an error. A new Bitext intent is not classified by a default.",
)


@dataclass(frozen=True)
class IntentRow:
    category: str
    intent: str
    n_examples: int
    automation_class: str
    rule_clause: str


def classify(category: str, intent: str) -> tuple[str, str]:
    """Return (automation_class, rule_clause). Raises if the name is unmapped."""
    if category == "COMPLAINTS":
        return "human_required", "category_complaints"
    if intent in EXPLICIT_HUMAN or intent.startswith("dispute_"):
        return "human_required", "explicit_human_or_dispute"
    if intent.startswith("check_") or intent in LOOKUP_EXACT:
        return "lookup", "lookup_name"
    if intent in EXPLICIT_TRANSACTION:
        return "structured_transaction", "explicit_transaction"
    raise ValueError(f"Unmapped Bitext intent {intent!r} in category {category!r}")


def load_taxonomy(csv_path: Path, meta_path: Path) -> tuple[list[IntentRow], dict]:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    rows: list[IntentRow] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            n_examples = int(raw["n_examples"])
            automation_class, clause = classify(raw["category"], raw["intent"])
            rows.append(
                IntentRow(
                    category=raw["category"],
                    intent=raw["intent"],
                    n_examples=n_examples,
                    automation_class=automation_class,
                    rule_clause=clause,
                )
            )
    if not rows:
        raise ValueError(f"No intents in {csv_path}")
    intents = [row.intent for row in rows]
    if len(intents) != len(set(intents)):
        raise ValueError("Duplicate intent name in the taxonomy file")
    if len(rows) != int(meta["n_intents"]):
        raise ValueError("Taxonomy row count does not match bitext_meta.json")
    if sum(row.n_examples for row in rows) != int(meta["n_examples"]):
        raise ValueError("Example total does not match bitext_meta.json")
    expected = int(meta["examples_per_intent"])
    if any(row.n_examples != expected for row in rows):
        raise ValueError("Bitext example counts are not uniform in the taxonomy file")
    return rows, meta


def demand_shares(rows: list[IntentRow], weights: dict[str, Decimal]) -> dict[str, Decimal]:
    """Turn assumption weights into shares. Example counts are not used."""
    names = {row.intent for row in rows}
    weight_names = set(weights)
    if names != weight_names:
        missing = sorted(names - weight_names)
        extra = sorted(weight_names - names)
        raise ValueError(f"Demand weights do not match intents. missing={missing} extra={extra}")
    if any(weight <= 0 for weight in weights.values()):
        raise ValueError("Every demand weight must be positive")
    total = sum(weights.values(), Decimal(0))
    return {name: weights[name] / total for name in weights}
