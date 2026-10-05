/**
 * Illustrative placeholders copied from assumptions.yaml.
 * Numeric leaves stay decimal strings until parse so the YAML scalars stay exact.
 */
import { Decimal, ZERO, decToInput, parseDecimal } from "./decimal-util";
import {
  AUTOMATION_CLASSES,
  CONTAINMENT_CHANNELS,
  ROUTING_CHANNELS,
  type AutomationClass,
  type ContainmentChannel,
  type RoutingChannel,
} from "./taxonomy";

export const CURRENCY_CODE = "KES";
export const CURRENCY_LABEL = "KES (illustrative)";
export const ASSUMPTION_NOTE =
  "Every number in this file is an illustrative placeholder, not a real operator figure.";

export const GITHUB_REPO = "https://github.com/ChristopherKiokoStrathmore/care-automation-roi";

export interface AssumptionDraft {
  volume: { annual_contacts: string };
  wages: {
    voice_agent_monthly_wage: string;
    chat_agent_monthly_wage: string;
    senior_agent_monthly_wage: string;
    burden_rate: string;
    monthly_productive_hours: string;
  };
  handle_time_minutes: {
    voice_agent: string;
    senior_agent: string;
    live_chat: string;
    ivr: string;
  };
  channel_variable: {
    voice_telco_per_minute: string;
    ivr_per_minute: string;
    ivr_platform_per_contact: string;
    ussd_per_session: string;
    ussd_sessions_per_contact: string;
    live_chat_platform_per_contact: string;
    chat_bot_platform_per_contact: string;
  };
  routing_share: Record<AutomationClass, Record<RoutingChannel, string>>;
  containment_rate: Record<AutomationClass, Record<ContainmentChannel, string>>;
  containment_scenario_delta: string;
  demand_weight_by_intent: Record<string, string>;
  triage: {
    prevalence: string;
    recall: string;
    precision: string;
    value_per_true_positive: string;
    penalty_per_false_negative: string;
  };
  investment: {
    bot_build_cost: string;
    bot_annual_licence: string;
    triage_build_cost: string;
    triage_annual_licence: string;
  };
  sensitivity_relative_swing: string;
}

export const DEFAULT_DRAFT: AssumptionDraft = {
  volume: { annual_contacts: "120000" },
  wages: {
    voice_agent_monthly_wage: "80000",
    chat_agent_monthly_wage: "70000",
    senior_agent_monthly_wage: "120000",
    burden_rate: "0.30",
    monthly_productive_hours: "140",
  },
  handle_time_minutes: {
    voice_agent: "8",
    senior_agent: "10",
    live_chat: "12",
    ivr: "3",
  },
  channel_variable: {
    voice_telco_per_minute: "1.50",
    ivr_per_minute: "0.80",
    ivr_platform_per_contact: "2.00",
    ussd_per_session: "1.00",
    ussd_sessions_per_contact: "1.20",
    live_chat_platform_per_contact: "3.00",
    chat_bot_platform_per_contact: "3.00",
  },
  routing_share: {
    lookup: { ussd_bot: "0.80", chat_bot: "0.10", ivr: "0.05", voice_agent: "0.05" },
    structured_transaction: { ussd_bot: "0.30", chat_bot: "0.20", ivr: "0.10", voice_agent: "0.40" },
    human_required: { ussd_bot: "0.00", chat_bot: "0.00", ivr: "0.10", voice_agent: "0.90" },
  },
  containment_rate: {
    lookup: { ussd_bot: "0.70", chat_bot: "0.65", ivr: "0.50" },
    structured_transaction: { ussd_bot: "0.40", chat_bot: "0.45", ivr: "0.20" },
    human_required: { ussd_bot: "0.00", chat_bot: "0.00", ivr: "0.00" },
  },
  containment_scenario_delta: "0.20",
  demand_weight_by_intent: {
    check_usage: "140",
    invoices: "90",
    check_mobile_payments: "50",
    payment_methods: "30",
    check_excess_data_charges: "40",
    check_signal_coverage: "35",
    check_cancellation_fee: "15",
    pay: "100",
    schedule_payments: "25",
    set_usage_limits: "20",
    change_plan: "45",
    sign_up_for_plan: "30",
    activate_roaming: "20",
    activate_call_management_services: "15",
    deactivate_call_management_services: "10",
    report_problem: "80",
    report_poor_signal_coverage: "40",
    dispute_invoice: "35",
    get_compensation: "20",
    human_agent: "45",
    customer_service: "30",
    cancel_plan: "25",
    change_provider: "15",
    activate_phone: "15",
    deactivate_phone: "10",
    install_internet: "20",
  },
  triage: {
    prevalence: "0.08",
    recall: "0.75",
    precision: "0.40",
    value_per_true_positive: "250",
    penalty_per_false_negative: "250",
  },
  investment: {
    bot_build_cost: "2500000",
    bot_annual_licence: "600000",
    triage_build_cost: "400000",
    triage_annual_licence: "180000",
  },
  sensitivity_relative_swing: "0.20",
};

export interface RawAssumptions {
  volume: { annual_contacts: Decimal };
  wages: {
    voice_agent_monthly_wage: Decimal;
    chat_agent_monthly_wage: Decimal;
    senior_agent_monthly_wage: Decimal;
    burden_rate: Decimal;
    monthly_productive_hours: Decimal;
  };
  handle_time_minutes: {
    voice_agent: Decimal;
    senior_agent: Decimal;
    live_chat: Decimal;
    ivr: Decimal;
  };
  channel_variable: {
    voice_telco_per_minute: Decimal;
    ivr_per_minute: Decimal;
    ivr_platform_per_contact: Decimal;
    ussd_per_session: Decimal;
    ussd_sessions_per_contact: Decimal;
    live_chat_platform_per_contact: Decimal;
    chat_bot_platform_per_contact: Decimal;
  };
  routing_share: Record<AutomationClass, Record<RoutingChannel, Decimal>>;
  containment_rate: Record<AutomationClass, Record<ContainmentChannel, Decimal>>;
  containment_scenario_delta: Decimal;
  demand_weight_by_intent: Record<string, Decimal>;
  triage: {
    prevalence: Decimal;
    recall: Decimal;
    precision: Decimal;
    value_per_true_positive: Decimal;
    penalty_per_false_negative: Decimal;
  };
  investment: {
    bot_build_cost: Decimal;
    bot_annual_licence: Decimal;
    triage_build_cost: Decimal;
    triage_annual_licence: Decimal;
  };
  sensitivity_relative_swing: Decimal;
}

export interface Assumptions {
  currencyCode: string;
  currencyLabel: string;
  note: string;
  annualContacts: Decimal;
  voiceAgentMonthlyWage: Decimal;
  chatAgentMonthlyWage: Decimal;
  seniorAgentMonthlyWage: Decimal;
  burdenRate: Decimal;
  monthlyProductiveHours: Decimal;
  ahtVoiceAgent: Decimal;
  ahtSeniorAgent: Decimal;
  ahtLiveChat: Decimal;
  ahtIvr: Decimal;
  voiceTelcoPerMinute: Decimal;
  ivrPerMinute: Decimal;
  ivrPlatformPerContact: Decimal;
  ussdPerSession: Decimal;
  ussdSessionsPerContact: Decimal;
  liveChatPlatformPerContact: Decimal;
  chatBotPlatformPerContact: Decimal;
  routingShare: Record<AutomationClass, Record<RoutingChannel, Decimal>>;
  containmentRate: Record<AutomationClass, Record<ContainmentChannel, Decimal>>;
  containmentScenarioDelta: Decimal;
  demandWeightByIntent: Record<string, Decimal>;
  triagePrevalence: Decimal;
  triageRecall: Decimal;
  triagePrecision: Decimal;
  valuePerTruePositive: Decimal;
  penaltyPerFalseNegative: Decimal;
  botBuildCost: Decimal;
  botAnnualLicence: Decimal;
  triageBuildCost: Decimal;
  triageAnnualLicence: Decimal;
  sensitivityRelativeSwing: Decimal;
}

export function cloneDraft(draft: AssumptionDraft = DEFAULT_DRAFT): AssumptionDraft {
  return structuredClone(draft);
}

export function draftsEqual(left: AssumptionDraft, right: AssumptionDraft): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

export function getDraftPath(draft: AssumptionDraft, path: string): string {
  const node = walkDraft(draft, path);
  if (typeof node !== "string") throw new Error(`${path} is not a field`);
  return node;
}

export function setRoutingShare(
  draft: AssumptionDraft,
  className: AutomationClass,
  channel: RoutingChannel,
  value: string,
): AssumptionDraft {
  const next = setDraftPath(draft, `routing_share.${className}.${channel}`, value);
  if (channel === "voice_agent") return next;
  const shares = next.routing_share[className];
  try {
    const voice = new Decimal(1).minus(shares.ussd_bot).minus(shares.chat_bot).minus(shares.ivr);
    if (voice.gte(0) && voice.lte(1)) {
      shares.voice_agent = decToInput(voice);
    } else if (voice.lt(0)) {
      const capped = new Decimal(shares[channel]).plus(voice);
      if (capped.gte(0) && capped.lte(1)) {
        shares[channel] = decToInput(capped);
        shares.voice_agent = "0";
      }
    }
  } catch {
    return next;
  }
  return next;
}

export function setDraftPath(draft: AssumptionDraft, path: string, value: string): AssumptionDraft {
  const next = cloneDraft(draft);
  const parts = path.split(".");
  let node: Record<string, unknown> = next as unknown as Record<string, unknown>;
  for (const part of parts.slice(0, -1)) {
    const child = node[part];
    if (!child || typeof child !== "object") throw new Error(`Unknown assumption path ${path}`);
    node = child as Record<string, unknown>;
  }
  const leaf = parts[parts.length - 1];
  if (!(leaf in node)) throw new Error(`Unknown assumption path ${path}`);
  node[leaf] = value;
  return next;
}

function walkDraft(draft: AssumptionDraft, path: string): unknown {
  const parts = path.split(".");
  let node: unknown = draft;
  for (const part of parts) {
    if (!node || typeof node !== "object" || !(part in node)) {
      throw new Error(`Unknown assumption path ${path}`);
    }
    node = (node as Record<string, unknown>)[part];
  }
  return node;
}

function between(value: Decimal, low: Decimal, high: Decimal, path: string): void {
  if (value.lt(low) || value.gt(high)) {
    throw new Error(`${path} must be between ${low.toString()} and ${high.toString()}, got ${value.toString()}`);
  }
}

function sumChannelShares(shares: Record<string, Decimal>): Decimal {
  return Object.values(shares).reduce((total, share) => total.plus(share), ZERO);
}

export function parseDraft(draft: AssumptionDraft): RawAssumptions {
  const num = (path: string) => parseDecimal(getDraftPath(draft, path), path);
  const routing = {} as RawAssumptions["routing_share"];
  const containment = {} as RawAssumptions["containment_rate"];
  for (const name of AUTOMATION_CLASSES) {
    routing[name] = {
      ussd_bot: num(`routing_share.${name}.ussd_bot`),
      chat_bot: num(`routing_share.${name}.chat_bot`),
      ivr: num(`routing_share.${name}.ivr`),
      voice_agent: num(`routing_share.${name}.voice_agent`),
    };
    containment[name] = {
      ussd_bot: num(`containment_rate.${name}.ussd_bot`),
      chat_bot: num(`containment_rate.${name}.chat_bot`),
      ivr: num(`containment_rate.${name}.ivr`),
    };
  }
  const demand: Record<string, Decimal> = {};
  for (const intent of Object.keys(draft.demand_weight_by_intent)) {
    demand[intent] = num(`demand_weight_by_intent.${intent}`);
  }
  return {
    volume: { annual_contacts: num("volume.annual_contacts") },
    wages: {
      voice_agent_monthly_wage: num("wages.voice_agent_monthly_wage"),
      chat_agent_monthly_wage: num("wages.chat_agent_monthly_wage"),
      senior_agent_monthly_wage: num("wages.senior_agent_monthly_wage"),
      burden_rate: num("wages.burden_rate"),
      monthly_productive_hours: num("wages.monthly_productive_hours"),
    },
    handle_time_minutes: {
      voice_agent: num("handle_time_minutes.voice_agent"),
      senior_agent: num("handle_time_minutes.senior_agent"),
      live_chat: num("handle_time_minutes.live_chat"),
      ivr: num("handle_time_minutes.ivr"),
    },
    channel_variable: {
      voice_telco_per_minute: num("channel_variable.voice_telco_per_minute"),
      ivr_per_minute: num("channel_variable.ivr_per_minute"),
      ivr_platform_per_contact: num("channel_variable.ivr_platform_per_contact"),
      ussd_per_session: num("channel_variable.ussd_per_session"),
      ussd_sessions_per_contact: num("channel_variable.ussd_sessions_per_contact"),
      live_chat_platform_per_contact: num("channel_variable.live_chat_platform_per_contact"),
      chat_bot_platform_per_contact: num("channel_variable.chat_bot_platform_per_contact"),
    },
    routing_share: routing,
    containment_rate: containment,
    containment_scenario_delta: num("containment_scenario_delta"),
    demand_weight_by_intent: demand,
    triage: {
      prevalence: num("triage.prevalence"),
      recall: num("triage.recall"),
      precision: num("triage.precision"),
      value_per_true_positive: num("triage.value_per_true_positive"),
      penalty_per_false_negative: num("triage.penalty_per_false_negative"),
    },
    investment: {
      bot_build_cost: num("investment.bot_build_cost"),
      bot_annual_licence: num("investment.bot_annual_licence"),
      triage_build_cost: num("investment.triage_build_cost"),
      triage_annual_licence: num("investment.triage_annual_licence"),
    },
    sensitivity_relative_swing: num("sensitivity_relative_swing"),
  };
}

export function cloneRaw(raw: RawAssumptions): RawAssumptions {
  const walk = (node: unknown): unknown => {
    if (Decimal.isDecimal(node)) return new Decimal(node as Decimal);
    if (Array.isArray(node)) return node.map(walk);
    if (node && typeof node === "object") {
      const copy: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(node)) copy[key] = walk(value);
      return copy;
    }
    return node;
  };
  return walk(raw) as RawAssumptions;
}

export function getRawPath(data: RawAssumptions, path: string): Decimal {
  const parts = path.split(".");
  let node: unknown = data;
  for (const part of parts) {
    if (!node || typeof node !== "object" || !(part in (node as object))) {
      throw new Error(`Unknown assumption path ${path}`);
    }
    node = (node as Record<string, unknown>)[part];
  }
  if (!Decimal.isDecimal(node)) throw new Error(`${path} is not a number`);
  return node;
}

export function setRawPath(data: RawAssumptions, path: string, value: Decimal): void {
  const parts = path.split(".");
  let node: Record<string, unknown> = data as unknown as Record<string, unknown>;
  for (const part of parts.slice(0, -1)) {
    const child = node[part];
    if (!child || typeof child !== "object") throw new Error(`Unknown assumption path ${path}`);
    node = child as Record<string, unknown>;
  }
  const leaf = parts[parts.length - 1];
  if (!(leaf in node)) throw new Error(`Unknown assumption path ${path}`);
  node[leaf] = value;
}

export function validate(data: RawAssumptions): Assumptions {
  const annualContacts = data.volume.annual_contacts;
  if (annualContacts.lte(0)) throw new Error("volume.annual_contacts must be positive");

  const burden = data.wages.burden_rate;
  const hours = data.wages.monthly_productive_hours;
  between(burden, ZERO, new Decimal(2), "wages.burden_rate");
  if (hours.lte(0)) throw new Error("wages.monthly_productive_hours must be positive");

  for (const name of AUTOMATION_CLASSES) {
    const shares = data.routing_share[name];
    for (const channel of ROUTING_CHANNELS) {
      between(shares[channel], ZERO, new Decimal(1), `routing_share.${name}.${channel}`);
    }
    const total = sumChannelShares(shares);
    if (!total.eq(1)) {
      throw new Error(`routing_share.${name} shares sum to ${total.toString()}, expected 1`);
    }
    for (const channel of CONTAINMENT_CHANNELS) {
      between(data.containment_rate[name][channel], ZERO, new Decimal(1), `containment_rate.${name}.${channel}`);
    }
  }

  between(data.containment_scenario_delta, ZERO, new Decimal(1), "containment_scenario_delta");
  between(data.sensitivity_relative_swing, ZERO, new Decimal("0.9"), "sensitivity_relative_swing");

  for (const [intent, weight] of Object.entries(data.demand_weight_by_intent)) {
    if (weight.lte(0)) throw new Error(`demand_weight_by_intent.${intent} must be positive`);
  }

  between(data.triage.prevalence, ZERO, new Decimal(1), "triage.prevalence");
  between(data.triage.recall, ZERO, new Decimal(1), "triage.recall");
  between(data.triage.precision, ZERO, new Decimal(1), "triage.precision");
  if (data.triage.value_per_true_positive.lt(0) || data.triage.penalty_per_false_negative.lt(0)) {
    throw new Error("triage value and penalty must be non-negative");
  }

  return {
    currencyCode: CURRENCY_CODE,
    currencyLabel: CURRENCY_LABEL,
    note: ASSUMPTION_NOTE,
    annualContacts,
    voiceAgentMonthlyWage: data.wages.voice_agent_monthly_wage,
    chatAgentMonthlyWage: data.wages.chat_agent_monthly_wage,
    seniorAgentMonthlyWage: data.wages.senior_agent_monthly_wage,
    burdenRate: burden,
    monthlyProductiveHours: hours,
    ahtVoiceAgent: data.handle_time_minutes.voice_agent,
    ahtSeniorAgent: data.handle_time_minutes.senior_agent,
    ahtLiveChat: data.handle_time_minutes.live_chat,
    ahtIvr: data.handle_time_minutes.ivr,
    voiceTelcoPerMinute: data.channel_variable.voice_telco_per_minute,
    ivrPerMinute: data.channel_variable.ivr_per_minute,
    ivrPlatformPerContact: data.channel_variable.ivr_platform_per_contact,
    ussdPerSession: data.channel_variable.ussd_per_session,
    ussdSessionsPerContact: data.channel_variable.ussd_sessions_per_contact,
    liveChatPlatformPerContact: data.channel_variable.live_chat_platform_per_contact,
    chatBotPlatformPerContact: data.channel_variable.chat_bot_platform_per_contact,
    routingShare: data.routing_share,
    containmentRate: data.containment_rate,
    containmentScenarioDelta: data.containment_scenario_delta,
    demandWeightByIntent: data.demand_weight_by_intent,
    triagePrevalence: data.triage.prevalence,
    triageRecall: data.triage.recall,
    triagePrecision: data.triage.precision,
    valuePerTruePositive: data.triage.value_per_true_positive,
    penaltyPerFalseNegative: data.triage.penalty_per_false_negative,
    botBuildCost: data.investment.bot_build_cost,
    botAnnualLicence: data.investment.bot_annual_licence,
    triageBuildCost: data.investment.triage_build_cost,
    triageAnnualLicence: data.investment.triage_annual_licence,
    sensitivityRelativeSwing: data.sensitivity_relative_swing,
  };
}
