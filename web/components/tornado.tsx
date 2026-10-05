import { fmtInput, fmtMoney } from "@/lib/decimal-util";
import type { SwingRow } from "@/lib/sensitivity";

function percent(value: number, min: number, span: number): string {
  return `${(((value - min) / span) * 100).toFixed(4)}%`;
}

export function TornadoChart({ swings }: { swings: SwingRow[] }) {
  const base = swings[0]?.baseYear1NetCash;
  const numbers = swings.flatMap((swing) => [
    swing.year1NetCashLow.toNumber(),
    swing.year1NetCashHigh.toNumber(),
    swing.baseYear1NetCash.toNumber(),
  ]);
  const rawMin = Math.min(...numbers);
  const rawMax = Math.max(...numbers);
  const pad = rawMin === rawMax ? 1 : (rawMax - rawMin) * 0.04;
  const min = rawMin - pad;
  const span = rawMax + pad - min;

  return (
    <ol className="tornado">
      {swings.map((swing) => {
        const low = swing.year1NetCashLow.toNumber();
        const high = swing.year1NetCashHigh.toNumber();
        const left = Math.min(low, high);
        const width = Math.abs(high - low);
        const lowLabel = `Low input ${fmtInput(swing.inputLow)}${swing.lowClamped ? " (clamped)" : ""} → ${fmtMoney(swing.year1NetCashLow)}`;
        const highLabel = `High input ${fmtInput(swing.inputHigh)}${swing.highClamped ? " (clamped)" : ""} → ${fmtMoney(swing.year1NetCashHigh)}`;
        return (
          <li key={swing.factorId}>
            <p className="tornado-name">{swing.label}</p>
            <p className="tornado-ends">
              <span>{lowLabel}</span>
              <span>{highLabel}</span>
            </p>
            <div
              className="track"
              aria-hidden="true"
            >
              <span className="bar" style={{ left: percent(left, min, span), width: percent(width, 0, span) }} />
              {base ? <span className="base" style={{ left: percent(base.toNumber(), min, span) }} /> : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
