/**
 * Port of care_roi/sensitivity.py. One-at-a-time swings of the bot programme's year-1 net cash.
 */
import { cloneRaw, getRawPath, setRawPath, validate, type RawAssumptions } from "./assumptions";
import { ONE, ZERO, type Decimal } from "./decimal-util";
import { buildScenarios, prepareDemand, unitCosts, type Scenario } from "./model";
import { loadIntents, type IntentRow } from "./taxonomy";

export const FACTORS: readonly { label: string; path: string; kind: "number" | "unit_interval" | "lookup_ussd_share" }[] = [
  { label: "Annual contacts", path: "volume.annual_contacts", kind: "number" },
  { label: "Voice-agent monthly wage", path: "wages.voice_agent_monthly_wage", kind: "number" },
  { label: "Voice-agent handle time", path: "handle_time_minutes.voice_agent", kind: "number" },
  { label: "Wage burden rate", path: "wages.burden_rate", kind: "number" },
  { label: "Monthly productive hours", path: "wages.monthly_productive_hours", kind: "number" },
  { label: "Lookup USSD containment", path: "containment_rate.lookup.ussd_bot", kind: "unit_interval" },
  { label: "Transaction USSD containment", path: "containment_rate.structured_transaction.ussd_bot", kind: "unit_interval" },
  { label: "Lookup USSD offer share", path: "routing_share.lookup.ussd_bot", kind: "lookup_ussd_share" },
  { label: "USSD cost per session", path: "channel_variable.ussd_per_session", kind: "number" },
  { label: "Bot build cost", path: "investment.bot_build_cost", kind: "number" },
  { label: "Bot annual licence", path: "investment.bot_annual_licence", kind: "number" },
];

export interface SwingRow {
  factorId: string;
  label: string;
  inputLow: Decimal;
  inputHigh: Decimal;
  lowClamped: boolean;
  highClamped: boolean;
  year1NetCashLow: Decimal;
  year1NetCashHigh: Decimal;
  paybackMonthsLow: Decimal | null;
  paybackMonthsHigh: Decimal | null;
  baseYear1NetCash: Decimal;
  basePaybackMonths: Decimal | null;
}

function clamp01(value: Decimal): { value: Decimal; clamped: boolean } {
  if (value.lt(0)) return { value: ZERO, clamped: true };
  if (value.gt(1)) return { value: ONE, clamped: true };
  return { value, clamped: false };
}

function swingLookupUssd(data: RawAssumptions, factor: Decimal): { value: Decimal; clamped: boolean } {
  const lookup = data.routing_share.lookup;
  const base = lookup.ussd_bot;
  const voice = lookup.voice_agent;
  let { value: target, clamped } = clamp01(base.mul(factor));
  let newVoice = voice.minus(target.minus(base));
  if (newVoice.lt(0)) {
    target = base.plus(voice);
    newVoice = ZERO;
    clamped = true;
  }
  lookup.ussd_bot = target;
  lookup.voice_agent = newVoice;
  return { value: target, clamped };
}

function botBase(raw: RawAssumptions, rows: IntentRow[]): Scenario {
  const assumptions = validate(raw);
  const units = unitCosts(assumptions);
  const { classes } = prepareDemand(assumptions, rows);
  const scenarios = buildScenarios(assumptions, units, classes);
  const found = scenarios.find((item) => item.scenarioId === "bot_base");
  if (!found) throw new Error("bot_base scenario missing");
  return found;
}

export function buildSwings(raw: RawAssumptions, rows: IntentRow[] = loadIntents()): SwingRow[] {
  const base = botBase(raw, rows).economics;
  const swing = validate(raw).sensitivityRelativeSwing;
  const lowFactor = ONE.minus(swing);
  const highFactor = ONE.plus(swing);
  const rowsOut: SwingRow[] = [];

  for (const factor of FACTORS) {
    const lowData = cloneRaw(raw);
    const highData = cloneRaw(raw);
    let inputLow: Decimal;
    let inputHigh: Decimal;
    let lowClamped = false;
    let highClamped = false;
    if (factor.kind === "lookup_ussd_share") {
      const lowSwing = swingLookupUssd(lowData, lowFactor);
      const highSwing = swingLookupUssd(highData, highFactor);
      inputLow = lowSwing.value;
      inputHigh = highSwing.value;
      lowClamped = lowSwing.clamped;
      highClamped = highSwing.clamped;
    } else {
      const baseInput = getRawPath(raw, factor.path);
      inputLow = baseInput.mul(lowFactor);
      inputHigh = baseInput.mul(highFactor);
      if (factor.kind === "unit_interval") {
        const lowClamp = clamp01(inputLow);
        const highClamp = clamp01(inputHigh);
        inputLow = lowClamp.value;
        inputHigh = highClamp.value;
        lowClamped = lowClamp.clamped;
        highClamped = highClamp.clamped;
      }
      setRawPath(lowData, factor.path, inputLow);
      setRawPath(highData, factor.path, inputHigh);
    }
    const lowEcon = botBase(lowData, rows).economics;
    const highEcon = botBase(highData, rows).economics;
    rowsOut.push({
      factorId: factor.path,
      label: factor.label,
      inputLow,
      inputHigh,
      lowClamped,
      highClamped,
      year1NetCashLow: lowEcon.year1NetCash,
      year1NetCashHigh: highEcon.year1NetCash,
      paybackMonthsLow: lowEcon.paybackMonths,
      paybackMonthsHigh: highEcon.paybackMonths,
      baseYear1NetCash: base.year1NetCash,
      basePaybackMonths: base.paybackMonths,
    });
  }

  rowsOut.sort((left, right) => {
    const spanLeft = left.year1NetCashHigh.minus(left.year1NetCashLow).abs();
    const spanRight = right.year1NetCashHigh.minus(right.year1NetCashLow).abs();
    const bySpan = spanRight.comparedTo(spanLeft);
    if (bySpan !== 0) return bySpan;
    return left.factorId < right.factorId ? -1 : left.factorId > right.factorId ? 1 : 0;
  });
  return rowsOut;
}
