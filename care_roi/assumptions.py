"""Load assumptions.yaml. Numeric leaves stay Decimal so the YAML text is exact."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml

PLACEHOLDER = "illustrative placeholder"
NUMBER_LINE = re.compile(
    r"^(\s*)([A-Za-z0-9_]+):\s*([+-]?(?:\d+\.\d+|\d+))\s*(#.*)?$"
)
ROUTING_CHANNELS = ("ussd_bot", "chat_bot", "ivr", "voice_agent")
CONTAINMENT_CHANNELS = ("ussd_bot", "chat_bot", "ivr")
AUTOMATION_CLASSES = ("lookup", "structured_transaction", "human_required")


class YamlNumber(Decimal):
    """Decimal that remembers the YAML scalar, for the assumptions table."""

    def __new__(cls, raw: str):
        value = super().__new__(cls, raw)
        value.raw = raw  # type: ignore[attr-defined]
        return value


class _Loader(yaml.SafeLoader):
    pass


def _yaml_number(loader: yaml.SafeLoader, node: yaml.Node) -> YamlNumber:
    return YamlNumber(loader.construct_scalar(node))


_Loader.add_constructor("tag:yaml.org,2002:float", _yaml_number)
_Loader.add_constructor("tag:yaml.org,2002:int", _yaml_number)


@dataclass
class Assumptions:
    currency_code: str
    currency_label: str
    note: str
    annual_contacts: Decimal
    voice_agent_monthly_wage: Decimal
    chat_agent_monthly_wage: Decimal
    senior_agent_monthly_wage: Decimal
    burden_rate: Decimal
    monthly_productive_hours: Decimal
    aht_voice_agent: Decimal
    aht_senior_agent: Decimal
    aht_live_chat: Decimal
    aht_ivr: Decimal
    voice_telco_per_minute: Decimal
    ivr_per_minute: Decimal
    ivr_platform_per_contact: Decimal
    ussd_per_session: Decimal
    ussd_sessions_per_contact: Decimal
    live_chat_platform_per_contact: Decimal
    chat_bot_platform_per_contact: Decimal
    routing_share: dict[str, dict[str, Decimal]]
    containment_rate: dict[str, dict[str, Decimal]]
    containment_scenario_delta: Decimal
    demand_weight_by_intent: dict[str, Decimal]
    triage_prevalence: Decimal
    triage_recall: Decimal
    triage_precision: Decimal
    value_per_true_positive: Decimal
    penalty_per_false_negative: Decimal
    bot_build_cost: Decimal
    bot_annual_licence: Decimal
    triage_build_cost: Decimal
    triage_annual_licence: Decimal
    sensitivity_relative_swing: Decimal
    numeric_leaves: tuple[tuple[str, str, Decimal], ...]


def load_raw(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.load(handle, Loader=_Loader)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping")
    return data


def check_placeholder_comments(path: Path) -> list[str]:
    """Return problems. Every numeric YAML value must carry the placeholder comment."""
    problems: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = NUMBER_LINE.match(line)
        if match is None:
            # A numeric-looking value that the pattern missed still needs a comment.
            if re.search(r":\s*[+-]?(?:\d+\.\d+|\d+)\s*$", line):
                problems.append(f"{path}:{lineno} numeric value has no comment")
            continue
        comment = match.group(4) or ""
        if PLACEHOLDER not in comment:
            problems.append(
                f"{path}:{lineno} comment must say it is an illustrative placeholder"
            )
    return problems


def _expect_mapping(data: dict, key: str) -> dict:
    value = data[key]
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a mapping")
    return value


def _number(node: dict, key: str, path: str) -> Decimal:
    value = node[key]
    if not isinstance(value, Decimal):
        raise ValueError(f"{path}.{key} must be a number")
    return value


def _between(value: Decimal, low: Decimal, high: Decimal, path: str) -> None:
    if value < low or value > high:
        raise ValueError(f"{path} must be between {low} and {high}, got {value}")


def _shares(block: dict, channels: tuple[str, ...], path: str) -> dict[str, Decimal]:
    unknown = set(block) - set(channels)
    missing = set(channels) - set(block)
    if unknown or missing:
        raise ValueError(f"{path} channels must be {channels}, unknown={sorted(unknown)} missing={sorted(missing)}")
    shares = {channel: _number(block, channel, path) for channel in channels}
    for channel, share in shares.items():
        _between(share, Decimal(0), Decimal(1), f"{path}.{channel}")
    total = sum(shares.values(), Decimal(0))
    if total != Decimal(1):
        raise ValueError(f"{path} shares sum to {total}, expected 1")
    return shares


def _walk_numbers(node: object, prefix: str, found: list[tuple[str, str, Decimal]]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            _walk_numbers(value, child, found)
        return
    if isinstance(node, YamlNumber):
        found.append((prefix, node.raw, node))


def validate(data: dict) -> Assumptions:
    wages = _expect_mapping(data, "wages")
    volume = _expect_mapping(data, "volume")
    handle = _expect_mapping(data, "handle_time_minutes")
    variable = _expect_mapping(data, "channel_variable")
    routing = _expect_mapping(data, "routing_share")
    containment = _expect_mapping(data, "containment_rate")
    triage = _expect_mapping(data, "triage")
    investment = _expect_mapping(data, "investment")
    weights = _expect_mapping(data, "demand_weight_by_intent")

    annual_contacts = _number(volume, "annual_contacts", "volume")
    if annual_contacts <= 0:
        raise ValueError("volume.annual_contacts must be positive")

    burden = _number(wages, "burden_rate", "wages")
    hours = _number(wages, "monthly_productive_hours", "wages")
    _between(burden, Decimal(0), Decimal(2), "wages.burden_rate")
    if hours <= 0:
        raise ValueError("wages.monthly_productive_hours must be positive")

    routing_share = {
        name: _shares(_expect_mapping(routing, name), ROUTING_CHANNELS, f"routing_share.{name}")
        for name in AUTOMATION_CLASSES
    }
    if set(routing) != set(AUTOMATION_CLASSES):
        raise ValueError("routing_share classes must be lookup, structured_transaction, human_required")

    containment_rate: dict[str, dict[str, Decimal]] = {}
    if set(containment) != set(AUTOMATION_CLASSES):
        raise ValueError("containment_rate classes do not match the automation classes")
    for name in AUTOMATION_CLASSES:
        block = _expect_mapping(containment, name)
        unknown = set(block) - set(CONTAINMENT_CHANNELS)
        missing = set(CONTAINMENT_CHANNELS) - set(block)
        if unknown or missing:
            raise ValueError(f"containment_rate.{name} channels are wrong")
        rates = {channel: _number(block, channel, f"containment_rate.{name}") for channel in CONTAINMENT_CHANNELS}
        for channel, rate in rates.items():
            _between(rate, Decimal(0), Decimal(1), f"containment_rate.{name}.{channel}")
        containment_rate[name] = rates

    delta = data["containment_scenario_delta"]
    if not isinstance(delta, Decimal):
        raise ValueError("containment_scenario_delta must be a number")
    _between(delta, Decimal(0), Decimal(1), "containment_scenario_delta")

    swing = data["sensitivity_relative_swing"]
    if not isinstance(swing, Decimal):
        raise ValueError("sensitivity_relative_swing must be a number")
    _between(swing, Decimal(0), Decimal("0.9"), "sensitivity_relative_swing")

    demand: dict[str, Decimal] = {}
    for intent, weight in weights.items():
        if not isinstance(weight, Decimal):
            raise ValueError(f"demand_weight_by_intent.{intent} must be a number")
        if weight <= 0:
            raise ValueError(f"demand_weight_by_intent.{intent} must be positive")
        demand[str(intent)] = weight

    prevalence = _number(triage, "prevalence", "triage")
    recall = _number(triage, "recall", "triage")
    precision = _number(triage, "precision", "triage")
    _between(prevalence, Decimal(0), Decimal(1), "triage.prevalence")
    _between(recall, Decimal(0), Decimal(1), "triage.recall")
    _between(precision, Decimal(0), Decimal(1), "triage.precision")
    value_tp = _number(triage, "value_per_true_positive", "triage")
    penalty_fn = _number(triage, "penalty_per_false_negative", "triage")
    if value_tp < 0 or penalty_fn < 0:
        raise ValueError("triage value and penalty must be non-negative")

    leaves: list[tuple[str, str, Decimal]] = []
    _walk_numbers(data, "", leaves)

    return Assumptions(
        currency_code=str(data["currency_code"]),
        currency_label=str(data["currency_label"]),
        note=str(data["note"]),
        annual_contacts=annual_contacts,
        voice_agent_monthly_wage=_number(wages, "voice_agent_monthly_wage", "wages"),
        chat_agent_monthly_wage=_number(wages, "chat_agent_monthly_wage", "wages"),
        senior_agent_monthly_wage=_number(wages, "senior_agent_monthly_wage", "wages"),
        burden_rate=burden,
        monthly_productive_hours=hours,
        aht_voice_agent=_number(handle, "voice_agent", "handle_time_minutes"),
        aht_senior_agent=_number(handle, "senior_agent", "handle_time_minutes"),
        aht_live_chat=_number(handle, "live_chat", "handle_time_minutes"),
        aht_ivr=_number(handle, "ivr", "handle_time_minutes"),
        voice_telco_per_minute=_number(variable, "voice_telco_per_minute", "channel_variable"),
        ivr_per_minute=_number(variable, "ivr_per_minute", "channel_variable"),
        ivr_platform_per_contact=_number(variable, "ivr_platform_per_contact", "channel_variable"),
        ussd_per_session=_number(variable, "ussd_per_session", "channel_variable"),
        ussd_sessions_per_contact=_number(variable, "ussd_sessions_per_contact", "channel_variable"),
        live_chat_platform_per_contact=_number(variable, "live_chat_platform_per_contact", "channel_variable"),
        chat_bot_platform_per_contact=_number(variable, "chat_bot_platform_per_contact", "channel_variable"),
        routing_share=routing_share,
        containment_rate=containment_rate,
        containment_scenario_delta=delta,
        demand_weight_by_intent=demand,
        triage_prevalence=prevalence,
        triage_recall=recall,
        triage_precision=precision,
        value_per_true_positive=value_tp,
        penalty_per_false_negative=penalty_fn,
        bot_build_cost=_number(investment, "bot_build_cost", "investment"),
        bot_annual_licence=_number(investment, "bot_annual_licence", "investment"),
        triage_build_cost=_number(investment, "triage_build_cost", "investment"),
        triage_annual_licence=_number(investment, "triage_annual_licence", "investment"),
        sensitivity_relative_swing=swing,
        numeric_leaves=tuple(leaves),
    )


def apply_overrides(data: dict, overrides: list[str]) -> dict:
    updated = copy.deepcopy(data)
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"--set value must be key=value, got {item!r}")
        path, raw = item.split("=", 1)
        parts = path.split(".")
        node = updated
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                raise ValueError(f"Unknown assumption path {path}")
            node = node[part]
        leaf = parts[-1]
        if leaf not in node:
            raise ValueError(f"Unknown assumption path {path}")
        if not re.fullmatch(r"[+-]?(?:\d+\.\d+|\d+)", raw):
            raise ValueError(f"--set {path} must be a number")
        node[leaf] = Decimal(raw)
    return updated


def load_assumptions(path: Path, overrides: list[str] | None = None) -> tuple[dict, Assumptions]:
    raw = load_raw(path)
    if overrides:
        raw = apply_overrides(raw, overrides)
    return raw, validate(raw)
