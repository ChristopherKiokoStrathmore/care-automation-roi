"use client";

import { CURRENCY_LABEL, getDraftPath, setDraftPath, setRoutingShare, type AssumptionDraft } from "@/lib/assumptions";
import { Decimal } from "@/lib/decimal-util";
import { economicsView, scenarioById, type ModelResult } from "@/lib/evaluate";

import { AssumptionControls, SliderField, type SliderSpec } from "./assumption-controls";
import { TornadoChart } from "./tornado";

export const STUDIO_PATHS = new Set([
  "containment_rate.lookup.ussd_bot",
  "containment_rate.structured_transaction.ussd_bot",
  "containment_scenario_delta",
  "volume.annual_contacts",
  "handle_time_minutes.voice_agent",
  "wages.voice_agent_monthly_wage",
  "investment.bot_build_cost",
  "investment.bot_annual_licence",
  "routing_share.lookup.ussd_bot",
]);

const STUDIO_LEVERS: SliderSpec[] = [
  {
    path: "containment_rate.lookup.ussd_bot",
    label: "Lookup USSD containment",
    min: 0,
    max: 1,
    step: 0.01,
    hint: "Share of lookup contacts offered to USSD that finish there.",
  },
  {
    path: "containment_rate.structured_transaction.ussd_bot",
    label: "Transaction USSD containment",
    min: 0,
    max: 1,
    step: 0.01,
    hint: "Share of structured-transaction contacts offered to USSD that finish there.",
  },
  {
    path: "containment_scenario_delta",
    label: "Low / high containment gap",
    min: 0,
    max: 0.5,
    step: 0.01,
    hint: "Low and high scenarios move every containment rate by this amount, clamped to 0–1.",
  },
  {
    path: "routing_share.lookup.ussd_bot",
    label: "Lookup offered to USSD",
    min: 0,
    max: 1,
    step: 0.01,
    hint: "Voice-agent share of lookup absorbs the change so the class still sums to 1.",
    balanceLookupUssd: true,
  },
  {
    path: "volume.annual_contacts",
    label: "Annual contacts",
    min: 20000,
    max: 300000,
    step: 1000,
    hint: "Offered contacts in a year.",
  },
  {
    path: "handle_time_minutes.voice_agent",
    label: "Voice-agent handle time",
    min: 1,
    max: 30,
    step: 0.1,
    hint: "Minutes. The fully loaded wage applies to this handle time.",
  },
  {
    path: "wages.voice_agent_monthly_wage",
    label: "Voice-agent monthly wage",
    min: 20000,
    max: 200000,
    step: 1000,
    hint: "Monthly wage before the burden rate.",
  },
  {
    path: "investment.bot_build_cost",
    label: "Bot build cost",
    min: 0,
    max: 8000000,
    step: 50000,
    hint: "Spent in year 1. Payback and year-1 ROI use this as the investment.",
  },
  {
    path: "investment.bot_annual_licence",
    label: "Bot annual licence",
    min: 0,
    max: 2000000,
    step: 10000,
    hint: "Subtracted in the net annual benefit. Triage licence is separate.",
  },
];

export const SCENARIO_SHORT: Record<string, string> = {
  baseline_voice_only: "Voice only",
  bot_low: "Low containment",
  bot_base: "Base",
  bot_high: "High containment",
  bot_base_triage: "Emergency routing",
  bot_base_triage_no_quality_value: "No quality value",
};

function asPercent(roi: string): string | null {
  if (!/^[+-]?(?:\d+\.\d+|\d+)$/.test(roi)) return null;
  return `${new Decimal(roi).mul(100).toDecimalPlaces(2, Decimal.ROUND_HALF_UP).toFixed(2)}%`;
}

function paybackNumber(cell: string): number | null {
  if (cell === "not defined" || cell === "does not pay back") return null;
  const parsed = Number(cell);
  return Number.isFinite(parsed) ? parsed : null;
}

function verdictFor(payback: string): { tone: "yes" | "no" | "later" | "na"; text: string } {
  if (payback === "not defined") {
    return { tone: "na", text: "Payback is not defined. Licence and build cost are zero on this scenario." };
  }
  if (payback === "does not pay back") {
    return { tone: "no", text: "Does not pay back. Net annual benefit is not positive, so the build cost is not recovered." };
  }
  const months = Number(payback);
  if (Number.isFinite(months) && months <= 12) {
    return { tone: "yes", text: "Pays back inside year 1." };
  }
  return {
    tone: "later",
    text: "Pays back after year 1. Year-1 ROI is negative because the build cost is spent in year 1.",
  };
}

function applyLever(draft: AssumptionDraft, spec: SliderSpec, value: string): AssumptionDraft {
  if (spec.balanceLookupUssd) return setRoutingShare(draft, "lookup", "ussd_bot", value);
  return setDraftPath(draft, spec.path, value);
}

export function DemoView({
  draft,
  result,
  message,
  selectedId,
  edited,
  headlinesMatch,
  swing,
  shares,
  onDraft,
  onSelect,
  onReset,
}: {
  draft: AssumptionDraft;
  result: ModelResult | null;
  message: string | null;
  selectedId: string;
  edited: boolean;
  headlinesMatch: boolean;
  swing: string;
  shares: Record<string, string> | null;
  onDraft: (next: AssumptionDraft) => void;
  onSelect: (scenarioId: string) => void;
  onReset: () => void;
}) {
  return (
    <div role="tabpanel" id="panel-demo" aria-labelledby="tab-demo">
      {message ? (
        <div className="wrap">
          <p className="alert" role="alert">
            {message}
          </p>
        </div>
      ) : null}

      {result ? (
        <>
          <div className="wrap">
            <ScenarioStrip result={result} selectedId={selectedId} onSelect={onSelect} />
          </div>
          <div className="studio wrap">
            <StudioLevers draft={draft} onDraft={onDraft} />
            <Scoreboard result={result} selectedId={selectedId} edited={edited} headlinesMatch={headlinesMatch} />
          </div>
          <section className="section wrap" aria-label="Payback comparison">
            <div className="section-head">
              <div>
                <h2>Payback by scenario</h2>
                <p className="section-note">
                  Months to recover build cost from net annual benefit. The mark is 12 months. Select a row to read that case in the scoreboard.
                </p>
              </div>
            </div>
            <PaybackChart result={result} selectedId={selectedId} onSelect={onSelect} />
          </section>
          <section className="section wrap" aria-label="Sensitivity tornado">
            <h2>Sensitivity tornado</h2>
            <p className="section-note">
              Each bar is year-1 net cash for the bot programme at base containment when that one assumption moves by the relative swing ({swing}). The other assumptions stay put. Lookup USSD offer moves against the voice-agent share of that class.
              {result.swings[0] ? ` Base year-1 net cash is ${formatBaseCash(result)}.` : ""}
            </p>
            <TornadoChart swings={result.swings} />
            <p className="legend">
              <span>
                <span className="swatch" aria-hidden="true" /> Year-1 net cash from the low input to the high input
              </span>
              <span>
                <span className="swatch signal" aria-hidden="true" /> Base case
              </span>
            </p>
          </section>
        </>
      ) : null}

      <section className="section wrap">
        <details className="drawer">
          <summary>All other assumptions</summary>
          <AssumptionControls
            draft={draft}
            shares={shares}
            edited={edited}
            onDraft={onDraft}
            onReset={onReset}
            excludePaths={STUDIO_PATHS}
            showIntro={false}
          />
        </details>
      </section>
    </div>
  );
}

function formatBaseCash(result: ModelResult): string {
  const selected = scenarioById(result.scenarios, "bot_base");
  return `${economicsView(selected.economics, selected.costPerContact).year1NetCash} ${CURRENCY_LABEL}`;
}

function ScenarioStrip({
  result,
  selectedId,
  onSelect,
}: {
  result: ModelResult;
  selectedId: string;
  onSelect: (scenarioId: string) => void;
}) {
  return (
    <div className="scenario-strip" role="group" aria-label="Scenarios">
      {result.scenarios.map((scenario) => {
        const view = economicsView(scenario.economics, scenario.costPerContact);
        const selected = scenario.scenarioId === selectedId;
        const payback =
          view.paybackMonths === "not defined" || view.paybackMonths === "does not pay back"
            ? view.paybackMonths
            : `${view.paybackMonths} mo`;
        return (
          <button
            key={scenario.scenarioId}
            type="button"
            className={selected ? "scenario-chip is-selected" : "scenario-chip"}
            aria-pressed={selected}
            aria-label={`${scenario.label}. Payback ${payback}. Year-1 ROI ${view.year1Roi}.`}
            onClick={() => onSelect(scenario.scenarioId)}
          >
            <span className="chip-name">{SCENARIO_SHORT[scenario.scenarioId] ?? scenario.label}</span>
            <span className="chip-figure">{payback}</span>
            <span className={`chip-figure${view.year1Roi.startsWith("-") ? " is-negative" : ""}`}>ROI {view.year1Roi}</span>
          </button>
        );
      })}
    </div>
  );
}

function StudioLevers({
  draft,
  onDraft,
}: {
  draft: AssumptionDraft;
  onDraft: (next: AssumptionDraft) => void;
}) {
  const groups: { legend: string; paths: string[] }[] = [
    {
      legend: "Containment",
      paths: [
        "containment_rate.lookup.ussd_bot",
        "containment_rate.structured_transaction.ussd_bot",
        "containment_scenario_delta",
        "routing_share.lookup.ussd_bot",
      ],
    },
    {
      legend: "Volume and labour",
      paths: ["volume.annual_contacts", "handle_time_minutes.voice_agent", "wages.voice_agent_monthly_wage"],
    },
    {
      legend: "Investment",
      paths: ["investment.bot_build_cost", "investment.bot_annual_licence"],
    },
  ];

  return (
    <form className="panel studio-levers" aria-label="Scenario levers" onSubmit={(event) => event.preventDefault()}>
      <h2>Try a case</h2>
      <p className="section-note">Illustrative placeholders. Drag a lever and the scoreboard, payback chart, and tornado update together.</p>
      {groups.map((group) => (
        <fieldset key={group.legend}>
          <legend>{group.legend}</legend>
          <div className="field-grid">
            {group.paths.map((path) => {
              const spec = STUDIO_LEVERS.find((item) => item.path === path);
              if (!spec) return null;
              return (
                <SliderField
                  key={spec.path}
                  idPrefix="studio-"
                  spec={spec}
                  value={getDraftPath(draft, spec.path)}
                  onValue={(value) => onDraft(applyLever(draft, spec, value))}
                />
              );
            })}
          </div>
        </fieldset>
      ))}
    </form>
  );
}

function Scoreboard({
  result,
  selectedId,
  edited,
  headlinesMatch,
}: {
  result: ModelResult;
  selectedId: string;
  edited: boolean;
  headlinesMatch: boolean;
}) {
  const selected = result.scenarios.find((item) => item.scenarioId === selectedId) ?? result.scenarios[0];
  const view = economicsView(selected.economics, selected.costPerContact);
  const verdict = verdictFor(view.paybackMonths);
  const percent = asPercent(view.year1Roi);
  const paybackLong = view.paybackMonths === "not defined" || view.paybackMonths === "does not pay back";

  return (
    <section className="panel board-sticky" aria-label="Live result">
      <p className="kicker">{edited ? "Edited inputs" : headlinesMatch ? "Committed inputs" : "These defaults differ from the committed reports"}</p>
      <h2>{selected.label}</h2>
      <p className={`verdict verdict-${verdict.tone}`}>{verdict.text}</p>
      <div className="scores">
        <article className="score">
          <p className="metric-kicker">Payback</p>
          <p className={paybackLong ? "score-value score-value-long" : "score-value"}>
            {view.paybackMonths}
            {paybackLong ? null : <span className="metric-unit"> months</span>}
          </p>
        </article>
        <article className="score">
          <p className="metric-kicker">Year-1 ROI</p>
          <p className={`score-value${view.year1Roi.startsWith("-") ? " is-negative" : ""}`}>{view.year1Roi}</p>
          <p className="metric-support">{percent ? `${percent} of build cost.` : "Not defined when build cost is zero."}</p>
        </article>
        <article className="score">
          <p className="metric-kicker">Year-1 net cash</p>
          <p className={`score-value score-value-long${view.year1NetCash.startsWith("-") ? " is-negative" : ""}`}>{view.year1NetCash}</p>
          <p className="metric-support">{CURRENCY_LABEL}</p>
        </article>
      </div>
      <h3 className="bridge-title">Year-1 cash build-up</h3>
      <dl className="facts">
        <dt>Cost per contact</dt>
        <dd>{view.costPerContact}</dd>
        <dt>Operating saving versus voice</dt>
        <dd>{view.annualOperatingSaving}</dd>
        <dt>Assumed quality value</dt>
        <dd>{view.assumedQualityValue}</dd>
        <dt>Annual licence</dt>
        <dd>{view.annualLicence}</dd>
        <dt>Net annual benefit</dt>
        <dd>{view.netAnnualBenefit}</dd>
        <dt>Build cost, spent in year 1</dt>
        <dd>{view.capex}</dd>
        <dt>Year-1 net cash</dt>
        <dd>{view.year1NetCash}</dd>
      </dl>
      <p className="section-note follow">{selected.note}</p>
    </section>
  );
}

function PaybackChart({
  result,
  selectedId,
  onSelect,
}: {
  result: ModelResult;
  selectedId: string;
  onSelect: (scenarioId: string) => void;
}) {
  const rows = result.scenarios.map((scenario) => {
    const view = economicsView(scenario.economics, scenario.costPerContact);
    return {
      id: scenario.scenarioId,
      label: scenario.label,
      short: SCENARIO_SHORT[scenario.scenarioId] ?? scenario.label,
      payback: view.paybackMonths,
      numeric: paybackNumber(view.paybackMonths),
    };
  });
  const longest = Math.max(12, ...rows.flatMap((row) => (row.numeric === null ? [] : [row.numeric])));
  const scale = longest * 1.06;
  const yearMark = `${((12 / scale) * 100).toFixed(4)}%`;

  return (
    <>
      <ul className="payback">
        {rows.map((row) => {
          const selected = row.id === selectedId;
          const width = row.numeric === null ? null : `${((row.numeric / scale) * 100).toFixed(4)}%`;
          const shown = row.numeric === null ? row.payback : `${row.payback} mo`;
          return (
            <li key={row.id}>
              <button
                type="button"
                className={selected ? "pay-row is-selected" : "pay-row"}
                aria-pressed={selected}
                aria-label={`${row.label}. Payback ${shown}.`}
                onClick={() => onSelect(row.id)}
              >
                <span className="pay-name">{row.short}</span>
                <span className="pay-track">
                  {width ? <span className="pay-fill" style={{ width }} /> : null}
                  <span className="pay-mark" style={{ left: yearMark }} />
                </span>
                <span className="pay-value">{shown}</span>
              </button>
            </li>
          );
        })}
      </ul>
      <p className="legend">
        <span>
          <span className="swatch" aria-hidden="true" /> Payback
        </span>
        <span>
          <span className="swatch signal" aria-hidden="true" /> 12 months
        </span>
      </p>
    </>
  );
}
