"""Tornado chart as HTML/SVG and as PNG. Both read the same swing rows."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from care_roi.formatutil import fmt_money, q2
from care_roi.sensitivity import SwingRow


def _xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_html(rows: list[SwingRow], path: Path, currency_label: str) -> None:
    if not rows:
        raise ValueError("No sensitivity rows to chart")
    base = q2(rows[0].base_year1_net_cash)
    values = [q2(row.year1_net_cash_low) for row in rows] + [q2(row.year1_net_cash_high) for row in rows]
    values.append(base)
    low = min(values)
    high = max(values)
    span = high - low
    if span == 0:
        span = Decimal(1)
    pad = span * Decimal("0.08")
    vmin = low - pad
    vmax = high + pad

    width = 1200
    left = 280
    right = 820
    plot_width = right - left
    row_h = 36
    top = 78
    height = top + row_h * len(rows) + 48

    def x_of(value: Decimal) -> int:
        ratio = (value - vmin) / (vmax - vmin)
        return int(left + ratio * plot_width)

    base_x = x_of(base)
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Bot programme sensitivity (assumption-driven)</title>",
        "<style>",
        "body { font-family: sans-serif; margin: 24px; color: #1c1c1c; }",
        "p { max-width: 920px; line-height: 1.45; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Bot programme sensitivity</h1>",
        "<p>Each bar is the year-1 net cash of the bot programme at base containment "
        "when that one assumption moves by the relative swing in assumptions.yaml. "
        "The vertical line is the base case. "
        f"Currency is {_xml(currency_label)}. "
        "Every input is an illustrative placeholder, not a real operator figure. "
        f"Base year-1 net cash: {fmt_money(base)}.</p>",
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">',
        "<title>Tornado chart of year-1 net cash</title>",
        f'<line x1="{base_x}" y1="{top - 16}" x2="{base_x}" y2="{top + row_h * len(rows) - 8}" '
        'stroke="#b00020" stroke-width="2"/>',
    ]
    for index, row in enumerate(rows):
        y = top + index * row_h
        lo = q2(row.year1_net_cash_low)
        hi = q2(row.year1_net_cash_high)
        x1 = x_of(min(lo, hi))
        x2 = x_of(max(lo, hi))
        if x2 == x1:
            x2 = x1 + 1
        parts.append(
            f'<rect x="{x1}" y="{y}" width="{x2 - x1}" height="22" fill="#4c78a8"/>'
        )
        parts.append(
            f'<text x="8" y="{y + 16}" font-size="13" font-family="sans-serif">{_xml(row.label)}</text>'
        )
        parts.append(
            f'<text x="{right + 8}" y="{y + 16}" font-size="12" font-family="sans-serif">'
            f"{fmt_money(lo)} to {fmt_money(hi)}</text>"
        )
    parts.append("</svg>")
    parts.append("</body></html>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_png(rows: list[SwingRow], path: Path, currency_label: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not rows:
        raise ValueError("No sensitivity rows to chart")
    labels = [row.label for row in rows]
    lows = [float(q2(row.year1_net_cash_low)) for row in rows]
    highs = [float(q2(row.year1_net_cash_high)) for row in rows]
    base = float(q2(rows[0].base_year1_net_cash))
    fig_h = 0.48 * len(rows) + 1.6
    fig, ax = plt.subplots(figsize=(10.5, fig_h))
    for index, (low, high) in enumerate(zip(lows, highs)):
        left = min(low, high)
        ax.barh(index, abs(high - low), left=left, height=0.62, color="#4C78A8")
    ax.axvline(base, color="#b00020", linewidth=1.5)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel(f"Year-1 net cash, {currency_label}. The red line is the base case.")
    ax.set_title("Bot programme sensitivity (every input is an assumption)")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda value, _pos: f"{value:,.0f}"))
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
