import { CURRENCY_LABEL } from "@/lib/assumptions";
import { economicsView, scenarioById, type ModelResult } from "@/lib/evaluate";

import { CostPanels } from "./cost-panels";
import { ScenarioTable } from "./scenario-table";
import { TornadoChart } from "./tornado";

function clause(name: string, payback: string, roi: string): string {
  if (payback === "not defined") {
    return `${name} has no defined payback or year-1 ROI, because licence and build cost are zero`;
  }
  if (payback === "does not pay back") {
    return `${name} does not pay back (year-1 ROI ${roi})`;
  }
  const months = Number(payback);
  if (Number.isFinite(months) && months > 12) {
    return `${name} pays back in ${payback} months, which is after year 1 (year-1 ROI ${roi})`;
  }
  return `${name} pays back in ${payback} months (year-1 ROI ${roi})`;
}

export function WriteUp({
  result,
  message,
  selectedId,
  edited,
  headlinesMatch,
  swing,
  onSelect,
  onShowDemo,
}: {
  result: ModelResult | null;
  message: string | null;
  selectedId: string;
  edited: boolean;
  headlinesMatch: boolean;
  swing: string;
  onSelect: (scenarioId: string) => void;
  onShowDemo: () => void;
}) {
  const base = result ? economicsView(scenarioById(result.scenarios, "bot_base").economics, scenarioById(result.scenarios, "bot_base").costPerContact) : null;
  const low = result ? economicsView(scenarioById(result.scenarios, "bot_low").economics, scenarioById(result.scenarios, "bot_low").costPerContact) : null;
  const high = result ? economicsView(scenarioById(result.scenarios, "bot_high").economics, scenarioById(result.scenarios, "bot_high").costPerContact) : null;
  const triage = result
    ? economicsView(scenarioById(result.scenarios, "bot_base_triage").economics, scenarioById(result.scenarios, "bot_base_triage").costPerContact)
    : null;
  const triageZero = result
    ? economicsView(
        scenarioById(result.scenarios, "bot_base_triage_no_quality_value").economics,
        scenarioById(result.scenarios, "bot_base_triage_no_quality_value").costPerContact,
      )
    : null;

  return (
    <div role="tabpanel" id="write-up" aria-labelledby="tab-writeup">
      <div className="wrap write-up">
        <p className="section-note">
          The figures in this write-up follow the assumptions in the demo. Currency is {CURRENCY_LABEL}. Every input is an illustrative placeholder.
        </p>
        <p className="follow">
          <button type="button" className="button" onClick={onShowDemo}>
            Back to the demo
          </button>
        </p>

        {message ? (
          <p className="alert" role="alert">
            {message}
          </p>
        ) : null}

        <section className="section prose">
          <h2>The question</h2>
          <p>
            A contact centre that moves work off the voice agent onto a bot only saves money when those contacts stay contained, and only after licence and build cost. This model prices that case from editable assumptions and shows which assumption moves year-1 cash the most.
          </p>
          <p>
            A contact has an intent. The automation class is a rule on the public Bitext category and intent name: lookup, structured transaction, or human required. Demand is a weight per intent. The weight is divided by the sum of the weights. Bitext publishes 1,000 training examples of each intent, so those counts are not used as demand.
          </p>
        </section>

        <section className="section prose">
          <h2>The six scenarios</h2>
          <ol>
            <li>Baseline: every contact on a voice agent. Licence and build cost are zero, so payback and ROI are not defined.</li>
            <li>Bot programme, low containment: each containment rate is the base assumption minus the containment gap, clamped to 0–1.</li>
            <li>Bot programme, base containment: the headline bot case. No triage, and no assumed quality value.</li>
            <li>Bot programme, high containment: each containment rate is the base assumption plus the same gap, clamped to 0–1.</li>
            <li>Bot programme plus emergency routing, with an assumed quality value.</li>
            <li>The same triage path with that quality value set to zero, so the operating result can be read on its own.</li>
          </ol>
          <p>
            The baseline sends every contact to a voice agent. The bot programme offers each class a mix of USSD bot, chat bot, IVR, and voice agent. The mix is an assumption and sums to 1 inside each class. A contact offered to USSD, chat bot, or IVR always pays that channel&apos;s unit cost. With probability equal to the containment rate it stops there. Otherwise it also pays one voice-agent contact. There is one spill step, and no further repeat contact.
          </p>
          <p>
            Triage is a separate switch on the base containment path. A predicted emergency contact skips the bot and pays the senior-agent unit cost. Prevalence, precision, and recall are assumptions, checked so they can sit in one confusion matrix. The true-positive value and the false-negative penalty are assumptions as well. They are reported in their own column so they are not mixed into the operating cost.
          </p>
        </section>

        {result && base && low && high && triage && triageZero ? (
          <section className="section prose">
            <h2>Reading these inputs</h2>
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
            <p>
              {clause("The bot programme at base containment", base.paybackMonths, base.year1Roi)}.{" "}
              {clause("At high containment it", high.paybackMonths, high.year1Roi)}.{" "}
              {clause("At low containment it", low.paybackMonths, low.year1Roi)}.{" "}
              {clause("Emergency routing with the assumed quality value", triage.paybackMonths, triage.year1Roi)}.{" "}
              {clause("The same path with that value removed", triageZero.paybackMonths, triageZero.year1Roi)}.
            </p>
            <p>
              Build cost is spent in year 1, so a payback longer than 12 months goes with a negative year-1 ROI. On the committed placeholders, base containment clears that one-year test and low containment does not. Adding emergency routing raises cost to serve on those placeholders, and the assumed quality value does not close the year-1 gap. Swap in measured inputs before treating any figure as a business case.
            </p>
          </section>
        ) : null}

        <section className="section prose">
          <h2>Costs</h2>
          <p>Unit cost of a contact completed on a channel, with no spill:</p>
          <ul>
            <li>Voice agent, and senior agent: handle minutes divided by 60, times the fully loaded hourly wage, plus a per-minute telecom charge. Fully loaded hourly wage is monthly wage times (1 + burden rate), divided by monthly productive hours.</li>
            <li>Staffed chat: the same wage formula on the chat handle time, plus a platform charge per contact. The telecom per-minute charge is not applied. Staffed chat is priced here and is absent from the routing mix.</li>
            <li>IVR: IVR minutes times the IVR per-minute charge, plus an IVR platform charge.</li>
            <li>USSD bot: sessions per contact times the cost per session.</li>
            <li>Chat bot: the unstaffed platform charge only.</li>
          </ul>
          <p>
            Build cost and the annual licence sit outside the unit cost. The bot programme uses the bot build cost and the bot annual licence. The triage scenarios add the triage build cost and the triage annual licence on top of the bot figures.
          </p>
        </section>

        {result ? (
          <section className="section">
            <CostPanels result={result} />
          </section>
        ) : null}

        <section className="section prose">
          <h2>Benefits, payback, and year-1 ROI</h2>
          <p>
            Annual operating saving is annual contacts times (baseline cost per contact minus scenario cost per contact). The triage scenarios also book an assumed quality value: true positives times the value per true positive, minus false negatives times the penalty per false negative, times annual contacts. That quality figure is an assumption. The zero-value triage row shows the same operating path with that assumption removed.
          </p>
          <p>
            Net annual benefit is the operating saving, plus any assumed quality value, minus the annual licence. Payback in months is build cost divided by that benefit over 12. Year-1 ROI is net annual benefit minus build cost, divided by build cost. Build cost is spent in year 1. There is no discount rate, no tax, and no ramp-up. Payback is undefined when net annual benefit is not positive, and both payback and ROI are not defined when build cost is zero.
          </p>
        </section>

        {result ? (
          <section className="section">
            <div className="section-head">
              <div>
                <h2>Scenario table</h2>
                <p className="section-note">Select a row to read its build-up. The same selection is used in the demo.</p>
              </div>
            </div>
            <ScenarioTable result={result} selectedId={selectedId} onSelect={onSelect} />
          </section>
        ) : null}

        <section className="section prose">
          <h2>Sensitivity</h2>
          <p>
            The tornado moves one assumption by the relative swing ({swing}) and recomputes year-1 net cash for the bot programme at base containment. The other assumptions stay put. Lookup USSD offer moves against the voice-agent share of that class so the shares still sum to 1. A move that would push a share outside 0–1 is clamped, and the clamp is flagged on that bar.
          </p>
          {result ? (
            <>
              <TornadoChart swings={result.swings} />
              <p className="legend">
                <span>
                  <span className="swatch" aria-hidden="true" /> Year-1 net cash from the low input to the high input
                </span>
                <span>
                  <span className="swatch signal" aria-hidden="true" /> Base case
                </span>
              </p>
            </>
          ) : null}
        </section>

        <section className="section prose">
          <h2>Limits</h2>
          <ul>
            <li>Every input number is an illustrative placeholder. The outputs are what those placeholders produce. They are not a quote or a measured return.</li>
            <li>The currency label is not a claim about Kenyan wages, tariffs, or contact volumes.</li>
            <li>The operating model is one offer and, on a miss, one voice-agent contact. It has no queue, no repeat contact after the agent, and no occupancy constraint.</li>
            <li>Triage precision and recall are assumptions. Routing value is an assumption, shown separately.</li>
            <li>Payback and year-1 ROI ignore discounting, tax, and implementation delay.</li>
          </ul>
          <p>
            Keep the formulas. Replace the numbers in <code>assumptions.yaml</code> when measured inputs exist, then rerun the Python model. Until then, use the demo to see how the case moves.
          </p>
        </section>
      </div>
    </div>
  );
}
