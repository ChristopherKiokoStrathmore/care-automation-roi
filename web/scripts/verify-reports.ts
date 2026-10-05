/**
 * Compare the TypeScript port with the committed Python reports.
 * Run from web/: npm run verify
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { DEFAULT_DRAFT } from "../lib/assumptions";
import { fmtInput, fmtMoney, fmtMonths, fmtRate, fmtUnit } from "../lib/decimal-util";
import { economicsView, evaluate, scenarioById } from "../lib/evaluate";

const reportsDir = resolve(dirname(fileURLToPath(import.meta.url)), "../../reports");

function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let inQuotes = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (inQuotes) {
      if (char === '"') {
        if (text[index + 1] === '"') {
          field += '"';
          index += 1;
        } else {
          inQuotes = false;
        }
      } else {
        field += char;
      }
    } else if (char === '"') {
      inQuotes = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (char !== "\r") {
      field += char;
    }
  }
  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  const [header, ...body] = rows.filter((cells) => cells.some((cell) => cell !== ""));
  return body.map((cells) => Object.fromEntries(header.map((key, index) => [key, cells[index] ?? ""])));
}

const evaluation = evaluate(DEFAULT_DRAFT);
if (!evaluation.ok) {
  throw new Error(evaluation.message);
}
const result = evaluation.result;

const summary = JSON.parse(readFileSync(resolve(reportsDir, "summary.json"), "utf8")) as {
  currency_label: string;
  base_year1_net_cash: string;
  unit_costs: Record<string, string>;
  scenarios: Record<string, Record<string, string>>;
  triage_rates: Record<string, string>;
};

assert.equal(result.currencyLabel, summary.currency_label);
assert.equal(fmtMoney(result.swings[0].baseYear1NetCash), summary.base_year1_net_cash);

for (const [id, cost] of Object.entries(summary.unit_costs)) {
  const unit = result.units.find((item) => item.id === id);
  assert.ok(unit, `missing unit ${id}`);
  assert.equal(fmtUnit(unit.cost), cost, id);
}

for (const [id, expected] of Object.entries(summary.scenarios)) {
  const scenario = scenarioById(result.scenarios, id);
  const view = economicsView(scenario.economics, scenario.costPerContact);
  assert.equal(view.costPerContact, expected.cost_per_contact, `${id} cost`);
  assert.equal(view.annualOperatingCost, expected.annual_operating_cost, `${id} annual cost`);
  assert.equal(view.annualOperatingSaving, expected.annual_operating_saving_vs_baseline, `${id} saving`);
  assert.equal(view.assumedQualityValue, expected.assumed_quality_value, `${id} quality`);
  assert.equal(view.netAnnualBenefit, expected.net_annual_benefit, `${id} net`);
  assert.equal(view.paybackMonths, expected.payback_months, `${id} payback`);
  assert.equal(view.year1Roi, expected.year1_roi, `${id} roi`);
  assert.equal(view.year1NetCash, expected.year1_net_cash, `${id} cash`);
}

assert.equal(summary.scenarios.bot_base.payback_months, "8.47");
assert.equal(summary.scenarios.bot_base.year1_roi, "0.4175");
assert.equal(summary.scenarios.bot_low.year1_roi, "-0.1571");

for (const [key, expected] of Object.entries(summary.triage_rates)) {
  assert.equal(fmtRate(result.triageRates[key as keyof typeof result.triageRates]), expected, key);
}

const classRows = parseCsv(readFileSync(resolve(reportsDir, "class_costs.csv"), "utf8"));
for (const row of classRows) {
  const found = result.classes.find((item) => item.id === row.automation_class);
  assert.ok(found, row.automation_class);
  assert.equal(String(found.nIntents), row.n_intents);
  assert.equal(fmtRate(found.nameShare), row.share_of_intent_names);
  assert.equal(fmtRate(found.demandShare), row.assumed_demand_share);
  assert.equal(fmtUnit(found.costPerContact), row.cost_per_contact);
}

const swingRows = parseCsv(readFileSync(resolve(reportsDir, "sensitivity.csv"), "utf8"));
assert.equal(result.swings.length, swingRows.length);
result.swings.forEach((swing, index) => {
  const row = swingRows[index];
  assert.equal(swing.factorId, row.factor_id, "factor order");
  assert.equal(swing.label, row.label);
  assert.equal(fmtInput(swing.inputLow), row.input_low, swing.factorId);
  assert.equal(fmtInput(swing.inputHigh), row.input_high, swing.factorId);
  assert.equal(swing.lowClamped ? "true" : "false", row.low_clamped);
  assert.equal(swing.highClamped ? "true" : "false", row.high_clamped);
  assert.equal(fmtMoney(swing.year1NetCashLow), row.year1_net_cash_low, swing.factorId);
  assert.equal(fmtMoney(swing.year1NetCashHigh), row.year1_net_cash_high, swing.factorId);
  assert.equal(fmtMonths(swing.paybackMonthsLow), row.payback_months_low, swing.factorId);
  assert.equal(fmtMonths(swing.paybackMonthsHigh), row.payback_months_high, swing.factorId);
  assert.equal(fmtMoney(swing.baseYear1NetCash), row.base_year1_net_cash);
  assert.equal(fmtMonths(swing.basePaybackMonths), row.base_payback_months);
});

const scenarioRows = parseCsv(readFileSync(resolve(reportsDir, "scenarios.csv"), "utf8"));
scenarioRows.forEach((row, index) => {
  const scenario = result.scenarios[index];
  const view = economicsView(scenario.economics, scenario.costPerContact);
  assert.equal(scenario.scenarioId, row.scenario_id);
  assert.equal(scenario.label, row.label);
  assert.equal(scenario.note, row.note);
  assert.equal(view.annualLicence, row.annual_licence, scenario.scenarioId);
  assert.equal(view.capex, row.capex, scenario.scenarioId);
});

console.log("Default case matches reports/: payback 8.47 months, year-1 ROI 0.4175, low-containment year-1 ROI -0.1571.");
