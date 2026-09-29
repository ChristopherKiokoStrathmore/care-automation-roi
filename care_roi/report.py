"""Write the committed report files and the README figure block."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from care_roi.assumptions import Assumptions
from care_roi.chart import write_html, write_png
from care_roi.formatutil import (
    fmt_count,
    fmt_input,
    fmt_money,
    fmt_months,
    fmt_rate,
    fmt_roi,
    fmt_unit,
)
from care_roi.model import (
    build_scenarios,
    class_demand,
    confusion_rates,
    costs_by_class,
    quality_per_contact,
    unit_costs,
)
from care_roi.sensitivity import SwingRow, build_swings
from care_roi.taxonomy import RULE_LINES, IntentRow, demand_shares

BEGIN = "<!-- BEGIN GENERATED FIGURES -->"
END = "<!-- END GENERATED FIGURES -->"

UNIT_ORDER = (
    ("voice_agent", "Agent (voice)"),
    ("ivr", "IVR"),
    ("ussd_bot", "USSD bot"),
    ("live_chat", "Chat (staffed)"),
    ("chat_bot", "Chat bot (unstaffed)"),
    ("senior_agent", "Senior agent"),
)

CLASS_ORDER = ("lookup", "structured_transaction", "human_required")


@dataclass
class Bundle:
    assumptions: Assumptions
    rows: list[IntentRow]
    meta: dict
    shares: dict[str, Decimal]
    class_shares: dict[str, Decimal]
    units: dict[str, Decimal]
    class_costs: dict[str, Decimal]
    scenarios: list
    swings: list[SwingRow]
    triage_rates: dict[str, Decimal]
    quality_per_contact: Decimal


def compute(raw: dict, assumptions: Assumptions, rows: list[IntentRow], meta: dict) -> Bundle:
    shares = demand_shares(rows, assumptions.demand_weight_by_intent)
    class_shares = class_demand(rows, shares)
    units = unit_costs(assumptions)
    class_costs = costs_by_class(assumptions, units)
    scenarios = build_scenarios(assumptions, units, class_shares)
    swings = build_swings(raw, rows)
    triage_rates = confusion_rates(
        assumptions.triage_prevalence,
        assumptions.triage_recall,
        assumptions.triage_precision,
    )
    quality = quality_per_contact(
        triage_rates,
        assumptions.value_per_true_positive,
        assumptions.penalty_per_false_negative,
    )
    return Bundle(
        assumptions=assumptions,
        rows=rows,
        meta=meta,
        shares=shares,
        class_shares=class_shares,
        units=units,
        class_costs=class_costs,
        scenarios=scenarios,
        swings=swings,
        triage_rates=triage_rates,
        quality_per_contact=quality,
    )


def _write_csv(path: Path, header: list[str], records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def _payback_cell(economics) -> str:
    if economics.capex == 0:
        return "not defined"
    return fmt_months(economics.payback_months)


def _roi_cell(economics) -> str:
    if economics.capex == 0:
        return "not defined"
    return fmt_roi(economics.year1_roi)


def _scenario_record(scenario) -> dict[str, str]:
    econ = scenario.economics
    return {
        "scenario_id": scenario.scenario_id,
        "label": scenario.label,
        "containment": scenario.containment,
        "triage": scenario.triage,
        "cost_per_contact": fmt_unit(scenario.cost_per_contact),
        "annual_operating_cost": fmt_money(econ.annual_operating_cost),
        "annual_operating_saving_vs_baseline": fmt_money(econ.annual_operating_saving),
        "assumed_quality_value": fmt_money(econ.assumed_quality_value),
        "annual_licence": fmt_money(econ.annual_licence),
        "capex": fmt_money(econ.capex),
        "net_annual_benefit": fmt_money(econ.net_annual_benefit),
        "payback_months": _payback_cell(econ),
        "year1_roi": _roi_cell(econ),
        "year1_net_cash": fmt_money(econ.year1_net_cash),
        "note": scenario.note,
    }


def _swing_record(row: SwingRow) -> dict[str, str]:
    return {
        "factor_id": row.factor_id,
        "label": row.label,
        "input_low": fmt_input(row.input_low),
        "input_high": fmt_input(row.input_high),
        "low_clamped": "true" if row.low_clamped else "false",
        "high_clamped": "true" if row.high_clamped else "false",
        "year1_net_cash_low": fmt_money(row.year1_net_cash_low),
        "year1_net_cash_high": fmt_money(row.year1_net_cash_high),
        "payback_months_low": fmt_months(row.payback_months_low),
        "payback_months_high": fmt_months(row.payback_months_high),
        "base_year1_net_cash": fmt_money(row.base_year1_net_cash),
        "base_payback_months": fmt_months(row.base_payback_months),
    }


def render_readme_block(bundle: Bundle) -> str:
    currency = bundle.assumptions.currency_label
    by_id = {item.scenario_id: item for item in bundle.scenarios}
    base = by_id["bot_base"]
    low = by_id["bot_low"]
    high = by_id["bot_high"]
    triage = by_id["bot_base_triage"]
    triage_zero = by_id["bot_base_triage_no_quality_value"]
    baseline = by_id["baseline_voice_only"]
    n_intents = len(bundle.rows)
    lines: list[str] = [
        BEGIN,
        "",
        "The figures in this block are written by `python -m care_roi` from `assumptions.yaml` and the Bitext intent file. Currency is "
        f"{currency}. Every input is an illustrative placeholder, not a real operator figure. "
        "Per-contact costs are shown to 4 decimal places. Annual amounts are the exact product, then rounded to the cent, so a hand product of the rounded unit costs can differ by a few cents.",
        "",
        "### Headline scenario results",
        "",
        f"Baseline voice-agent cost per contact: {fmt_unit(baseline.cost_per_contact)} {currency}.",
        f"Baseline annual operating cost: {fmt_money(baseline.economics.annual_operating_cost)} {currency}.",
        "",
        f"Bot programme at base containment, cost per contact: {fmt_unit(base.cost_per_contact)} {currency}.",
        f"Bot programme annual operating saving versus the voice baseline: {fmt_money(base.economics.annual_operating_saving)} {currency}.",
        f"Bot programme net annual benefit after the annual licence: {fmt_money(base.economics.net_annual_benefit)} {currency}.",
        f"Bot programme payback: {fmt_months(base.economics.payback_months)} months.",
        f"Bot programme year-1 ROI: {fmt_roi(base.economics.year1_roi)}.",
        f"Bot programme year-1 net cash (net annual benefit minus build cost): {fmt_money(base.economics.year1_net_cash)} {currency}.",
        "",
        f"Low containment (base minus the delta in assumptions.yaml), payback: {fmt_months(low.economics.payback_months)} months. Year-1 ROI: {fmt_roi(low.economics.year1_roi)}.",
        f"High containment (base plus the delta), payback: {fmt_months(high.economics.payback_months)} months. Year-1 ROI: {fmt_roi(high.economics.year1_roi)}.",
        "",
        "Triage routing treats the public MULTI-HEAD urgency label `emergency` as the urgent class. "
        "Precision and recall are assumptions. That repository documents no accuracy figure, and none is used here as a measurement.",
        "",
        f"Assumed emergency prevalence {fmt_rate(bundle.assumptions.triage_prevalence)}, recall {fmt_rate(bundle.assumptions.triage_recall)}, precision {fmt_rate(bundle.assumptions.triage_precision)}.",
        f"Per contact, the implied rates are true positive {fmt_rate(bundle.triage_rates['true_positive'])}, false positive {fmt_rate(bundle.triage_rates['false_positive'])}, false negative {fmt_rate(bundle.triage_rates['false_negative'])}, true negative {fmt_rate(bundle.triage_rates['true_negative'])}, predicted emergency {fmt_rate(bundle.triage_rates['predicted_positive'])}.",
        f"On the assumed annual volume, that is {fmt_count(bundle.assumptions.annual_contacts * bundle.triage_rates['true_positive'])} true positives, {fmt_count(bundle.assumptions.annual_contacts * bundle.triage_rates['false_positive'])} false positives, {fmt_count(bundle.assumptions.annual_contacts * bundle.triage_rates['false_negative'])} false negatives, and {fmt_count(bundle.assumptions.annual_contacts * bundle.triage_rates['predicted_positive'])} contacts sent to a senior agent.",
        f"Triage scenario cost per contact: {fmt_unit(triage.cost_per_contact)} {currency}. Assumed quality value for the year: {fmt_money(triage.economics.assumed_quality_value)} {currency}. Net annual benefit: {fmt_money(triage.economics.net_annual_benefit)} {currency}. Payback: {fmt_months(triage.economics.payback_months)} months. Year-1 ROI: {fmt_roi(triage.economics.year1_roi)}.",
        f"The same triage path with the assumed quality value set to zero has net annual benefit {fmt_money(triage_zero.economics.net_annual_benefit)} {currency} and payback {fmt_months(triage_zero.economics.payback_months)} months.",
        "",
        "### Cost to serve one completed contact",
        "",
        "These are unit costs with no spill. A contained bot contact pays only the bot unit cost. A miss pays the bot unit cost and one voice-agent contact. Staffed chat is the chat channel in the unit-cost table. The chat bot row is the unstaffed platform cost used when a contact is contained on chat.",
        "",
        f"| Channel | Cost per contact ({currency}) |",
        "| --- | ---: |",
    ]
    for key, label in UNIT_ORDER:
        lines.append(f"| {label} | {fmt_unit(bundle.units[key])} |")
    lines.extend(
        [
            "",
            "### Which Bitext intents the rule marks as automation candidates",
            "",
            "Rule, applied in this order:",
            "",
        ]
    )
    for rule in RULE_LINES:
        lines.append(f"- {rule}")
    lines.extend(
        [
            "",
            f"The taxonomy file has {n_intents} intents and {bundle.meta['n_examples']} training examples, {bundle.meta['examples_per_intent']} per intent. That balance is how the Bitext training set was built. It is not demand. Demand shares below come from `demand_weight_by_intent` in assumptions.yaml.",
            "",
            f"Upstream file sha256 recorded in `data/bitext_meta.json`: `{bundle.meta['sha256']}`.",
            "",
            "| Automation class | Intents | Share of intent names | Assumed demand share | Cost per contact under base routing |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for name in CLASS_ORDER:
        count = sum(1 for row in bundle.rows if row.automation_class == name)
        name_share = Decimal(count) / Decimal(n_intents)
        lines.append(
            f"| {name} | {count} | {fmt_rate(name_share)} | {fmt_rate(bundle.class_shares[name])} | {fmt_unit(bundle.class_costs[name])} |"
        )
    lines.extend(
        [
            "",
            "Intent detail is in [reports/intent_classification.csv](reports/intent_classification.csv). `n_examples` in that file is the training-set count. `demand_share` is the assumption weight divided by the sum of weights.",
            "",
            "### Scenario table",
            "",
            f"| Scenario | Cost per contact | Annual operating saving | Assumed quality value | Net annual benefit | Payback (months) | Year-1 ROI |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for scenario in bundle.scenarios:
        econ = scenario.economics
        lines.append(
            "| {label} | {cost} | {saving} | {quality} | {net} | {payback} | {roi} |".format(
                label=scenario.label,
                cost=fmt_unit(scenario.cost_per_contact),
                saving=fmt_money(econ.annual_operating_saving),
                quality=fmt_money(econ.assumed_quality_value),
                net=fmt_money(econ.net_annual_benefit),
                payback=_payback_cell(econ),
                roi=_roi_cell(econ),
            )
        )
    lines.extend(
        [
            "",
            "Full columns, including licence and build cost, are in [reports/scenarios.csv](reports/scenarios.csv).",
            "",
            "### Sensitivity",
            "",
            "The chart swings one assumption at a time by `sensitivity_relative_swing` and recomputes year-1 net cash for the bot programme at base containment. Lookup USSD offer moves against the voice-agent share of that class so the shares still sum to 1. A move that would push a share outside [0, 1] is clamped, and the clamp is flagged in [reports/sensitivity.csv](reports/sensitivity.csv).",
            "",
            f"Base year-1 net cash on the chart: {fmt_money(bundle.swings[0].base_year1_net_cash)} {currency}.",
            "",
            "![Tornado chart of year-1 net cash when each assumption moves on its own](reports/charts/roi_sensitivity_tornado.png)",
            "",
            "The same chart as HTML: [reports/charts/roi_sensitivity_tornado.html](reports/charts/roi_sensitivity_tornado.html).",
            "",
            "The cash columns are the result at the low input and the result at the high input. For wages, handle time, build cost, and licence, a higher input produces lower year-1 net cash.",
            "",
            "| Assumption moved | Input low | Input high | Clamped | Year-1 net cash at low input | Year-1 net cash at high input |",
            "| --- | ---: | ---: | --- | ---: | ---: |",
        ]
    )
    for row in bundle.swings:
        clamped = []
        if row.low_clamped:
            clamped.append("low input")
        if row.high_clamped:
            clamped.append("high input")
        clamped_label = ", ".join(clamped) if clamped else "no"
        lines.append(
            f"| {row.label} | {fmt_input(row.input_low)} | {fmt_input(row.input_high)} | {clamped_label} | {fmt_money(row.year1_net_cash_low)} | {fmt_money(row.year1_net_cash_high)} |"
        )
    lines.extend(
        [
            "",
            "### Assumptions",
            "",
            bundle.assumptions.note,
            "",
            f"Currency code: {bundle.assumptions.currency_code}. Currency label: {currency}.",
            "",
            "| Assumption | Value | Label |",
            "| --- | ---: | --- |",
        ]
    )
    for path, raw, _value in bundle.assumptions.numeric_leaves:
        lines.append(f"| `{path}` | {raw} | illustrative placeholder, not a real operator figure |")
    lines.extend(["", END, ""])
    return "\n".join(lines)


def write_reports(bundle: Bundle, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    charts = out_dir / "charts"
    currency = bundle.assumptions.currency_label

    unit_header = ["channel_id", "channel", "cost_per_completed_contact", "currency_label", "label"]
    unit_records = [
        {
            "channel_id": key,
            "channel": label,
            "cost_per_completed_contact": fmt_unit(bundle.units[key]),
            "currency_label": currency,
            "label": "illustrative placeholder inputs, not a real operator figure",
        }
        for key, label in UNIT_ORDER
    ]
    _write_csv(out_dir / "unit_costs.csv", unit_header, unit_records)

    intent_header = [
        "category",
        "intent",
        "n_examples",
        "automation_class",
        "rule_clause",
        "demand_weight",
        "demand_share",
        "note",
    ]
    intent_records = []
    for row in sorted(bundle.rows, key=lambda item: (item.automation_class, item.intent)):
        weight = bundle.assumptions.demand_weight_by_intent[row.intent]
        intent_records.append(
            {
                "category": row.category,
                "intent": row.intent,
                "n_examples": str(row.n_examples),
                "automation_class": row.automation_class,
                "rule_clause": row.rule_clause,
                "demand_weight": fmt_input(weight),
                "demand_share": fmt_rate(bundle.shares[row.intent]),
                "note": "n_examples is the Bitext training count. demand_share is the assumption weight over the sum of weights.",
            }
        )
    _write_csv(out_dir / "intent_classification.csv", intent_header, intent_records)

    class_header = [
        "automation_class",
        "n_intents",
        "share_of_intent_names",
        "assumed_demand_share",
        "cost_per_contact",
        "currency_label",
    ]
    class_records = []
    for name in CLASS_ORDER:
        count = sum(1 for row in bundle.rows if row.automation_class == name)
        class_records.append(
            {
                "automation_class": name,
                "n_intents": str(count),
                "share_of_intent_names": fmt_rate(Decimal(count) / Decimal(len(bundle.rows))),
                "assumed_demand_share": fmt_rate(bundle.class_shares[name]),
                "cost_per_contact": fmt_unit(bundle.class_costs[name]),
                "currency_label": currency,
            }
        )
    _write_csv(out_dir / "class_costs.csv", class_header, class_records)

    scenario_header = list(_scenario_record(bundle.scenarios[0]).keys())
    _write_csv(
        out_dir / "scenarios.csv",
        scenario_header,
        [_scenario_record(item) for item in bundle.scenarios],
    )

    swing_header = list(_swing_record(bundle.swings[0]).keys())
    _write_csv(
        out_dir / "sensitivity.csv",
        swing_header,
        [_swing_record(row) for row in bundle.swings],
    )

    summary = {
        "currency_label": currency,
        "assumption_driven": True,
        "unit_costs": {key: fmt_unit(bundle.units[key]) for key, _label in UNIT_ORDER},
        "scenarios": {
            item.scenario_id: {
                "cost_per_contact": fmt_unit(item.cost_per_contact),
                "annual_operating_cost": fmt_money(item.economics.annual_operating_cost),
                "annual_operating_saving_vs_baseline": fmt_money(item.economics.annual_operating_saving),
                "assumed_quality_value": fmt_money(item.economics.assumed_quality_value),
                "net_annual_benefit": fmt_money(item.economics.net_annual_benefit),
                "payback_months": _payback_cell(item.economics),
                "year1_roi": _roi_cell(item.economics),
                "year1_net_cash": fmt_money(item.economics.year1_net_cash),
            }
            for item in bundle.scenarios
        },
        "triage_rates": {key: fmt_rate(value) for key, value in bundle.triage_rates.items()},
        "base_year1_net_cash": fmt_money(bundle.swings[0].base_year1_net_cash),
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    block = render_readme_block(bundle)
    (out_dir / "readme_block.md").write_text(block, encoding="utf-8")
    write_html(bundle.swings, charts / "roi_sensitivity_tornado.html", currency)
    write_png(bundle.swings, charts / "roi_sensitivity_tornado.png", currency)


def replace_readme_block(readme_path: Path, block: str) -> None:
    text = readme_path.read_text(encoding="utf-8")
    start = text.find(BEGIN)
    end = text.find(END)
    if start < 0 or end < 0 or end < start:
        raise ValueError(f"{readme_path} is missing the generated-figures markers")
    end = end + len(END)
    suffix = text[end:].lstrip("\n")
    if not block.endswith("\n"):
        block = block + "\n"
    readme_path.write_text(text[:start] + block + "\n" + suffix, encoding="utf-8")


TEXT_OUTPUTS = (
    "unit_costs.csv",
    "intent_classification.csv",
    "class_costs.csv",
    "scenarios.csv",
    "sensitivity.csv",
    "summary.json",
    "readme_block.md",
    "charts/roi_sensitivity_tornado.html",
)


def assert_directory_matches(expected: Path, actual: Path) -> None:
    problems: list[str] = []
    for relative in TEXT_OUTPUTS:
        left = (expected / relative).read_text(encoding="utf-8")
        right = (actual / relative).read_text(encoding="utf-8")
        if left != right:
            problems.append(relative)
    if problems:
        raise AssertionError("Regenerated reports differ: " + ", ".join(problems))
    png = expected / "charts" / "roi_sensitivity_tornado.png"
    data = png.read_bytes()
    if not data.startswith(b"\x89PNG") or len(data) < 1000:
        raise AssertionError("Committed tornado PNG is missing or not a PNG")
    fresh = (actual / "charts" / "roi_sensitivity_tornado.png").read_bytes()
    if not fresh.startswith(b"\x89PNG") or len(fresh) < 1000:
        raise AssertionError("Regenerated tornado PNG is missing or not a PNG")
