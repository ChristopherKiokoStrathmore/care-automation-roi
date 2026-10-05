/**
 * Run the full cost-benefit model from an editable assumption draft.
 */
import { parseDraft, validate, type AssumptionDraft } from "./assumptions";
import { Decimal, fmtMoney, fmtMonths, fmtRate, fmtUnit, paybackCell, roiCell, type Decimal as DecimalValue } from "./decimal-util";
import {
  buildScenarios,
  confusionRates,
  costsByClass,
  prepareDemand,
  qualityPerContact,
  unitCosts,
  type Economics,
  type Scenario,
} from "./model";
import { buildSwings, type SwingRow } from "./sensitivity";
import { AUTOMATION_CLASSES, loadIntents, type AutomationClass, type IntentRow } from "./taxonomy";

export const UNIT_ORDER: readonly { id: "voice_agent" | "ivr" | "ussd_bot" | "live_chat" | "chat_bot" | "senior_agent"; label: string }[] = [
  { id: "voice_agent", label: "Agent (voice)" },
  { id: "ivr", label: "IVR" },
  { id: "ussd_bot", label: "USSD bot" },
  { id: "live_chat", label: "Chat (staffed)" },
  { id: "chat_bot", label: "Chat bot (unstaffed)" },
  { id: "senior_agent", label: "Senior agent" },
];

export const CLASS_LABEL: Record<AutomationClass, string> = {
  lookup: "Lookup",
  structured_transaction: "Structured transaction",
  human_required: "Human required",
};

export interface ClassResult {
  id: AutomationClass;
  label: string;
  nIntents: number;
  nameShare: Decimal;
  demandShare: DecimalValue;
  costPerContact: DecimalValue;
}

export interface ModelResult {
  currencyLabel: string;
  note: string;
  annualContacts: DecimalValue;
  rows: IntentRow[];
  intentShares: Record<string, DecimalValue>;
  units: { id: string; label: string; cost: DecimalValue }[];
  classes: ClassResult[];
  scenarios: Scenario[];
  swings: SwingRow[];
  triageRates: ReturnType<typeof confusionRates>;
  qualityPerContact: Decimal;
}

export type Evaluation = { ok: true; result: ModelResult } | { ok: false; message: string };

export function scenarioById(scenarios: Scenario[], id: string): Scenario {
  const found = scenarios.find((item) => item.scenarioId === id);
  if (!found) throw new Error(`Missing scenario ${id}`);
  return found;
}

export function economicsView(economics: Economics, costPerContact: Decimal) {
  return {
    costPerContact: fmtUnit(costPerContact),
    annualOperatingCost: fmtMoney(economics.annualOperatingCost),
    annualOperatingSaving: fmtMoney(economics.annualOperatingSaving),
    assumedQualityValue: fmtMoney(economics.assumedQualityValue),
    annualLicence: fmtMoney(economics.annualLicence),
    capex: fmtMoney(economics.capex),
    netAnnualBenefit: fmtMoney(economics.netAnnualBenefit),
    paybackMonths: paybackCell(economics.capex, economics.paybackMonths),
    year1Roi: roiCell(economics.capex, economics.year1Roi),
    year1NetCash: fmtMoney(economics.year1NetCash),
  };
}

export function evaluate(draft: AssumptionDraft): Evaluation {
  try {
    const raw = parseDraft(draft);
    const assumptions = validate(raw);
    const rows = loadIntents();
    const { shares, classes: classShares } = prepareDemand(assumptions, rows);
    const units = unitCosts(assumptions);
    const classCosts = costsByClass(assumptions, units);
    const scenarios = buildScenarios(assumptions, units, classShares);
    const swings = buildSwings(raw, rows);
    const triageRates = confusionRates(
      assumptions.triagePrevalence,
      assumptions.triageRecall,
      assumptions.triagePrecision,
    );
    const quality = qualityPerContact(triageRates, assumptions.valuePerTruePositive, assumptions.penaltyPerFalseNegative);
    const nIntents = rows.length;
    return {
      ok: true,
      result: {
        currencyLabel: assumptions.currencyLabel,
        note: assumptions.note,
        annualContacts: assumptions.annualContacts,
        rows,
        intentShares: shares,
        units: UNIT_ORDER.map((item) => ({ id: item.id, label: item.label, cost: units[item.id] })),
        classes: AUTOMATION_CLASSES.map((name) => {
          const count = rows.filter((row) => row.automationClass === name).length;
          return {
            id: name,
            label: CLASS_LABEL[name],
            nIntents: count,
            nameShare: new Decimal(count).div(nIntents),
            demandShare: classShares[name],
            costPerContact: classCosts[name],
          };
        }),
        scenarios,
        swings,
        triageRates,
        qualityPerContact: quality,
      },
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : "The assumptions could not be evaluated.";
    return { ok: false, message };
  }
}

export function committedHeadlineMatch(result: ModelResult): boolean {
  const base = economicsView(scenarioById(result.scenarios, "bot_base").economics, scenarioById(result.scenarios, "bot_base").costPerContact);
  const low = economicsView(scenarioById(result.scenarios, "bot_low").economics, scenarioById(result.scenarios, "bot_low").costPerContact);
  return base.paybackMonths === "8.47" && base.year1Roi === "0.4175" && low.year1Roi === "-0.1571";
}

export function formatRateMap(rates: Record<string, DecimalValue>): Record<string, string> {
  return Object.fromEntries(Object.entries(rates).map(([key, value]) => [key, fmtRate(value)]));
}

export { fmtMonths };
