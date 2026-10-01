"""Render README visuals from a real run of the cost model.

Numbers on every chart come from care_roi.report.compute, formatted with the
same helpers the committed reports use. The GIF plays the CLI stdout.
"""

from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image, ImageDraw, ImageFont

from care_roi.assumptions import load_assumptions
from care_roi.formatutil import fmt_money, fmt_months, fmt_rate, fmt_roi, fmt_unit
from care_roi.report import CLASS_ORDER, UNIT_ORDER, compute
from care_roi.taxonomy import load_taxonomy

ASSETS = ROOT / "assets"

GREEN = "#0B3D2E"
GOLD = "#C8962E"
CHARCOAL = "#2C2C2C"
CREAM = "#F7F4EC"
CARD = "#FFFDF8"
MUTED = "#5E675F"
GRID = "#E3DCCA"
ZERO = "#8A8175"

INTER = "/usr/share/fonts/truetype/macos/Inter-Regular.ttf"
INTER_MED = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"
INTER_SEMI = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"
INTER_BOLD = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf"
MONO_MED = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"


def _fonts() -> None:
    for path in (INTER, INTER_MED, INTER_SEMI, INTER_BOLD):
        font_manager.fontManager.addfont(path)
    plt.rcParams["font.family"] = "Inter"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["text.color"] = CHARCOAL
    plt.rcParams["axes.labelcolor"] = CHARCOAL
    plt.rcParams["xtick.color"] = CHARCOAL
    plt.rcParams["ytick.color"] = CHARCOAL


def _save(fig: plt.Figure, path: Path, size: tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)
    image = Image.open(path).convert("RGB")
    if image.size != size:
        raise SystemExit(f"{path.name} is {image.size}, expected {size}")
    image.save(path, format="PNG", optimize=True)


def _header(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.patches.append(
        Rectangle((0, 0.905), 1, 0.095, transform=fig.transFigure, facecolor=GREEN, edgecolor="none", zorder=0)
    )
    fig.patches.append(
        Rectangle((0, 0.905), 1, 0.008, transform=fig.transFigure, facecolor=GOLD, edgecolor="none", zorder=1)
    )
    fig.text(0.03, 0.958, title, color=CREAM, fontsize=20, fontweight="semibold", va="center", ha="left")
    fig.text(0.03, 0.924, subtitle, color=GOLD, fontsize=11, va="center", ha="left")


def _footer(fig: plt.Figure, text: str) -> None:
    fig.text(0.03, 0.035, text, color=MUTED, fontsize=9, va="center", ha="left")


def _style_axis(ax: plt.Axes) -> None:
    ax.set_facecolor(CREAM)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color("#C9C0B0")
    ax.tick_params(length=0, labelsize=10)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def _bar_color(scenario_id: str) -> str:
    if scenario_id == "bot_base":
        return GOLD
    if scenario_id == "baseline_voice_only":
        return "#7E8F86"
    return GREEN


def _scenario_labels(bundle) -> list[str]:
    """One-line labels taken from the scenario names the model already uses."""
    rename = {
        "baseline_voice_only": "Voice baseline",
        "bot_low": "Bot, low containment",
        "bot_base": "Bot, base containment",
        "bot_high": "Bot, high containment",
        "bot_base_triage": "Emergency routing, quality value",
        "bot_base_triage_no_quality_value": "Emergency routing, value zero",
    }
    return [rename[item.scenario_id] for item in bundle.scenarios]


def render_hero(bundle) -> None:
    labels = _scenario_labels(bundle)
    costs = [float(fmt_unit(item.cost_per_contact)) for item in bundle.scenarios]
    cash = [float(fmt_money(item.economics.year1_net_cash).replace(",", "")) for item in bundle.scenarios]
    colors = [_bar_color(item.scenario_id) for item in bundle.scenarios]
    base = next(item for item in bundle.scenarios if item.scenario_id == "bot_base")
    y = list(range(len(labels)))[::-1]

    fig = plt.figure(figsize=(16, 8), dpi=100, facecolor=CREAM)
    _header(
        fig,
        "Contact-centre automation ROI",
        "Illustrative placeholders  ·  KES (illustrative)  ·  six scenarios from the cost model",
    )

    cards = [
        ("Base containment payback", f"{fmt_months(base.economics.payback_months)} months"),
        ("Base year-1 ROI", fmt_roi(base.economics.year1_roi)),
        ("Base cost per contact", f"{fmt_unit(base.cost_per_contact)} KES"),
    ]
    for index, (caption, value) in enumerate(cards):
        x = 0.03 + index * 0.32
        fig.patches.append(
            FancyBboxPatch(
                (x, 0.785),
                0.30,
                0.095,
                transform=fig.transFigure,
                boxstyle="round,pad=0.004,rounding_size=0.008",
                facecolor=CARD,
                edgecolor="#E4D8C0",
                linewidth=0.8,
                mutation_aspect=0.6,
            )
        )
        fig.patches.append(Rectangle((x, 0.785), 0.006, 0.095, transform=fig.transFigure, facecolor=GOLD, edgecolor="none"))
        fig.text(x + 0.018, 0.852, caption.upper(), color=MUTED, fontsize=8.5, va="center", ha="left")
        fig.text(x + 0.018, 0.818, value, color=GREEN, fontsize=16, fontweight="semibold", va="center", ha="left")

    ax_cost = fig.add_axes((0.23, 0.13, 0.33, 0.60))
    ax_cash = fig.add_axes((0.64, 0.13, 0.32, 0.60))
    _style_axis(ax_cost)
    _style_axis(ax_cash)

    ax_cost.barh(y, costs, color=colors, height=0.62, zorder=2)
    ax_cost.set_yticks(y)
    ax_cost.set_yticklabels(labels)
    for tick, scenario in zip(ax_cost.get_yticklabels(), bundle.scenarios):
        if scenario.scenario_id == "bot_base":
            tick.set_color(GREEN)
            tick.set_fontweight("semibold")
    ax_cost.set_xlabel("Cost per contact, KES (illustrative)")
    ax_cost.set_xlim(0, max(costs) * 1.28)
    for ypos, value in zip(y, costs):
        ax_cost.text(value + max(costs) * 0.02, ypos, f"{value:,.4f}", va="center", ha="left", fontsize=8.5, color=CHARCOAL)
    ax_cost.set_title("Cost per contact", loc="left", fontsize=13, color=GREEN, pad=8, fontweight="semibold")

    ax_cash.barh(y, cash, color=colors, height=0.62, zorder=2)
    ax_cash.axvline(0, color=ZERO, linewidth=0.9, zorder=1)
    ax_cash.set_yticks(y)
    ax_cash.set_yticklabels([])
    span = max(abs(value) for value in cash)
    ax_cash.set_xlim(-span * 1.62, span * 1.72)
    ax_cash.set_xlabel("Year-1 net cash, KES (illustrative)")
    ax_cash.xaxis.set_major_formatter(plt.FuncFormatter(lambda value, _pos: f"{value:,.0f}"))
    for ypos, value, scenario in zip(y, cash, bundle.scenarios):
        text = fmt_money(scenario.economics.year1_net_cash)
        if value >= 0:
            ax_cash.text(value + span * 0.03, ypos, text, va="center", ha="left", fontsize=8.5, color=CHARCOAL)
        else:
            ax_cash.text(value - span * 0.03, ypos, text, va="center", ha="right", fontsize=8.5, color=CHARCOAL)
    ax_cash.set_title("Year-1 net cash", loc="left", fontsize=13, color=GREEN, pad=8, fontweight="semibold")

    fig.text(
        0.03,
        0.075,
        "Gold bar: bot programme at base containment. Baseline year-1 net cash is 0.00 because licence and build cost are zero, so payback and ROI are not defined.",
        color=MUTED,
        fontsize=9,
        va="center",
        ha="left",
    )
    _footer(
        fig,
        "Source: python -m care_roi. Every input is an illustrative placeholder, not a real operator figure.",
    )
    _save(fig, ASSETS / "hero.png", (1600, 800))


def render_unit_costs(bundle) -> None:
    labels = [label for _key, label in UNIT_ORDER]
    values = [float(fmt_unit(bundle.units[key])) for key, _label in UNIT_ORDER]
    y = list(range(len(labels)))[::-1]
    fig = plt.figure(figsize=(12, 7), dpi=100, facecolor=CREAM)
    _header(fig, "Cost to serve one completed contact", "No spill to another channel  ·  illustrative placeholders")
    ax = fig.add_axes((0.28, 0.14, 0.58, 0.70))
    _style_axis(ax)
    colors = [GOLD if key == "voice_agent" else GREEN for key, _label in UNIT_ORDER]
    ax.barh(y, values, color=colors, height=0.62, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("KES (illustrative) per completed contact")
    ax.set_xlim(0, max(values) * 1.22)
    for ypos, value in zip(y, values):
        ax.text(value + max(values) * 0.015, ypos, f"{value:,.4f}", va="center", ha="left", fontsize=10, color=CHARCOAL)
    _footer(fig, "Source: unit costs from python -m care_roi. Gold bar is the voice-agent baseline. Illustrative placeholders.")
    _save(fig, ASSETS / "unit_costs.png", (1200, 700))


def render_class_costs(bundle) -> None:
    labels = []
    costs = []
    shares = []
    for name in CLASS_ORDER:
        count = sum(1 for row in bundle.rows if row.automation_class == name)
        labels.append(f"{name}   ({count} intents)")
        costs.append(float(fmt_unit(bundle.class_costs[name])))
        shares.append(float(fmt_rate(bundle.class_shares[name])))
    y = list(range(len(labels)))[::-1]
    fig = plt.figure(figsize=(12, 7), dpi=100, facecolor=CREAM)
    _header(
        fig,
        "Automation class under base routing",
        "Assumed demand share and cost per contact  ·  illustrative placeholders",
    )
    ax = fig.add_axes((0.34, 0.20, 0.26, 0.60))
    ax2 = fig.add_axes((0.68, 0.20, 0.26, 0.60))
    _style_axis(ax)
    _style_axis(ax2)
    ax.barh(y, shares, color=GREEN, height=0.55, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, max(shares) * 1.45)
    ax.set_xlabel("Assumed demand share")
    ax.set_title("Demand share", loc="left", fontsize=13, color=GREEN, pad=8, fontweight="semibold")
    for ypos, value in zip(y, shares):
        ax.text(value + 0.012, ypos, f"{value:.4f}", va="center", ha="left", fontsize=10, color=CHARCOAL)
    ax2.barh(y, costs, color=GOLD, height=0.55, zorder=2)
    ax2.set_yticks(y)
    ax2.set_yticklabels([])
    ax2.set_xlim(0, max(costs) * 1.32)
    ax2.set_xlabel("KES (illustrative)")
    ax2.set_title("Cost per contact", loc="left", fontsize=13, color=GREEN, pad=8, fontweight="semibold")
    for ypos, value in zip(y, costs):
        ax2.text(value + max(costs) * 0.02, ypos, f"{value:,.4f}", va="center", ha="left", fontsize=10, color=CHARCOAL)
    _footer(
        fig,
        "Demand shares are assumption weights, not Bitext example counts. Cost is base routing. Illustrative placeholders.",
    )
    _save(fig, ASSETS / "class_costs.png", (1200, 700))


def render_payback(bundle) -> None:
    rows = [item for item in bundle.scenarios if item.economics.payback_months is not None]
    labels = _scenario_labels_for(rows)
    values = [float(fmt_months(item.economics.payback_months)) for item in rows]
    y = list(range(len(labels)))[::-1]
    colors = []
    for item in rows:
        if item.scenario_id == "bot_base":
            colors.append(GOLD)
        elif item.economics.payback_months <= Decimal(12):
            colors.append(GREEN)
        else:
            colors.append(CHARCOAL)
    fig = plt.figure(figsize=(12, 7), dpi=100, facecolor=CREAM)
    _header(fig, "Payback where it is defined", "Months  ·  illustrative placeholders  ·  line at 12 months")
    ax = fig.add_axes((0.34, 0.16, 0.55, 0.66))
    _style_axis(ax)
    ax.barh(y, values, color=colors, height=0.62, zorder=2)
    ax.axvline(12, color=GOLD, linewidth=1.2, linestyle=(0, (4, 3)), zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Payback, months")
    ax.set_xlim(0, max(values) * 1.22)
    for ypos, value in zip(y, values):
        ax.text(value + max(values) * 0.015, ypos, f"{value:.2f}", va="center", ha="left", fontsize=10, color=CHARCOAL)
    _footer(
        fig,
        "Dashed line: 12 months. Voice baseline omitted because payback is not defined when licence and build cost are zero. Illustrative placeholders.",
    )
    _save(fig, ASSETS / "payback_months.png", (1200, 700))


def _scenario_labels_for(rows) -> list[str]:
    rename = {
        "baseline_voice_only": "Voice baseline",
        "bot_low": "Bot, low containment",
        "bot_base": "Bot, base containment",
        "bot_high": "Bot, high containment",
        "bot_base_triage": "Emergency routing, quality value",
        "bot_base_triage_no_quality_value": "Emergency routing, value zero",
    }
    return [rename[item.scenario_id] for item in rows]


def render_social(hero_path: Path, bundle) -> None:
    """1280x640 card. Text and the hero thumbnail sit inside a 40px margin."""
    canvas = Image.new("RGB", (1280, 640), GREEN)
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(INTER_SEMI, 34)
    tag_font = ImageFont.truetype(INTER, 20)
    label_font = ImageFont.truetype(INTER_MED, 13)
    value_font = ImageFont.truetype(INTER_SEMI, 20)
    small_font = ImageFont.truetype(INTER, 15)
    name = "care-automation-roi"
    tagline = (
        "Automating customer care saves agent time, but at what licence "
        "and build cost, and how sensitive is the case to containment rates?"
    )
    draw.text((48, 44), name, font=title_font, fill=CREAM)
    wrapped = _wrap_pil(tagline, tag_font, 1184)
    y = 84
    for line in wrapped:
        draw.text((48, y), line, font=tag_font, fill="#F3E6C4")
        y += 26
    draw.rectangle((48, y + 8, 160, y + 12), fill=GOLD)
    base = next(item for item in bundle.scenarios if item.scenario_id == "bot_base")
    stats = [
        ("BASE PAYBACK", f"{fmt_months(base.economics.payback_months)} months"),
        ("YEAR-1 ROI", fmt_roi(base.economics.year1_roi)),
        ("COST / CONTACT", f"{fmt_unit(base.cost_per_contact)} KES"),
    ]
    x = 48
    stat_y = y + 24
    for caption, value in stats:
        draw.text((x, stat_y), caption, font=label_font, fill=GOLD)
        draw.text((x, stat_y + 16), value, font=value_font, fill=CREAM)
        x += 250
    draw.text((900, stat_y + 16), "Illustrative placeholders", font=small_font, fill=GOLD)

    hero = Image.open(hero_path).convert("RGB")
    # Chart band of the hero, fitted whole so labels are not clipped.
    chart = hero.crop((0, 188, 1600, 735))
    box = (48, 248, 1232, 600)
    box_w = box[2] - box[0]
    box_h = box[3] - box[1]
    scale = min(box_w / chart.width, box_h / chart.height)
    thumb = chart.resize((int(chart.width * scale), int(chart.height * scale)), Image.Resampling.LANCZOS)
    paste_x = box[0] + (box_w - thumb.width) // 2
    paste_y = box[1] + (box_h - thumb.height) // 2
    frame = Image.new("RGB", (thumb.width + 16, thumb.height + 16), CREAM)
    frame.paste(thumb, (8, 8))
    # Keep the framed thumbnail inside the 40px margin.
    fx = max(40, paste_x - 8)
    fy = max(40, paste_y - 8)
    if fx + frame.width > 1240:
        fx = 1240 - frame.width
    if fy + frame.height > 600:
        fy = 600 - frame.height
    canvas.paste(frame, (fx, fy))
    canvas.save(ASSETS / "social-preview.png", format="PNG", optimize=True)
    saved = Image.open(ASSETS / "social-preview.png")
    if saved.size != (1280, 640):
        raise SystemExit(f"social preview is {saved.size}")


def _wrap_pil(text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if font.getlength(trial) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _run_cli(args: list[str]) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "care_roi", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr or result.stdout)
    return result.stdout.rstrip("\n")


def render_gif() -> None:
    runs = [
        ("python -m care_roi --out /tmp/roi-demo", ["--out", "/tmp/roi-demo"]),
        (
            "python -m care_roi --set volume.annual_contacts=100000 --out /tmp/roi-try",
            ["--set", "volume.annual_contacts=100000", "--out", "/tmp/roi-try"],
        ),
        ("python -m care_roi --check", ["--check"]),
    ]
    captured = [(command, _run_cli(argv)) for command, argv in runs]

    width, height = 1000, 560
    margin_x, margin_y = 28, 22
    title_h = 44
    font = ImageFont.truetype(MONO, 16)
    font_bold = ImageFont.truetype(MONO_MED, 16)
    title_font = ImageFont.truetype(INTER_MED, 15)
    line_h = 24
    rows = (height - title_h - margin_y * 2) // line_h
    text_width = width - margin_x * 2
    prompt = "care-roi $ "

    def wrap_line(text: str) -> list[str]:
        if text == "":
            return [""]
        lines: list[str] = []
        current = ""
        for char in text:
            trial = current + char
            if font.getlength(trial) <= text_width:
                current = trial
            else:
                lines.append(current)
                current = char
        lines.append(current)
        return lines

    # Build the animation as a list of screen states. Each state is wrapped lines.
    frames: list[tuple[list[str], int]] = []
    screen: list[str] = [prompt]

    def push(duration: int) -> None:
        wrapped: list[str] = []
        for line in screen:
            wrapped.extend(wrap_line(line))
        frames.append((wrapped[-rows:], duration))

    push(700)
    for command, output in captured:
        # Retype on the current prompt line.
        typed = prompt
        screen[-1] = typed
        step = 2
        for index in range(0, len(command), step):
            typed = prompt + command[: index + step]
            screen[-1] = typed
            push(55)
        screen[-1] = prompt + command
        push(280)
        for line in output.split("\n"):
            screen.append(line)
            push(420)
        screen.append(prompt)
        push(360)
    # Hold the finished screen.
    push(1600)

    images: list[Image.Image] = []
    durations: list[int] = []
    for lines, duration in frames:
        image = Image.new("RGB", (width, height), CREAM)
        draw = ImageDraw.Draw(image)
        # Window shadow and chrome in the portfolio palette.
        draw.rounded_rectangle((8, 8, width - 8, height - 8), radius=12, fill=GREEN)
        draw.rectangle((8, 8, width - 8, 8 + title_h), fill=GREEN)
        draw.ellipse((24, 22, 36, 34), fill="#E7D7A8")
        draw.ellipse((44, 22, 56, 34), fill=GOLD)
        draw.ellipse((64, 22, 76, 34), fill=CREAM)
        draw.text((92, 16), "care-automation-roi  ·  python -m care_roi", font=title_font, fill=CREAM)
        body_top = 8 + title_h
        draw.rectangle((8, body_top, width - 8, height - 8), fill="#12241C")
        y = body_top + margin_y
        for line in lines:
            if line.startswith(prompt):
                draw.text((margin_x, y), prompt, font=font_bold, fill=GOLD)
                rest = line[len(prompt) :]
                draw.text((margin_x + font_bold.getlength(prompt), y), rest, font=font, fill=CREAM)
            else:
                draw.text((margin_x, y), line, font=font, fill="#E7E1D4")
            y += line_h
        images.append(image)
        durations.append(duration)

    gif_path = ASSETS / "demo.gif"
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    # Quantize further with ffmpeg so the file stays small and the timing holds.
    palette_gif = gif_path.with_suffix(".opt.gif")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(gif_path),
            "-vf",
            "split[s0][s1];[s0]palettegen=max_colors=48:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
            str(palette_gif),
        ],
        check=True,
        capture_output=True,
    )
    palette_gif.replace(gif_path)
    total_ms = sum(durations)
    size = gif_path.stat().st_size
    if not (5000 <= total_ms <= 15000):
        raise SystemExit(f"GIF duration {total_ms}ms is outside 5-15s")
    if size > 5 * 1024 * 1024:
        raise SystemExit(f"GIF is {size} bytes")
    print(f"demo.gif {size} bytes, {total_ms} ms, {len(images)} frames")


def main() -> None:
    _fonts()
    raw, assumptions = load_assumptions(ROOT / "assumptions.yaml")
    rows, meta = load_taxonomy(ROOT / "data" / "bitext_by_intent.csv", ROOT / "data" / "bitext_meta.json")
    bundle = compute(raw, assumptions, rows, meta)
    render_hero(bundle)
    render_unit_costs(bundle)
    render_class_costs(bundle)
    render_payback(bundle)
    render_social(ASSETS / "hero.png", bundle)
    render_gif()
    for name in ("hero.png", "unit_costs.png", "class_costs.png", "payback_months.png", "social-preview.png"):
        path = ASSETS / name
        print(f"{name} {path.stat().st_size} bytes {Image.open(path).size}")


if __name__ == "__main__":
    main()
