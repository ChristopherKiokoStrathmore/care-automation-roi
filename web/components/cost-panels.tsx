import { CURRENCY_LABEL } from "@/lib/assumptions";
import { fmtCount, fmtRate, fmtUnit } from "@/lib/decimal-util";
import type { ModelResult } from "@/lib/evaluate";

export function CostPanels({ result }: { result: ModelResult }) {
  const maxUnit = Math.max(...result.units.map((unit) => unit.cost.toNumber()), 0);
  const rates = result.triageRates;
  const annual = result.annualContacts;

  return (
    <div className="cost-grid">
      <section>
        <h2>Cost to serve one completed contact</h2>
        <p className="section-note">
          Unit cost with no spill. A miss on USSD, chat bot, or IVR also pays one voice-agent contact. Currency is {CURRENCY_LABEL}. The red bar is the voice agent. Staffed chat is priced here and is absent from the routing mix.
        </p>
        <ul className="bars">
          {result.units.map((unit) => (
            <li className="bar-row" key={unit.id}>
              <span>{unit.label}</span>
              <span className="bar-track" aria-hidden="true">
                <span
                  className={unit.id === "voice_agent" ? "bar-fill is-signal" : "bar-fill"}
                  style={{ width: `${maxUnit === 0 ? 0 : (unit.cost.toNumber() / maxUnit) * 100}%` }}
                />
              </span>
              <span className="bar-value">{fmtUnit(unit.cost)}</span>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2>Cost by automation class</h2>
        <p className="section-note">
          Demand shares are the assumption weights divided by their sum. Bitext publishes 1,000 training examples of each intent, and those counts are not demand.
        </p>
        <div className="table-scroll">
          <table>
            <caption>Base routing. Currency is {CURRENCY_LABEL}.</caption>
            <thead>
              <tr>
                <th scope="col">Class</th>
                <th className="num" scope="col">Intents</th>
                <th className="num" scope="col">Demand share</th>
                <th className="num" scope="col">Cost / contact</th>
              </tr>
            </thead>
            <tbody>
              {result.classes.map((row) => (
                <tr key={row.id}>
                  <th scope="row">{row.label}</th>
                  <td className="num">{row.nIntents}</td>
                  <td className="num">{fmtRate(row.demandShare)}</td>
                  <td className="num">{fmtUnit(row.costPerContact)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="section-note follow">
          Triage rates per contact: true positive {fmtRate(rates.true_positive)}, false positive {fmtRate(rates.false_positive)}, false negative {fmtRate(rates.false_negative)}, true negative {fmtRate(rates.true_negative)}, predicted emergency {fmtRate(rates.predicted_positive)}. On this volume that is {fmtCount(annual.mul(rates.true_positive))} true positives, {fmtCount(annual.mul(rates.false_positive))} false positives, {fmtCount(annual.mul(rates.false_negative))} false negatives, and {fmtCount(annual.mul(rates.predicted_positive))} contacts sent to a senior agent.
        </p>
      </section>
    </div>
  );
}
