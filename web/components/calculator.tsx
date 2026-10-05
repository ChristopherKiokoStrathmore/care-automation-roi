"use client";

import { useMemo, useState } from "react";

import {
  CURRENCY_LABEL,
  DEFAULT_DRAFT,
  GITHUB_REPO,
  cloneDraft,
  draftsEqual,
  type AssumptionDraft,
} from "@/lib/assumptions";
import { Decimal, fmtMoney, fmtRate } from "@/lib/decimal-util";
import { committedHeadlineMatch, economicsView, evaluate, scenarioById, type ModelResult } from "@/lib/evaluate";

import { AssumptionControls } from "./assumption-controls";
import { CostPanels } from "./cost-panels";
import { ScenarioTable } from "./scenario-table";
import { TornadoChart } from "./tornado";

function asPercent(roi: string): string | null {
  if (!/^[+-]?(?:\d+\.\d+|\d+)$/.test(roi)) return null;
  return `${new Decimal(roi).mul(100).toDecimalPlaces(2, Decimal.ROUND_HALF_UP).toFixed(2)}%`;
}

export function Calculator() {
  const [draft, setDraft] = useState<AssumptionDraft>(() => cloneDraft());
  const [selectedId, setSelectedId] = useState("bot_base");
  const evaluation = useMemo(() => evaluate(draft), [draft]);
  const edited = !draftsEqual(draft, DEFAULT_DRAFT);
  const shares = evaluation.ok
    ? Object.fromEntries(Object.entries(evaluation.result.intentShares).map(([intent, share]) => [intent, fmtRate(share)]))
    : null;

  return (
    <main id="calculator">
      <header className="masthead wrap">
        <p className="kicker">Illustrative cost-benefit</p>
        <h1>Contact-centre automation ROI</h1>
        <p className="lede">
          A contact centre saves money when bot contacts stay contained, and only after licence and build cost. Move an assumption and the scenarios, payback, year-1 ROI, and tornado recompute from the same formulas as the Python model.
        </p>
      </header>

      {evaluation.ok ? (
        <Results
          result={evaluation.result}
          selectedId={selectedId}
          onSelect={setSelectedId}
          edited={edited}
          swing={draft.sensitivity_relative_swing}
        />
      ) : (
        <div className="wrap">
          <p className="alert" role="alert">
            {evaluation.message}
          </p>
        </div>
      )}

      <section className="controls" aria-label="Editable assumptions">
        <AssumptionControls
          draft={draft}
          shares={shares}
          edited={edited}
          onDraft={setDraft}
          onReset={() => {
            setDraft(cloneDraft(DEFAULT_DRAFT));
            setSelectedId("bot_base");
          }}
        />
      </section>

      <footer className="footer wrap">
        <p>Illustrative inputs. Currency is {CURRENCY_LABEL}.</p>
        <a href={GITHUB_REPO}>github.com/ChristopherKiokoStrathmore/care-automation-roi</a>
      </footer>
    </main>
  );
}

function Results({
  result,
  selectedId,
  onSelect,
  edited,
  swing,
}: {
  result: ModelResult;
  selectedId: string;
  onSelect: (scenarioId: string) => void;
  edited: boolean;
  swing: string;
}) {
  const base = scenarioById(result.scenarios, "bot_base");
  const low = scenarioById(result.scenarios, "bot_low");
  const baseView = economicsView(base.economics, base.costPerContact);
  const lowView = economicsView(low.economics, low.costPerContact);
  const basePercent = asPercent(baseView.year1Roi);
  const lowPercent = asPercent(lowView.year1Roi);
  const headlinesMatch = committedHeadlineMatch(result);
  const baseCash = result.swings[0]?.baseYear1NetCash;

  return (
    <>
      <section className="wrap" aria-label="Headline results">
        <div className="metrics">
          <article className="metric">
            <p className="metric-kicker">Base-case payback</p>
            <p className={`metric-value${baseView.paybackMonths.length > 8 ? " metric-value-long" : ""}`}>
              {baseView.paybackMonths}
              {baseView.paybackMonths !== "not defined" && baseView.paybackMonths !== "does not pay back" ? (
                <span className="metric-unit"> months</span>
              ) : null}
            </p>
            <p className="metric-support">Bot programme at base containment. Currency is {CURRENCY_LABEL}.</p>
          </article>
          <article className="metric">
            <p className="metric-kicker">Year-1 ROI</p>
            <p className={`metric-value${baseView.year1Roi.startsWith("-") ? " is-negative" : ""}`}>{baseView.year1Roi}</p>
            <p className="metric-support">
              {basePercent ? `${basePercent} of build cost in year 1. ` : ""}
              Net cash {baseView.year1NetCash} {CURRENCY_LABEL}.
            </p>
          </article>
          <article className="metric">
            <p className="metric-kicker">Low-containment year-1 ROI</p>
            <p className={`metric-value${lowView.year1Roi.startsWith("-") ? " is-negative" : ""}`}>{lowView.year1Roi}</p>
            <p className="metric-support">
              {lowPercent ? `${lowPercent} of build cost. ` : ""}
              Payback {lowView.paybackMonths === "not defined" || lowView.paybackMonths === "does not pay back" ? lowView.paybackMonths : `${lowView.paybackMonths} months`}.
            </p>
          </article>
        </div>
        <p className="status">
          {edited ? (
            "Assumptions edited. Payback, year-1 ROI, the scenarios, and the tornado are recomputed from these inputs."
          ) : headlinesMatch ? (
            <>
              <strong>Committed base case.</strong> Payback 8.47 months, year-1 ROI 0.4175, low-containment year-1 ROI -0.1571.
            </>
          ) : (
            "These defaults do not match the committed reports."
          )}
        </p>
        <p className="formula">
          Net annual benefit is the operating saving, plus any assumed quality value, minus the annual licence. Payback in months is build cost divided by that benefit over 12. Year-1 ROI is net annual benefit minus build cost, divided by build cost. Build cost is spent in year 1. There is no discount rate.
        </p>
      </section>

      <section className="section wrap">
        <div className="report-grid">
          <div>
            <div className="section-head">
              <div>
                <h2>Scenarios</h2>
                <p className="section-note">Six comparisons, from a voice-only baseline to emergency routing with the quality value removed.</p>
              </div>
            </div>
            <ScenarioTable result={result} selectedId={selectedId} onSelect={onSelect} />
          </div>
          <div>
            <h2>Sensitivity tornado</h2>
            <p className="section-note">
              Each bar is year-1 net cash for the bot programme at base containment when that one assumption moves by the relative swing ({swing}). The other assumptions stay put. Lookup USSD offer moves against the voice-agent share of that class.
              {baseCash ? ` Base year-1 net cash is ${fmtMoney(baseCash)} ${CURRENCY_LABEL}.` : ""}
            </p>
            <TornadoChart swings={result.swings} />
            <p className="legend">
              <span><span className="swatch" aria-hidden="true" /> Year-1 net cash from the low input to the high input</span>
              <span><span className="swatch signal" aria-hidden="true" /> Base case</span>
            </p>
          </div>
        </div>
      </section>

      <section className="section wrap">
        <CostPanels result={result} />
      </section>
    </>
  );
}
