/**
 * Port of care_roi/model.py.
 * Formulas use the assumptions object only. Bitext example counts never enter the arithmetic.
 */
import type { Assumptions } from "./assumptions";
import { ONE, SIXTY, TWELVE, ZERO, type Decimal } from "./decimal-util";
import {
  type AutomationClass,
  type ContainmentChannel,
  type IntentRow,
  classDemand,
  demandShares,
} from "./taxonomy";

export type UnitCostId = "voice_agent" | "senior_agent" | "live_chat" | "ivr" | "ussd_bot" | "chat_bot";

export type ContainmentMap = Record<AutomationClass, Record<ContainmentChannel, Decimal>>;

export function fullyLoadedHourly(monthlyWage: Decimal, burdenRate: Decimal, productiveHours: Decimal): Decimal {
  return monthlyWage.mul(ONE.plus(burdenRate)).div(productiveHours);
}

export function timedAgentCost(handleMinutes: Decimal, hourly: Decimal, telcoPerMinute: Decimal): Decimal {
  return handleMinutes.div(SIXTY).mul(hourly).plus(telcoPerMinute.mul(handleMinutes));
}

export function unitCosts(assumptions: Assumptions): Record<UnitCostId, Decimal> {
  const voiceHourly = fullyLoadedHourly(
    assumptions.voiceAgentMonthlyWage,
    assumptions.burdenRate,
    assumptions.monthlyProductiveHours,
  );
  const seniorHourly = fullyLoadedHourly(
    assumptions.seniorAgentMonthlyWage,
    assumptions.burdenRate,
    assumptions.monthlyProductiveHours,
  );
  const chatHourly = fullyLoadedHourly(
    assumptions.chatAgentMonthlyWage,
    assumptions.burdenRate,
    assumptions.monthlyProductiveHours,
  );
  return {
    voice_agent: timedAgentCost(assumptions.ahtVoiceAgent, voiceHourly, assumptions.voiceTelcoPerMinute),
    senior_agent: timedAgentCost(assumptions.ahtSeniorAgent, seniorHourly, assumptions.voiceTelcoPerMinute),
    live_chat: timedAgentCost(assumptions.ahtLiveChat, chatHourly, ZERO).plus(assumptions.liveChatPlatformPerContact),
    ivr: assumptions.ahtIvr.mul(assumptions.ivrPerMinute).plus(assumptions.ivrPlatformPerContact),
    ussd_bot: assumptions.ussdSessionsPerContact.mul(assumptions.ussdPerSession),
    chat_bot: assumptions.chatBotPlatformPerContact,
  };
}

export function attemptCost(channel: string, containment: Decimal, units: Record<UnitCostId, Decimal>): Decimal {
  if (channel === "voice_agent") return units.voice_agent;
  if (containment.lt(0) || containment.gt(1)) {
    throw new Error("containment must be between 0 and 1");
  }
  return units[channel as UnitCostId].plus(ONE.minus(containment).mul(units.voice_agent));
}

export function expectedClassCost(
  shares: Record<string, Decimal>,
  containment: Record<string, Decimal>,
  units: Record<UnitCostId, Decimal>,
): Decimal {
  let total = ZERO;
  for (const [channel, share] of Object.entries(shares)) {
    const rate = channel === "voice_agent" ? ZERO : containment[channel];
    total = total.plus(share.mul(attemptCost(channel, rate, units)));
  }
  return total;
}

export function shiftContainment(containment: ContainmentMap, delta: Decimal, direction: number): ContainmentMap {
  const shifted = {} as ContainmentMap;
  for (const [className, rates] of Object.entries(containment) as [AutomationClass, Record<ContainmentChannel, Decimal>][]) {
    shifted[className] = {} as Record<ContainmentChannel, Decimal>;
    for (const [channel, rate] of Object.entries(rates) as [ContainmentChannel, Decimal][]) {
      let value = direction > 0 ? rate.plus(delta) : rate.minus(delta);
      if (value.lt(0)) value = ZERO;
      if (value.gt(1)) value = ONE;
      shifted[className][channel] = value;
    }
  }
  return shifted;
}

export interface ConfusionRates {
  true_positive: Decimal;
  false_positive: Decimal;
  false_negative: Decimal;
  true_negative: Decimal;
  predicted_positive: Decimal;
}

export function confusionRates(prevalence: Decimal, recall: Decimal, precision: Decimal): ConfusionRates {
  const checks: [string, Decimal][] = [
    ["prevalence", prevalence],
    ["recall", recall],
    ["precision", precision],
  ];
  for (const [name, value] of checks) {
    if (value.lt(0) || value.gt(1)) throw new Error(`triage ${name} must be between 0 and 1`);
  }
  if (precision.isZero()) {
    throw new Error("triage precision must be positive so the predicted-positive rate is defined");
  }
  const truePositive = recall.mul(prevalence);
  if (truePositive.gt(precision)) {
    throw new Error(
      "inconsistent triage assumptions: precision is below recall times prevalence, so the predicted-positive rate would exceed 1",
    );
  }
  const predictedPositive = truePositive.div(precision);
  const falsePositive = predictedPositive.minus(truePositive);
  const falseNegative = prevalence.minus(truePositive);
  const trueNegative = ONE.minus(prevalence).minus(falsePositive);
  if (falsePositive.lt(0) || trueNegative.lt(0)) {
    throw new Error("inconsistent triage assumptions");
  }
  return {
    true_positive: truePositive,
    false_positive: falsePositive,
    false_negative: falseNegative,
    true_negative: trueNegative,
    predicted_positive: predictedPositive,
  };
}

export function triageOperatingCost(autoCost: Decimal, seniorCost: Decimal, rates: ConfusionRates): Decimal {
  const predicted = rates.predicted_positive;
  return predicted.mul(seniorCost).plus(ONE.minus(predicted).mul(autoCost));
}

export function qualityPerContact(rates: ConfusionRates, valuePerTp: Decimal, penaltyPerFn: Decimal): Decimal {
  return rates.true_positive.mul(valuePerTp).minus(rates.false_negative.mul(penaltyPerFn));
}

export interface Economics {
  annualOperatingCost: Decimal;
  annualOperatingSaving: Decimal;
  assumedQualityValue: Decimal;
  annualLicence: Decimal;
  capex: Decimal;
  netAnnualBenefit: Decimal;
  year1NetCash: Decimal;
  year1Roi: Decimal | null;
  paybackMonths: Decimal | null;
}

export function programmeEconomics(
  annualOperatingSaving: Decimal,
  quality: Decimal,
  licence: Decimal,
  capex: Decimal,
): Economics {
  const netAnnual = annualOperatingSaving.plus(quality).minus(licence);
  const year1NetCash = netAnnual.minus(capex);
  let roi: Decimal | null = null;
  let payback: Decimal | null = null;
  if (!capex.isZero()) {
    roi = netAnnual.minus(capex).div(capex);
    if (netAnnual.gt(0)) payback = capex.div(netAnnual.div(TWELVE));
  }
  return {
    annualOperatingCost: ZERO,
    annualOperatingSaving: annualOperatingSaving,
    assumedQualityValue: quality,
    annualLicence: licence,
    capex,
    netAnnualBenefit: netAnnual,
    year1NetCash,
    year1Roi: roi,
    paybackMonths: payback,
  };
}

export function blendedCost(
  classCosts: Record<AutomationClass, Decimal>,
  classShares: Record<AutomationClass, Decimal>,
): Decimal {
  let total = ZERO;
  for (const name of Object.keys(classCosts) as AutomationClass[]) {
    total = total.plus(classShares[name].mul(classCosts[name]));
  }
  return total;
}

export function costsByClass(
  assumptions: Assumptions,
  units: Record<UnitCostId, Decimal>,
  containment?: ContainmentMap,
): Record<AutomationClass, Decimal> {
  const rates = containment ?? assumptions.containmentRate;
  return {
    lookup: expectedClassCost(assumptions.routingShare.lookup, rates.lookup, units),
    structured_transaction: expectedClassCost(
      assumptions.routingShare.structured_transaction,
      rates.structured_transaction,
      units,
    ),
    human_required: expectedClassCost(assumptions.routingShare.human_required, rates.human_required, units),
  };
}

export interface Scenario {
  scenarioId: string;
  label: string;
  containment: string;
  triage: string;
  costPerContact: Decimal;
  economics: Economics;
  note: string;
}

export function buildScenarios(
  assumptions: Assumptions,
  units: Record<UnitCostId, Decimal>,
  classShares: Record<AutomationClass, Decimal>,
): Scenario[] {
  const baseline = units.voice_agent;
  const annualBaseline = assumptions.annualContacts.mul(baseline);
  const rates = confusionRates(assumptions.triagePrevalence, assumptions.triageRecall, assumptions.triagePrecision);
  const qualityRate = qualityPerContact(rates, assumptions.valuePerTruePositive, assumptions.penaltyPerFalseNegative);

  const scenario = (
    scenarioId: string,
    label: string,
    containmentName: string,
    triageName: string,
    cost: Decimal,
    qualityPer: Decimal,
    licence: Decimal,
    capex: Decimal,
    note: string,
  ): Scenario => {
    const annualCost = assumptions.annualContacts.mul(cost);
    const saving = annualBaseline.minus(annualCost);
    const quality = assumptions.annualContacts.mul(qualityPer);
    const economics = programmeEconomics(saving, quality, licence, capex);
    return {
      scenarioId,
      label,
      containment: containmentName,
      triage: triageName,
      costPerContact: cost,
      economics: { ...economics, annualOperatingCost: annualCost },
      note,
    };
  };

  const lowRates = shiftContainment(assumptions.containmentRate, assumptions.containmentScenarioDelta, -1);
  const highRates = shiftContainment(assumptions.containmentRate, assumptions.containmentScenarioDelta, 1);
  const baseClass = costsByClass(assumptions, units);
  const lowClass = costsByClass(assumptions, units, lowRates);
  const highClass = costsByClass(assumptions, units, highRates);
  const baseCost = blendedCost(baseClass, classShares);
  const lowCost = blendedCost(lowClass, classShares);
  const highCost = blendedCost(highClass, classShares);
  const triageCost = triageOperatingCost(baseCost, units.senior_agent, rates);

  const botLicence = assumptions.botAnnualLicence;
  const botCapex = assumptions.botBuildCost;
  const bothLicence = botLicence.plus(assumptions.triageAnnualLicence);
  const bothCapex = botCapex.plus(assumptions.triageBuildCost);

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
      lowCost,
      ZERO,
      botLicence,
      botCapex,
      "Each containment rate is the base assumption minus containment_scenario_delta, clamped to [0, 1].",
    ),
    scenario(
      "bot_base",
      "Bot programme, base containment",
      "base",
      "off",
      baseCost,
      ZERO,
      botLicence,
      botCapex,
      "Headline bot scenario. No triage routing and no assumed quality value.",
    ),
    scenario(
      "bot_high",
      "Bot programme, high containment",
      "base plus delta",
      "off",
      highCost,
      ZERO,
      botLicence,
      botCapex,
      "Each containment rate is the base assumption plus containment_scenario_delta, clamped to [0, 1].",
    ),
    scenario(
      "bot_base_triage",
      "Bot programme plus emergency routing, with assumed quality value",
      "base",
      "on",
      triageCost,
      qualityRate,
      bothLicence,
      bothCapex,
      "Predicted emergency contacts skip the bot and pay the senior-agent unit cost. The quality column is an assumption, not a measured saving.",
    ),
    scenario(
      "bot_base_triage_no_quality_value",
      "Bot programme plus emergency routing, quality value set to zero",
      "base",
      "on",
      triageCost,
      ZERO,
      bothLicence,
      bothCapex,
      "Same operating path as the triage scenario, with the assumed quality value removed.",
    ),
  ];
}

export function prepareDemand(assumptions: Assumptions, rows: IntentRow[]) {
  const shares = demandShares(rows, assumptions.demandWeightByIntent);
  const classes = classDemand(rows, shares);
  return { shares, classes };
}
