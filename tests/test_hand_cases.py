"""Hand-checked arithmetic. These cases do not use the portfolio assumption file."""

from decimal import Decimal

import pytest

from care_roi.model import (
    attempt_cost,
    confusion_rates,
    expected_class_cost,
    fully_loaded_hourly,
    programme_economics,
    timed_agent_cost,
    triage_operating_cost,
)


def test_voice_agent_unit_cost_matches_the_fraction():
    hourly = fully_loaded_hourly(Decimal("80000"), Decimal("0.30"), Decimal("140"))
    assert hourly == Decimal("80000") * Decimal("1.30") / Decimal("140")
    cost = timed_agent_cost(Decimal("8"), hourly, Decimal("1.50"))
    # (8/60) * (104000/140) + 1.50 * 8 = 2080/21 + 12
    expected = Decimal(2080) / Decimal(21) + Decimal(12)
    assert cost == expected


def test_ivr_ussd_and_chat_bot_unit_costs_are_the_products_written_above():
    ivr = Decimal("3") * Decimal("0.80") + Decimal("2.00")
    ussd = Decimal("1.20") * Decimal("1.00")
    assert ivr == Decimal("4.40")
    assert ussd == Decimal("1.20")


def test_contained_attempt_adds_the_voice_cost_only_on_the_miss():
    units = {
        "voice_agent": Decimal("100"),
        "ussd_bot": Decimal("5"),
        "chat_bot": Decimal("3"),
        "ivr": Decimal("4"),
    }
    assert attempt_cost("ussd_bot", Decimal("0.25"), units) == Decimal("80")
    assert attempt_cost("voice_agent", Decimal("0"), units) == Decimal("100")
    shares = {"ussd_bot": Decimal("1"), "chat_bot": Decimal("0"), "ivr": Decimal("0"), "voice_agent": Decimal("0")}
    containment = {"ussd_bot": Decimal("0.25"), "chat_bot": Decimal("0"), "ivr": Decimal("0")}
    assert expected_class_cost(shares, containment, units) == Decimal("80")


def test_triage_counts_for_one_thousand_contacts():
    rates = confusion_rates(Decimal("0.10"), Decimal("0.80"), Decimal("0.50"))
    assert rates["true_positive"] == Decimal("0.08")
    assert rates["false_positive"] == Decimal("0.08")
    assert rates["false_negative"] == Decimal("0.02")
    assert rates["true_negative"] == Decimal("0.82")
    assert rates["predicted_positive"] == Decimal("0.16")
    total = sum(rates[key] for key in ("true_positive", "false_positive", "false_negative", "true_negative"))
    assert total == Decimal("1")
    assert Decimal(1000) * rates["true_positive"] == Decimal(80)
    assert Decimal(1000) * rates["predicted_positive"] == Decimal(160)


def test_inconsistent_precision_is_rejected():
    with pytest.raises(ValueError, match="predicted-positive"):
        confusion_rates(Decimal("0.50"), Decimal("0.90"), Decimal("0.20"))


def test_payback_and_year1_roi():
    result = programme_economics(
        annual_operating_saving=Decimal("120000"),
        quality=Decimal("0"),
        licence=Decimal("20000"),
        capex=Decimal("50000"),
    )
    assert result.net_annual_benefit == Decimal("100000")
    assert result.payback_months == Decimal("6")
    assert result.year1_roi == Decimal("1")
    assert result.year1_net_cash == Decimal("50000")


def test_non_positive_net_benefit_does_not_pay_back():
    result = programme_economics(
        annual_operating_saving=Decimal("1000"),
        quality=Decimal("0"),
        licence=Decimal("1000"),
        capex=Decimal("5000"),
    )
    assert result.net_annual_benefit == Decimal("0")
    assert result.payback_months is None
    assert result.year1_roi == Decimal("-1")


def test_triage_operating_cost_sends_predicted_emergencies_to_the_senior_rate():
    rates = confusion_rates(Decimal("0.10"), Decimal("0.80"), Decimal("0.50"))
    cost = triage_operating_cost(Decimal("40"), Decimal("200"), rates)
    # 0.16 * 200 + 0.84 * 40 = 32 + 33.6
    assert cost == Decimal("65.6")
