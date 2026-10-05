import {
  setDraftPath,
  setRoutingShare,
  type AssumptionDraft,
} from "@/lib/assumptions";
import { Decimal, decToInput } from "@/lib/decimal-util";
import { CLASS_LABEL } from "@/lib/evaluate";
import {
  AUTOMATION_CLASSES,
  ROUTING_CHANNELS,
  loadIntents,
  type AutomationClass,
  type ContainmentChannel,
  type RoutingChannel,
} from "@/lib/taxonomy";

const INTENTS = loadIntents();

interface SliderSpec {
  path: string;
  label: string;
  min: number;
  max: number;
  step: number;
  hint: string;
  balanceLookupUssd?: boolean;
}

const DRIVERS: SliderSpec[] = [
  { path: "handle_time_minutes.voice_agent", label: "Voice-agent handle time", min: 1, max: 30, step: 0.1, hint: "Minutes. The fully loaded wage applies to this handle time." },
  { path: "volume.annual_contacts", label: "Annual contacts", min: 20000, max: 300000, step: 1000, hint: "Offered contacts in a year." },
  { path: "wages.monthly_productive_hours", label: "Monthly productive hours", min: 40, max: 220, step: 1, hint: "Hours available for contacts. The divisor in the hourly wage." },
  { path: "wages.voice_agent_monthly_wage", label: "Voice-agent monthly wage", min: 20000, max: 200000, step: 1000, hint: "Monthly wage before the burden rate." },
  { path: "containment_rate.lookup.ussd_bot", label: "Lookup USSD containment", min: 0, max: 1, step: 0.01, hint: "Share of lookup contacts offered to USSD that finish there." },
  { path: "investment.bot_build_cost", label: "Bot build cost", min: 0, max: 8000000, step: 50000, hint: "Spent in year 1. Payback and year-1 ROI use this as the investment." },
  {
    path: "routing_share.lookup.ussd_bot",
    label: "Lookup USSD offer share",
    min: 0,
    max: 1,
    step: 0.01,
    hint: "Voice-agent share of lookup absorbs the change so the class still sums to 1.",
    balanceLookupUssd: true,
  },
  { path: "wages.burden_rate", label: "Wage burden rate", min: 0, max: 1, step: 0.01, hint: "Added to the monthly wage before dividing by productive hours." },
  { path: "investment.bot_annual_licence", label: "Bot annual licence", min: 0, max: 2000000, step: 10000, hint: "Subtracted in the net annual benefit. Triage licence is separate." },
  { path: "containment_rate.structured_transaction.ussd_bot", label: "Transaction USSD containment", min: 0, max: 1, step: 0.01, hint: "Share of structured-transaction contacts offered to USSD that finish there." },
  { path: "channel_variable.ussd_per_session", label: "USSD cost per session", min: 0, max: 10, step: 0.05, hint: "Times sessions per contact for the USSD unit cost." },
];

const LABOUR: SliderSpec[] = [
  { path: "wages.chat_agent_monthly_wage", label: "Chat-agent monthly wage", min: 20000, max: 200000, step: 1000, hint: "Used for staffed chat. Staffed chat is not in the routing mix." },
  { path: "wages.senior_agent_monthly_wage", label: "Senior-agent monthly wage", min: 20000, max: 250000, step: 1000, hint: "Predicted emergency contacts pay this unit cost." },
  { path: "handle_time_minutes.senior_agent", label: "Senior-agent handle time", min: 1, max: 30, step: 0.1, hint: "Minutes." },
  { path: "handle_time_minutes.live_chat", label: "Staffed-chat handle time", min: 1, max: 30, step: 0.1, hint: "Minutes. Telecom per-minute charge is not applied." },
  { path: "handle_time_minutes.ivr", label: "IVR handle time", min: 0, max: 15, step: 0.1, hint: "Minutes, times the IVR per-minute charge." },
];

const CHANNELS: SliderSpec[] = [
  { path: "channel_variable.voice_telco_per_minute", label: "Voice telecom per minute", min: 0, max: 10, step: 0.05, hint: "Charged on voice-agent and senior-agent handle time." },
  { path: "channel_variable.ivr_per_minute", label: "IVR per minute", min: 0, max: 10, step: 0.05, hint: "Times IVR handle time." },
  { path: "channel_variable.ivr_platform_per_contact", label: "IVR platform per contact", min: 0, max: 20, step: 0.1, hint: "Added once per IVR contact." },
  { path: "channel_variable.ussd_per_session", label: "USSD cost per session", min: 0, max: 10, step: 0.05, hint: "Same input as the tornado driver." },
  { path: "channel_variable.ussd_sessions_per_contact", label: "USSD sessions per contact", min: 0, max: 5, step: 0.05, hint: "Times the session cost." },
  { path: "channel_variable.live_chat_platform_per_contact", label: "Staffed-chat platform per contact", min: 0, max: 20, step: 0.1, hint: "Added to the staffed-chat wage cost." },
  { path: "channel_variable.chat_bot_platform_per_contact", label: "Chat-bot platform per contact", min: 0, max: 20, step: 0.1, hint: "The whole unstaffed chat-bot unit cost." },
];

const PROGRAMME: SliderSpec[] = [
  { path: "containment_scenario_delta", label: "Containment scenario delta", min: 0, max: 0.5, step: 0.01, hint: "Low and high scenarios move every containment rate by this amount, clamped to 0–1." },
  { path: "investment.triage_build_cost", label: "Triage build cost", min: 0, max: 3000000, step: 10000, hint: "Added to the bot build cost on the triage scenarios." },
  { path: "investment.triage_annual_licence", label: "Triage annual licence", min: 0, max: 1000000, step: 5000, hint: "Added to the bot licence on the triage scenarios." },
  { path: "sensitivity_relative_swing", label: "Sensitivity relative swing", min: 0, max: 0.9, step: 0.01, hint: "Each tornado bar moves one assumption by this fraction, up and down." },
];

const TRIAGE: SliderSpec[] = [
  { path: "triage.prevalence", label: "Emergency prevalence", min: 0, max: 1, step: 0.01, hint: "Assumed share of contacts that are emergencies." },
  { path: "triage.recall", label: "Recall", min: 0, max: 1, step: 0.01, hint: "Assumed. Precision must be at least recall times prevalence." },
  { path: "triage.precision", label: "Precision", min: 0.01, max: 1, step: 0.01, hint: "Assumed. A zero precision makes the predicted-positive rate undefined." },
  { path: "triage.value_per_true_positive", label: "Value per true positive", min: 0, max: 2000, step: 10, hint: "Booked only on the triage scenario that includes quality value." },
  { path: "triage.penalty_per_false_negative", label: "Penalty per false negative", min: 0, max: 2000, step: 10, hint: "Subtracted in that same quality column." },
];

const CHANNEL_LABEL: Record<RoutingChannel | ContainmentChannel, string> = {
  ussd_bot: "USSD bot",
  chat_bot: "Chat bot",
  ivr: "IVR",
  voice_agent: "Voice agent",
};

const EXTRA_CONTAINMENT: { className: AutomationClass; channel: ContainmentChannel }[] = [
  { className: "lookup", channel: "chat_bot" },
  { className: "lookup", channel: "ivr" },
  { className: "structured_transaction", channel: "chat_bot" },
  { className: "structured_transaction", channel: "ivr" },
  { className: "human_required", channel: "ussd_bot" },
  { className: "human_required", channel: "chat_bot" },
  { className: "human_required", channel: "ivr" },
];

function stepPlaces(step: number): number {
  const text = String(step);
  const dot = text.indexOf(".");
  return dot === -1 ? 0 : text.length - dot - 1;
}

function snapToStep(raw: string, step: number): string {
  try {
    return decToInput(new Decimal(raw).toDecimalPlaces(stepPlaces(step), Decimal.ROUND_HALF_UP));
  } catch {
    return raw;
  }
}

function rangeValue(raw: string, min: number, max: number): string {
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return String(min);
  return String(Math.min(max, Math.max(min, parsed)));
}

function readPath(draft: AssumptionDraft, path: string): string {
  const parts = path.split(".");
  let node: unknown = draft;
  for (const part of parts) {
    if (!node || typeof node !== "object" || !(part in node)) return "";
    node = (node as Record<string, unknown>)[part];
  }
  return typeof node === "string" ? node : "";
}

function SliderField({
  spec,
  value,
  onValue,
  idPrefix,
}: {
  spec: SliderSpec;
  value: string;
  onValue: (value: string) => void;
  idPrefix: string;
}) {
  const fieldId = `${idPrefix}${spec.path.replaceAll(".", "-")}`;
  const labelId = `${fieldId}-label`;
  const hintId = `${fieldId}-hint`;
  return (
    <div className="field">
      <label className="field-label" id={labelId} htmlFor={fieldId}>
        {spec.label}
      </label>
      <span className="field-control">
        <input
          type="range"
          min={spec.min}
          max={spec.max}
          step={spec.step}
          value={rangeValue(value, spec.min, spec.max)}
          aria-labelledby={labelId}
          onChange={(event) => onValue(snapToStep(event.target.value, spec.step))}
        />
        <input
          id={fieldId}
          type="text"
          inputMode="decimal"
          autoComplete="off"
          aria-describedby={hintId}
          value={value}
          onChange={(event) => onValue(event.target.value)}
        />
      </span>
      <span className="field-hint" id={hintId}>
        {spec.hint}
      </span>
    </div>
  );
}

function shareSum(shares: Record<RoutingChannel, string>): { text: string; ok: boolean } {
  try {
    const total = ROUTING_CHANNELS.reduce((sum, channel) => sum.plus(shares[channel]), new Decimal(0));
    if (total.eq(1)) return { text: "Sum 1", ok: true };
    return { text: `Sum ${decToInput(total)}, expected 1`, ok: false };
  } catch {
    return { text: "Enter a number in each share", ok: false };
  }
}

export function AssumptionControls({
  draft,
  shares,
  edited,
  onDraft,
  onReset,
}: {
  draft: AssumptionDraft;
  shares: Record<string, string> | null;
  edited: boolean;
  onDraft: (next: AssumptionDraft) => void;
  onReset: () => void;
}) {
  const apply = (spec: SliderSpec, value: string) => {
    if (spec.balanceLookupUssd) {
      onDraft(setRoutingShare(draft, "lookup", "ussd_bot", value));
      return;
    }
    onDraft(setDraftPath(draft, spec.path, value));
  };

  return (
    <>
      <div className="control-bar wrap">
        <div>
          <h2>Assumptions</h2>
          <p className="section-note">
            Every control writes the same input the model reads. Sliders recompute payback, year-1 ROI, the six scenarios, and the tornado.
          </p>
        </div>
        <button type="button" className="button" onClick={onReset} disabled={!edited}>
          Reset to committed inputs
        </button>
      </div>
      <div className="wrap">
        <fieldset>
          <legend>What the tornado moves</legend>
          <div className="field-grid">
            {DRIVERS.map((spec) => (
              <SliderField key={spec.path} idPrefix="tornado-" spec={spec} value={readPath(draft, spec.path)} onValue={(value) => apply(spec, value)} />
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend>Programme and other containment</legend>
          <div className="field-grid">
            {PROGRAMME.map((spec) => (
              <SliderField key={spec.path} idPrefix="programme-" spec={spec} value={readPath(draft, spec.path)} onValue={(value) => apply(spec, value)} />
            ))}
            {EXTRA_CONTAINMENT.map(({ className, channel }) => {
              const spec: SliderSpec = {
                path: `containment_rate.${className}.${channel}`,
                label: `${CLASS_LABEL[className]} ${CHANNEL_LABEL[channel]} containment`,
                min: 0,
                max: 1,
                step: 0.01,
                hint: "Probability the contact finishes on this channel.",
              };
              return <SliderField key={spec.path} idPrefix="containment-" spec={spec} value={readPath(draft, spec.path)} onValue={(value) => apply(spec, value)} />;
            })}
          </div>
        </fieldset>

        <fieldset>
          <legend>Other labour</legend>
          <div className="field-grid">
            {LABOUR.map((spec) => (
              <SliderField key={spec.path} idPrefix="labour-" spec={spec} value={readPath(draft, spec.path)} onValue={(value) => apply(spec, value)} />
            ))}
          </div>
        </fieldset>

        <details className="drawer">
          <summary>Routing shares</summary>
          <p className="section-note">
            Each class sums to 1. Moving USSD, chat bot, or IVR sets the voice-agent share to the residual when that residual stays inside 0–1. Voice agent means the contact is served with no automation attempt.
          </p>
          {AUTOMATION_CLASSES.map((className) => {
            const total = shareSum(draft.routing_share[className]);
            return (
              <div className="class-block" key={className}>
                <h3>{CLASS_LABEL[className]}</h3>
                <div className="field-grid">
                  {ROUTING_CHANNELS.map((channel) => {
                    const spec: SliderSpec = {
                      path: `routing_share.${className}.${channel}`,
                      label: CHANNEL_LABEL[channel],
                      min: 0,
                      max: 1,
                      step: 0.01,
                      hint: channel === "voice_agent" ? "Direct to a voice agent." : "Offer share for this channel.",
                    };
                    return (
                      <SliderField
                        key={spec.path}
                        idPrefix="route-"
                        spec={spec}
                        value={draft.routing_share[className][channel]}
                        onValue={(value) => onDraft(setRoutingShare(draft, className, channel, value))}
                      />
                    );
                  })}
                </div>
                <p className={total.ok ? "sum-line" : "sum-line is-off"}>{total.text}</p>
              </div>
            );
          })}
        </details>

        <details className="drawer">
          <summary>Channel charges</summary>
          <div className="field-grid">
            {CHANNELS.map((spec) => (
              <SliderField key={spec.path} idPrefix="charge-" spec={spec} value={readPath(draft, spec.path)} onValue={(value) => apply(spec, value)} />
            ))}
          </div>
        </details>

        <details className="drawer">
          <summary>Triage assumptions</summary>
          <p className="section-note">
            Precision and recall are assumptions. They have to be able to sit in one confusion matrix. The quality value is reported on its own and is removed in the last scenario.
          </p>
          <div className="field-grid">
            {TRIAGE.map((spec) => (
              <SliderField key={spec.path} idPrefix="triage-" spec={spec} value={readPath(draft, spec.path)} onValue={(value) => apply(spec, value)} />
            ))}
          </div>
        </details>

        <details className="drawer">
          <summary>Demand weights</summary>
          <p className="section-note">
            A weight divided by the sum of the weights is the demand share. The Bitext training count stays at 1,000 for every intent and never enters the arithmetic.
          </p>
          {AUTOMATION_CLASSES.map((className) => (
            <div className="class-block" key={className}>
              <h3>{CLASS_LABEL[className]}</h3>
              <div className="field-grid">
                {INTENTS.filter((row) => row.automationClass === className).map((row) => {
                  const spec: SliderSpec = {
                    path: `demand_weight_by_intent.${row.intent}`,
                    label: row.intent,
                    min: 1,
                    max: 400,
                    step: 1,
                    hint: shares ? `Share ${shares[row.intent]}. ${row.category}.` : `${row.category}.`,
                  };
                  return (
                    <SliderField
                      key={row.intent}
                      idPrefix="demand-"
                      spec={spec}
                      value={draft.demand_weight_by_intent[row.intent]}
                      onValue={(value) => onDraft(setDraftPath(draft, spec.path, value))}
                    />
                  );
                })}
              </div>
            </div>
          ))}
          <ol className="rule-list">
            <li>If the Bitext category is COMPLAINTS, the class is human required.</li>
            <li>Named service, cancellation, provider-change, and dispute intents are human required.</li>
            <li>Intents that start with check_, plus invoices and payment methods, are lookup.</li>
            <li>Pay, plan change, roaming, limits, and call-management intents are structured transactions.</li>
          </ol>
        </details>
      </div>
    </>
  );
}
