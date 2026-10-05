/**
 * Port of care_roi/taxonomy.py. Bitext example counts are not demand.
 */
import { Decimal, ZERO, parseDecimal } from "./decimal-util";

export const AUTOMATION_CLASSES = ["lookup", "structured_transaction", "human_required"] as const;
export type AutomationClass = (typeof AUTOMATION_CLASSES)[number];

export const ROUTING_CHANNELS = ["ussd_bot", "chat_bot", "ivr", "voice_agent"] as const;
export type RoutingChannel = (typeof ROUTING_CHANNELS)[number];

export const CONTAINMENT_CHANNELS = ["ussd_bot", "chat_bot", "ivr"] as const;
export type ContainmentChannel = (typeof CONTAINMENT_CHANNELS)[number];

const EXPLICIT_HUMAN = new Set([
  "customer_service",
  "human_agent",
  "activate_phone",
  "deactivate_phone",
  "install_internet",
  "cancel_plan",
  "change_provider",
]);

const LOOKUP_EXACT = new Set(["invoices", "payment_methods"]);

const EXPLICIT_TRANSACTION = new Set([
  "pay",
  "schedule_payments",
  "set_usage_limits",
  "activate_roaming",
  "activate_call_management_services",
  "deactivate_call_management_services",
  "change_plan",
  "sign_up_for_plan",
]);

export const RULE_LINES = [
  "1. If the Bitext category is COMPLAINTS, the class is human_required (clause category_complaints).",
  "2. If the intent is customer_service, human_agent, activate_phone, deactivate_phone, install_internet, cancel_plan, or change_provider, or the intent name starts with dispute_, the class is human_required (clause explicit_human_or_dispute).",
  "3. If the intent name starts with check_, or the intent is invoices or payment_methods, the class is lookup (clause lookup_name).",
  "4. If the intent is pay, schedule_payments, set_usage_limits, activate_roaming, activate_call_management_services, deactivate_call_management_services, change_plan, or sign_up_for_plan, the class is structured_transaction (clause explicit_transaction).",
  "5. Any other intent raises an error. A new Bitext intent is not classified by a default.",
] as const;

export interface IntentSource {
  category: string;
  intent: string;
  nExamples: number;
}

export interface IntentRow extends IntentSource {
  automationClass: AutomationClass;
  ruleClause: string;
}

/** Public Bitext intent names from data/bitext_by_intent.csv. nExamples is the training count. */
export const BITEXT_INTENTS: readonly IntentSource[] = [
  { category: "BILLING", intent: "dispute_invoice", nExamples: 1000 },
  { category: "BILLING", intent: "invoices", nExamples: 1000 },
  { category: "COMPLAINTS", intent: "get_compensation", nExamples: 1000 },
  { category: "COMPLAINTS", intent: "report_poor_signal_coverage", nExamples: 1000 },
  { category: "COMPLAINTS", intent: "report_problem", nExamples: 1000 },
  { category: "CONSUMPTION", intent: "check_excess_data_charges", nExamples: 1000 },
  { category: "CONSUMPTION", intent: "check_usage", nExamples: 1000 },
  { category: "CONSUMPTION", intent: "set_usage_limits", nExamples: 1000 },
  { category: "CONTACT", intent: "customer_service", nExamples: 1000 },
  { category: "CONTACT", intent: "human_agent", nExamples: 1000 },
  { category: "PAYMENT", intent: "check_mobile_payments", nExamples: 1000 },
  { category: "PAYMENT", intent: "pay", nExamples: 1000 },
  { category: "PAYMENT", intent: "payment_methods", nExamples: 1000 },
  { category: "PAYMENT", intent: "schedule_payments", nExamples: 1000 },
  { category: "SERVICES", intent: "activate_call_management_services", nExamples: 1000 },
  { category: "SERVICES", intent: "activate_phone", nExamples: 1000 },
  { category: "SERVICES", intent: "activate_roaming", nExamples: 1000 },
  { category: "SERVICES", intent: "check_signal_coverage", nExamples: 1000 },
  { category: "SERVICES", intent: "deactivate_call_management_services", nExamples: 1000 },
  { category: "SERVICES", intent: "deactivate_phone", nExamples: 1000 },
  { category: "SERVICES", intent: "install_internet", nExamples: 1000 },
  { category: "SUBSCRIPTION", intent: "cancel_plan", nExamples: 1000 },
  { category: "SUBSCRIPTION", intent: "change_plan", nExamples: 1000 },
  { category: "SUBSCRIPTION", intent: "change_provider", nExamples: 1000 },
  { category: "SUBSCRIPTION", intent: "check_cancellation_fee", nExamples: 1000 },
  { category: "SUBSCRIPTION", intent: "sign_up_for_plan", nExamples: 1000 },
];

export function classify(category: string, intent: string): { automationClass: AutomationClass; ruleClause: string } {
  if (category === "COMPLAINTS") {
    return { automationClass: "human_required", ruleClause: "category_complaints" };
  }
  if (EXPLICIT_HUMAN.has(intent) || intent.startsWith("dispute_")) {
    return { automationClass: "human_required", ruleClause: "explicit_human_or_dispute" };
  }
  if (intent.startsWith("check_") || LOOKUP_EXACT.has(intent)) {
    return { automationClass: "lookup", ruleClause: "lookup_name" };
  }
  if (EXPLICIT_TRANSACTION.has(intent)) {
    return { automationClass: "structured_transaction", ruleClause: "explicit_transaction" };
  }
  throw new Error(`Unmapped Bitext intent ${JSON.stringify(intent)} in category ${JSON.stringify(category)}`);
}

export function loadIntents(): IntentRow[] {
  const rows = BITEXT_INTENTS.map((source) => {
    const classified = classify(source.category, source.intent);
    return { ...source, ...classified };
  });
  const names = rows.map((row) => row.intent);
  if (new Set(names).size !== names.length) {
    throw new Error("Duplicate intent name in the taxonomy file");
  }
  if (rows.length !== 26) {
    throw new Error("Taxonomy row count does not match bitext_meta.json");
  }
  if (rows.some((row) => row.nExamples !== 1000)) {
    throw new Error("Bitext example counts are not uniform in the taxonomy file");
  }
  return rows;
}

export function demandShares(rows: IntentRow[], weights: Record<string, Decimal>): Record<string, Decimal> {
  const names = new Set(rows.map((row) => row.intent));
  const weightNames = new Set(Object.keys(weights));
  const missing = [...names].filter((name) => !weightNames.has(name)).sort();
  const extra = [...weightNames].filter((name) => !names.has(name)).sort();
  if (missing.length > 0 || extra.length > 0) {
    throw new Error(`Demand weights do not match intents. missing=${JSON.stringify(missing)} extra=${JSON.stringify(extra)}`);
  }
  for (const weight of Object.values(weights)) {
    if (weight.lte(0)) throw new Error("Every demand weight must be positive");
  }
  const total = Object.values(weights).reduce((sum, weight) => sum.plus(weight), ZERO);
  const shares: Record<string, Decimal> = {};
  for (const name of Object.keys(weights)) {
    shares[name] = weights[name].div(total);
  }
  return shares;
}

export function classDemand(rows: IntentRow[], shares: Record<string, Decimal>): Record<AutomationClass, Decimal> {
  const totals: Record<AutomationClass, Decimal> = {
    lookup: ZERO,
    structured_transaction: ZERO,
    human_required: ZERO,
  };
  for (const row of rows) {
    totals[row.automationClass] = totals[row.automationClass].plus(shares[row.intent]);
  }
  return totals;
}

export function parseWeightMap(raw: Record<string, string>): Record<string, Decimal> {
  const weights: Record<string, Decimal> = {};
  for (const [intent, value] of Object.entries(raw)) {
    weights[intent] = parseDecimal(value, `demand_weight_by_intent.${intent}`);
  }
  return weights;
}
