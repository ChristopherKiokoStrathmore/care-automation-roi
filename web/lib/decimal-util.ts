/**
 * Decimal arithmetic aligned with care_roi/formatutil.py.
 * Precision stays above Python's default 28 significant digits so display
 * rounding, not intermediate rounding, decides the committed figures.
 */
import Decimal from "decimal.js";

Decimal.set({
  precision: 40,
  rounding: Decimal.ROUND_HALF_UP,
});

export { Decimal };

export const ZERO = new Decimal(0);
export const ONE = new Decimal(1);
export const TWELVE = new Decimal(12);
export const SIXTY = new Decimal(60);

const HALF_UP = Decimal.ROUND_HALF_UP;

export function q2(value: Decimal): Decimal {
  return value.toDecimalPlaces(2, HALF_UP);
}

export function q4(value: Decimal): Decimal {
  return value.toDecimalPlaces(4, HALF_UP);
}

function grouped(value: Decimal, places: number): string {
  const rounded = value.toDecimalPlaces(places, HALF_UP);
  const negative = rounded.isNeg() && !rounded.isZero();
  const [whole, frac] = rounded.abs().toFixed(places).split(".");
  const withCommas = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${negative ? "-" : ""}${withCommas}.${frac}`;
}

export function fmtMoney(value: Decimal): string {
  return grouped(value, 2);
}

export function fmtUnit(value: Decimal): string {
  return grouped(value, 4);
}

export function fmtRate(value: Decimal): string {
  return q4(value).toFixed(4);
}

export function fmtRoi(value: Decimal | null): string {
  if (value === null) return "";
  return q4(value).toFixed(4);
}

export function fmtMonths(value: Decimal | null): string {
  if (value === null) return "does not pay back";
  return q2(value).toFixed(2);
}

export function paybackCell(capex: Decimal, months: Decimal | null): string {
  if (capex.isZero()) return "not defined";
  return fmtMonths(months);
}

export function roiCell(capex: Decimal, roi: Decimal | null): string {
  if (capex.isZero()) return "not defined";
  return fmtRoi(roi);
}

/** Python format(value, "f") with trailing zeros stripped. */
export function fmtInput(value: Decimal): string {
  let text = value.toFixed(value.decimalPlaces());
  if (text.includes(".")) {
    text = text.replace(/0+$/, "").replace(/\.$/, "");
  }
  if (text === "-0" || text === "") return "0";
  return text;
}

export function fmtCount(value: Decimal): string {
  const rounded = q2(value);
  if (rounded.isInteger()) {
    const negative = rounded.isNeg() && !rounded.isZero();
    const whole = rounded.abs().toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return `${negative ? "-" : ""}${whole}`;
  }
  return fmtMoney(rounded);
}

export function decToInput(value: Decimal): string {
  return fmtInput(value);
}

const NUMBER_TEXT = /^[+-]?(?:\d+\.\d+|\d+)$/;

export function parseDecimal(raw: string, path: string): Decimal {
  const text = raw.trim();
  if (!NUMBER_TEXT.test(text)) {
    throw new Error(`${path} must be a number`);
  }
  return new Decimal(text);
}
