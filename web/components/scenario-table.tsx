import { CURRENCY_LABEL } from "@/lib/assumptions";
import { economicsView, type ModelResult } from "@/lib/evaluate";

export function ScenarioTable({
  result,
  selectedId,
  onSelect,
}: {
  result: ModelResult;
  selectedId: string;
  onSelect: (scenarioId: string) => void;
}) {
  const selected = result.scenarios.find((item) => item.scenarioId === selectedId) ?? result.scenarios[0];
  const view = economicsView(selected.economics, selected.costPerContact);

  return (
    <div>
      <div className="table-scroll">
        <table>
          <caption>Currency is {CURRENCY_LABEL}. Select a row to read its build-up. Annual amounts are rounded to the cent.</caption>
          <thead>
            <tr>
              <th scope="col">Scenario</th>
              <th className="num" scope="col">Cost / contact</th>
              <th className="num" scope="col">Payback</th>
              <th className="num" scope="col">Year-1 ROI</th>
              <th className="num" scope="col">Year-1 net cash</th>
            </tr>
          </thead>
          <tbody>
            {result.scenarios.map((scenario) => {
              const cells = economicsView(scenario.economics, scenario.costPerContact);
              const selectedRow = scenario.scenarioId === selected.scenarioId;
              return (
                <tr key={scenario.scenarioId} className={selectedRow ? "is-selected" : undefined}>
                  <th scope="row">
                    <button
                      type="button"
                      className="row-select"
                      aria-pressed={selectedRow}
                      onClick={() => onSelect(scenario.scenarioId)}
                    >
                      {scenario.label}
                    </button>
                  </th>
                  <td className="num">{cells.costPerContact}</td>
                  <td className="num">{cells.paybackMonths === "not defined" ? cells.paybackMonths : `${cells.paybackMonths} mo`}</td>
                  <td className={`num${cells.year1Roi.startsWith("-") ? " is-negative" : ""}`}>{cells.year1Roi}</td>
                  <td className="num">{cells.year1NetCash}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <article className="detail">
        <h3>{selected.label}</h3>
        <p className="detail-note">{selected.note}</p>
        <dl className="facts">
          <dt>Cost per contact</dt>
          <dd>{view.costPerContact}</dd>
          <dt>Annual operating cost</dt>
          <dd>{view.annualOperatingCost}</dd>
          <dt>Operating saving versus voice baseline</dt>
          <dd>{view.annualOperatingSaving}</dd>
          <dt>Assumed quality value</dt>
          <dd>{view.assumedQualityValue}</dd>
          <dt>Annual licence</dt>
          <dd>{view.annualLicence}</dd>
          <dt>Build cost</dt>
          <dd>{view.capex}</dd>
          <dt>Net annual benefit</dt>
          <dd>{view.netAnnualBenefit}</dd>
          <dt>Payback (months)</dt>
          <dd>{view.paybackMonths}</dd>
          <dt>Year-1 ROI</dt>
          <dd>{view.year1Roi}</dd>
          <dt>Year-1 net cash</dt>
          <dd>{view.year1NetCash}</dd>
        </dl>
      </article>
    </div>
  );
}
