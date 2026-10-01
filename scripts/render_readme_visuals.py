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
from matplotlib.patches import Rectangle
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


def _story_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    """Fraunces and Inter Tight, downloaded on demand and cached outside the repo."""
    cache = Path("/tmp/care-roi-fonts")
    cache.mkdir(parents=True, exist_ok=True)
    specs = {
        "Fraunces-700.ttf": ("fraunces", "700"),
        "InterTight-regular.ttf": ("inter-tight", "regular"),
        "InterTight-600.ttf": ("inter-tight", "600"),
        "InterTight-700.ttf": ("inter-tight", "700"),
    }
    local = Path("/tmp/fonts/ttf")
    paths = {}
    for name, (family, variant) in specs.items():
        dest = cache / name
        if not dest.exists() or dest.stat().st_size < 1000:
            if (local / name).exists():
                dest.write_bytes((local / name).read_bytes())
            else:
                _download_font(family, variant, dest)
        paths[name] = dest
    display = paths["Fraunces-700.ttf"]
    sans = paths["InterTight-regular.ttf"]
    semi = paths["InterTight-600.ttf"]
    bold = paths["InterTight-700.ttf"]
    return {
        "display_lg": ImageFont.truetype(display, 34),
        "display": ImageFont.truetype(display, 30),
        "display_sm": ImageFont.truetype(display, 22),
        "hero_num": ImageFont.truetype(display, 52),
        "social_name": ImageFont.truetype(display, 36),
        "social_num": ImageFont.truetype(display, 32),
        "kicker": ImageFont.truetype(semi, 15),
        "kicker_sm": ImageFont.truetype(semi, 13),
        "strong": ImageFont.truetype(bold, 16),
        "strong_sm": ImageFont.truetype(bold, 14),
        "body": ImageFont.truetype(sans, 15),
        "small": ImageFont.truetype(sans, 13),
        "tiny": ImageFont.truetype(sans, 12),
        "social_tag": ImageFont.truetype(sans, 20),
    }


def _download_font(family: str, variant: str, dest: Path) -> None:
    import json
    import urllib.request

    url = f"https://gwfh.mranftl.com/api/fonts/{family}?subsets=latin"
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)
    for item in payload["variants"]:
        if item["id"] == variant and item["fontStyle"] == "normal":
            urllib.request.urlretrieve(item["ttf"], dest)
            return
    raise SystemExit(f"Could not download {family} {variant}")


def _icon(draw_fn, size: int, color: str) -> Image.Image:
    scale = 4
    canvas = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(canvas), size * scale, color)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def _paste(base: Image.Image, sprite: Image.Image, xy: tuple[int, int]) -> None:
    base.paste(sprite, xy, sprite)


def _person(draw: ImageDraw.ImageDraw, s: int, color: str) -> None:
    radius = s * 0.16
    cx, cy = s * 0.50, s * 0.32
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)
    draw.pieslice((s * 0.16, s * 0.46, s * 0.84, s * 1.08), 200, 340, fill=color)


def _headset(draw: ImageDraw.ImageDraw, s: int, color: str) -> None:
    width = max(3, s // 14)
    draw.arc((s * 0.18, s * 0.08, s * 0.82, s * 0.78), 200, 340, fill=color, width=width + 1)
    draw.ellipse((s * 0.30, s * 0.22, s * 0.70, s * 0.66), outline=color, width=width)
    ear_w, ear_h = s * 0.16, s * 0.26
    for side in (-1, 1):
        ex = s * 0.50 + side * s * 0.36
        draw.rounded_rectangle(
            (ex - ear_w / 2, s * 0.40, ex + ear_w / 2, s * 0.40 + ear_h),
            radius=s * 0.04,
            fill=color,
        )
    draw.line((s * 0.68, s * 0.62, s * 0.56, s * 0.82), fill=color, width=width)
    mic = s * 0.07
    draw.ellipse((s * 0.48, s * 0.76, s * 0.48 + mic * 2, s * 0.76 + mic * 2), fill=color)


def _clock(draw: ImageDraw.ImageDraw, s: int, color: str) -> None:
    width = max(3, s // 12)
    pad = s * 0.12
    draw.ellipse((pad, pad, s - pad, s - pad), outline=color, width=width)
    cx = cy = s * 0.50
    draw.line((cx, cy, cx, cy - s * 0.22), fill=color, width=width)
    draw.line((cx, cy, cx + s * 0.16, cy + s * 0.08), fill=color, width=width)


def _coins(draw: ImageDraw.ImageDraw, s: int, color: str) -> None:
    width = max(3, s // 14)
    for index, dy in enumerate((0.18, 0.00, -0.18)):
        box = (s * 0.16, s * (0.42 + dy), s * 0.84, s * (0.62 + dy))
        if index == 2:
            draw.ellipse(box, fill=color)
        else:
            draw.ellipse(box, outline=color, width=width)


def _document(draw: ImageDraw.ImageDraw, s: int, color: str) -> None:
    width = max(2, s // 16)
    draw.rounded_rectangle((s * 0.22, s * 0.12, s * 0.78, s * 0.88), radius=s * 0.06, outline=color, width=width)
    for row in range(3):
        y = s * (0.32 + row * 0.16)
        draw.line((s * 0.34, y, s * 0.66, y), fill=color, width=width)


def _tags(draw: ImageDraw.ImageDraw, s: int, color: str) -> None:
    for row in range(3):
        y = s * (0.18 + row * 0.24)
        draw.rounded_rectangle((s * 0.18, y, s * 0.82, y + s * 0.16), radius=s * 0.08, outline=color, width=max(2, s // 16))


def _branch(draw: ImageDraw.ImageDraw, s: int, color: str) -> None:
    width = max(3, s // 14)
    draw.line((s * 0.50, s * 0.16, s * 0.50, s * 0.46), fill=color, width=width)
    draw.line((s * 0.50, s * 0.46, s * 0.22, s * 0.80), fill=color, width=width)
    draw.line((s * 0.50, s * 0.46, s * 0.78, s * 0.80), fill=color, width=width)


def _grid6(draw: ImageDraw.ImageDraw, s: int, color: str) -> None:
    gap = s * 0.08
    cell = (s - gap * 4) / 3
    for row in range(2):
        for col in range(3):
            x = gap + col * (cell + gap)
            y = s * 0.18 + row * (cell + gap)
            draw.rounded_rectangle((x, y, x + cell, y + cell), radius=s * 0.04, fill=color)


def _swing(draw: ImageDraw.ImageDraw, s: int, color: str) -> None:
    width = max(3, s // 14)
    mid = s * 0.50
    draw.line((s * 0.16, mid, s * 0.84, mid), fill=color, width=width)
    draw.polygon([(s * 0.16, mid), (s * 0.30, mid - s * 0.12), (s * 0.30, mid + s * 0.12)], fill=color)
    draw.polygon([(s * 0.84, mid), (s * 0.70, mid - s * 0.12), (s * 0.70, mid + s * 0.12)], fill=color)


def _h_arrow(w: int = 40, h: int = 24, color: str = GOLD) -> Image.Image:
    scale = 4
    canvas = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    mid = (h * scale) // 2
    draw.line((2 * scale, mid, (w - 14) * scale, mid), fill=color, width=4 * scale)
    draw.polygon(
        [((w - 16) * scale, mid - 8 * scale), (w * scale - 2, mid), ((w - 16) * scale, mid + 8 * scale)],
        fill=color,
    )
    return canvas.resize((w, h), Image.Resampling.LANCZOS)


def _v_arrow(h: int = 16, color: str = GOLD) -> Image.Image:
    w = 14
    scale = 4
    canvas = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    cx = (w * scale) // 2
    draw.line((cx, 0, cx, (h - 7) * scale), fill=color, width=3 * scale)
    draw.polygon([(cx - 5 * scale, (h - 8) * scale), (cx + 5 * scale, (h - 8) * scale), (cx, h * scale - 1)], fill=color)
    return canvas.resize((w, h), Image.Resampling.LANCZOS)


def _round_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=22, fill=GREEN)
    draw.rectangle((x + 18, y + 50, x + w - 18, y + 54), fill=GOLD)
    draw.rounded_rectangle((x + 4, y + 54, x + w - 4, y + h - 4), radius=18, fill=CARD)


def _header_label(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], index: str, kicker: str, fonts: dict) -> None:
    x, y, _w, _h = box
    draw.text((x + 24, y + 27), index, font=fonts["display_sm"], fill=GOLD, anchor="lm")
    draw.text((x + 68, y + 27), kicker, font=fonts["kicker"], fill=CREAM, anchor="lm")


def _pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.FreeTypeFont) -> None:
    x, y = xy
    width = int(font.getlength(text)) + 22
    height = 26
    draw.rounded_rectangle((x, y, x + width, y + height), radius=13, fill=GREEN)
    draw.text((x + 11, y + 13), text, font=font, fill=CREAM, anchor="lm")


def _require(font: ImageFont.FreeTypeFont, text: str, max_width: float, what: str) -> None:
    width = font.getlength(text)
    if width > max_width:
        raise SystemExit(f"{what} is {width:.0f}px, wider than {max_width:.0f}px: {text}")


def _roi_rows(bundle) -> list[tuple[str, Decimal, str, bool]]:
    labels = {
        "bot_low": "Low containment",
        "bot_base": "Base containment",
        "bot_high": "High containment",
        "bot_base_triage": "Emergency routing",
        "bot_base_triage_no_quality_value": "Quality value 0",
    }
    rows = []
    for item in bundle.scenarios:
        if item.economics.year1_roi is None:
            continue
        rows.append(
            (
                labels[item.scenario_id],
                item.economics.year1_roi,
                fmt_roi(item.economics.year1_roi),
                item.scenario_id == "bot_base",
            )
        )
    return rows


def _draw_roi_chart(base: Image.Image, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], rows, fonts) -> None:
    x, y, w, h = box
    draw.text((x, y), "Year-1 ROI", font=fonts["strong"], fill=GREEN)
    plot_top = y + 26
    label_w = max(int(fonts["tiny"].getlength(label)) for label, _value, _text, _gold in rows) + 14
    value_w = max(int(fonts["tiny"].getlength(text)) for _label, _value, text, _gold in rows) + 8
    plot_x = x + label_w
    plot_w = w - label_w - value_w
    values = [float(value) for _label, value, _text, _gold in rows]
    low = min(min(values), 0.0)
    high = max(max(values), 0.0)
    span = (high - low) or 1.0
    low -= span * 0.06
    high += span * 0.06
    span = high - low
    row_h = (h - 26) / len(rows)

    def x_of(value: float) -> float:
        return plot_x + (value - low) / span * plot_w

    zero = x_of(0.0)
    draw.line((zero, plot_top, zero, plot_top + row_h * len(rows) - 6), fill=GOLD, width=2)
    for index, (label, value, text, gold) in enumerate(rows):
        cy = plot_top + row_h * index + row_h / 2
        _require(fonts["tiny"], label, label_w - 8, label)
        draw.text((x, cy), label, font=fonts["tiny"], fill=GREEN, anchor="lm")
        end = x_of(float(value))
        bar_color = GOLD if gold else GREEN
        top = cy - 7
        draw.rounded_rectangle((min(zero, end), top, max(zero, end), top + 14), radius=3, fill=bar_color)
        _require(fonts["tiny"], text, value_w - 4, text)
        draw.text((x + w, cy), text, font=fonts["tiny"], fill=GREEN, anchor="rm")


def _problem_scene(base: Image.Image, box: tuple[int, int, int, int]) -> None:
    x, y, w, h = box
    draw = ImageDraw.Draw(base)
    person = _icon(_person, 48, GREEN)
    gap = 12
    cluster = 3 * person.width + 2 * gap
    left = x + 6
    icon_top = y + 4
    for index in range(3):
        _paste(base, person, (left + index * (person.width + gap), icon_top))
    ring_r = 44
    ring_cx = x + w - ring_r - 6
    ring_cy = icon_top + 26
    draw.ellipse(
        (ring_cx - ring_r, ring_cy - ring_r, ring_cx + ring_r, ring_cy + ring_r),
        outline=GOLD,
        width=3,
    )
    headset = _icon(_headset, 62, GREEN)
    _paste(base, headset, (ring_cx - headset.width // 2, ring_cy - headset.height // 2 + 2))
    arrow = _h_arrow(36, 18)
    arrow_x = left + cluster + 12
    arrow_limit = ring_cx - ring_r - 10 - arrow.width
    if arrow_x > arrow_limit:
        arrow_x = arrow_limit
    _paste(base, arrow, (arrow_x, icon_top + 15))
    caption = ImageFont.truetype(_story_font_path("InterTight-600.ttf"), 13)
    muted = ImageFont.truetype(_story_font_path("InterTight-regular.ttf"), 13)
    caption_y = max(icon_top + person.height, ring_cy + ring_r) + 10
    draw.text((left + cluster / 2, caption_y), "Contacts", font=caption, fill=GREEN, anchor="mt")
    draw.text((ring_cx, caption_y), "Voice agent", font=caption, fill=GREEN, anchor="mt")
    clock = _icon(_clock, 34, GREEN)
    coins = _icon(_coins, 34, GOLD)
    row_y = caption_y + 26
    _paste(base, clock, (x + 4, row_y))
    draw.text((x + 46, row_y + 17), "Agent time", font=muted, fill=GREEN, anchor="lm")
    _paste(base, coins, (x + w // 2, row_y))
    draw.text((x + w // 2 + 42, row_y + 17), "Wage and telco", font=muted, fill=GREEN, anchor="lm")


def _story_font_path(name: str) -> str:
    return str(Path("/tmp/care-roi-fonts") / name)


def _method_steps(bundle) -> list[tuple[str, str, object]]:
    class_names = {
        "lookup": "lookup",
        "structured_transaction": "structured transaction",
        "human_required": "human required",
    }
    classes = ", ".join(class_names[name] for name in CLASS_ORDER)
    count = len(bundle.scenarios)
    return [
        ("assumptions.yaml", "Illustrative inputs, not operator data", _document),
        ("Intent rule", classes, _tags),
        ("Cost and routing", "Channel mix, containment, one voice spill", _branch),
        (f"{count} scenarios", "Payback, year-1 ROI, and year-1 cash", _grid6),
        ("Sensitivity", "Move one input, recompute year-1 cash", _swing),
    ]


def render_hero(bundle) -> None:
    """Three-panel story: manual voice care, the model pipeline, and base-case payback."""
    fonts = _story_fonts()
    base = next(item for item in bundle.scenarios if item.scenario_id == "bot_base")
    baseline = next(item for item in bundle.scenarios if item.scenario_id == "baseline_voice_only")
    voice_cost = fmt_unit(baseline.cost_per_contact)
    payback = fmt_months(base.economics.payback_months)
    roi = fmt_roi(base.economics.year1_roi)
    image = Image.new("RGB", (1600, 800), CREAM)
    draw = ImageDraw.Draw(image)
    cards = []
    x = 24
    for _index in range(3):
        cards.append((x, 18, 480, 724))
        x += 480 + 56
    for box, index, kicker in zip(cards, ("01", "02", "03"), ("PROBLEM", "METHOD", "RESULT")):
        _round_card(draw, box)
        _header_label(draw, box, index, kicker, fonts)
    for left, right in zip(cards, cards[1:]):
        gap_x = left[0] + left[2] + 8
        arrow = _h_arrow(40, 26)
        _paste(image, arrow, (gap_x, left[1] + left[3] // 2 - arrow.height // 2))

    _draw_problem_panel(image, draw, cards[0], fonts, voice_cost)
    _draw_method_panel(image, draw, cards[1], fonts, bundle)
    _draw_result_panel(image, draw, cards[2], fonts, bundle, payback, roi)
    footer = "Illustrative inputs in assumptions.yaml. Currency is KES (illustrative). Not a measured operator result."
    _require(fonts["small"], footer, 1500, "footer")
    draw.text((800, 768), footer, font=fonts["small"], fill=MUTED, anchor="mt")
    image.save(ASSETS / "hero.png", format="PNG", optimize=True)
    saved = Image.open(ASSETS / "hero.png")
    if saved.size != (1600, 800):
        raise SystemExit(f"hero is {saved.size}")


def _content_box(card: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x, y, w, h = card
    return (x + 28, y + 78, w - 56, h - 102)


def _draw_problem_panel(image, draw, card, fonts, voice_cost: str) -> None:
    x, y, w, h = _content_box(card)
    _require(fonts["display"], "Time and money", w, "problem title")
    draw.text((x, y), "Time and money", font=fonts["display"], fill=GREEN)
    draw.text((x, y + 36), "on every contact", font=fonts["display"], fill=GREEN)
    scene = (x, y + 92, w, 210)
    _problem_scene(image, scene)
    rule_y = scene[1] + scene[3] + 18
    draw.line((x, rule_y, x + 72, rule_y), fill=GOLD, width=3)
    number_y = rule_y + 28
    _require(fonts["hero_num"], voice_cost, w, "voice cost")
    draw.text((x, number_y), voice_cost, font=fonts["hero_num"], fill=GREEN)
    draw.text((x, number_y + 64), "KES per voice contact", font=fonts["strong"], fill=GREEN)
    draw.text((x, number_y + 88), "Baseline cost to serve", font=fonts["small"], fill=MUTED)
    _pill(draw, (x, number_y + 116), "illustrative inputs", fonts["tiny"])


def _draw_method_panel(image, draw, card, fonts, bundle) -> None:
    x, y, w, h = _content_box(card)
    draw.text((x, y), "From assumptions", font=fonts["display"], fill=GREEN)
    draw.text((x, y + 36), "to payback", font=fonts["display"], fill=GREEN)
    steps = _method_steps(bundle)
    top = y + 96
    bottom = y + h - 8
    row_h = 58
    usable = bottom - top
    gap = (usable - len(steps) * row_h) / max(len(steps) - 1, 1)
    gap = min(gap, 28)
    block = len(steps) * row_h + (len(steps) - 1) * gap
    cursor = top + max(0, (usable - block) / 2)
    for index, (title, subtitle, icon_fn) in enumerate(steps):
        bubble = _icon(icon_fn, 34, CREAM)
        disc = Image.new("RGBA", (44, 44), (0, 0, 0, 0))
        disc_draw = ImageDraw.Draw(disc)
        disc_draw.ellipse((0, 0, 43, 43), fill=GREEN)
        disc.paste(bubble, (5, 5), bubble)
        _paste(image, disc, (x, int(cursor)))
        text_x = x + 56
        _require(fonts["strong_sm"], title, w - 56, title)
        draw.text((text_x, cursor + 4), title, font=fonts["strong_sm"], fill=GREEN)
        for line_index, line in enumerate(_wrap_pil(subtitle, fonts["tiny"], w - 56)):
            draw.text((text_x, cursor + 24 + line_index * 15), line, font=fonts["tiny"], fill=MUTED)
        if index < len(steps) - 1:
            arrow = _v_arrow(max(12, int(gap) - 4))
            _paste(image, arrow, (x + 15, int(cursor + 46)))
        cursor += row_h + gap


def _draw_result_panel(image, draw, card, fonts, bundle, payback: str, roi: str) -> None:
    x, y, w, h = _content_box(card)
    draw.text((x, y), "Base case", font=fonts["display"], fill=GREEN)
    draw.text((x, y + 36), "inside year 1", font=fonts["display"], fill=GREEN)
    chart_box = (x, y + 92, w, 176)
    _draw_roi_chart(image, draw, chart_box, _roi_rows(bundle), fonts)
    note = "Only base and high containment clear year 1."
    _require(fonts["tiny"], note, w, "result note")
    draw.text((x, y + 274), note, font=fonts["tiny"], fill=MUTED)
    draw.text((x, y + 292), "Baseline ROI is not defined.", font=fonts["tiny"], fill=MUTED)
    draw.line((x, y + 318, x + 72, y + 318), fill=GOLD, width=3)
    draw.text((x, y + 336), payback, font=fonts["hero_num"], fill=GREEN)
    draw.text((x, y + 396), "months payback", font=fonts["strong"], fill=GREEN)
    roi_x = x + w // 2 + 8
    draw.line((x + w // 2 - 8, y + 348, x + w // 2 - 8, y + 430), fill=GOLD, width=2)
    _require(fonts["display_lg"], roi, w // 2 - 16, "roi")
    draw.text((roi_x, y + 344), roi, font=fonts["display_lg"], fill=GREEN)
    draw.text((roi_x, y + 386), "year-1 ROI", font=fonts["strong"], fill=GREEN)
    draw.text((x, y + 428), "Bot programme, base containment", font=fonts["small"], fill=MUTED)
    _pill(draw, (x, y + 452), "illustrative inputs", fonts["tiny"])


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
    """1280x640 condensed story. Key content stays inside a 40px margin."""
    del hero_path  # Drawn from the model run, not cropped from the hero file.
    fonts = _story_fonts()
    base = next(item for item in bundle.scenarios if item.scenario_id == "bot_base")
    baseline = next(item for item in bundle.scenarios if item.scenario_id == "baseline_voice_only")
    voice_cost = fmt_unit(baseline.cost_per_contact)
    payback = fmt_months(base.economics.payback_months)
    roi = fmt_roi(base.economics.year1_roi)
    tagline = "Manual care costs time and money. The model prices the payback."
    _require(fonts["social_tag"], tagline, 1200, "tagline")
    if len(_wrap_pil(tagline, fonts["social_tag"], 1200)) != 1:
        raise SystemExit("social tagline wraps onto a second line")

    image = Image.new("RGB", (1280, 640), CREAM)
    draw = ImageDraw.Draw(image)
    draw.text((40, 40), "care-automation-roi", font=fonts["social_name"], fill=GREEN, anchor="lt")
    draw.text((40, 84), tagline, font=fonts["social_tag"], fill=MUTED, anchor="lt")
    draw.rectangle((40, 116, 112, 120), fill=GOLD)

    cards = []
    x = 40
    for _index in range(3):
        cards.append((x, 136, 376, 464))
        x += 376 + 36
    for box, index, kicker in zip(cards, ("01", "02", "03"), ("PROBLEM", "METHOD", "RESULT")):
        _round_card(draw, box)
        _header_label(draw, box, index, kicker, fonts)
    for left, right in zip(cards, cards[1:]):
        arrow = _h_arrow(24, 18)
        gap_x = left[0] + left[2] + (36 - arrow.width) // 2
        _paste(image, arrow, (gap_x, left[1] + left[3] // 2 - arrow.height // 2))

    _draw_social_problem(image, draw, cards[0], fonts, voice_cost)
    _draw_social_method(image, draw, cards[1], fonts, bundle)
    _draw_social_result(image, draw, cards[2], fonts, bundle, payback, roi)
    image.save(ASSETS / "social-preview.png", format="PNG", optimize=True)
    saved = Image.open(ASSETS / "social-preview.png")
    if saved.size != (1280, 640):
        raise SystemExit(f"social preview is {saved.size}")


def _draw_social_problem(image, draw, card, fonts, voice_cost: str) -> None:
    x, y, w, _h = _content_box(card)
    person = _icon(_person, 34, GREEN)
    for index in range(3):
        _paste(image, person, (x + index * 40, y + 6))
    arrow = _h_arrow(26, 14)
    _paste(image, arrow, (x + 126, y + 16))
    headset = _icon(_headset, 52, GREEN)
    _paste(image, headset, (x + w - 64, y + 2))
    draw.text((x + 60, y + 46), "Contacts", font=fonts["tiny"], fill=GREEN, anchor="mt")
    draw.text((x + w - 38, y + 58), "Voice agent", font=fonts["tiny"], fill=GREEN, anchor="mt")
    clock = _icon(_clock, 28, GREEN)
    coins = _icon(_coins, 28, GOLD)
    _paste(image, clock, (x, y + 96))
    draw.text((x + 36, y + 110), "Agent time", font=fonts["tiny"], fill=GREEN, anchor="lm")
    _paste(image, coins, (x + w // 2, y + 96))
    draw.text((x + w // 2 + 36, y + 110), "Wage and telco", font=fonts["tiny"], fill=GREEN, anchor="lm")
    draw.text((x, y + 146), voice_cost, font=fonts["social_num"], fill=GREEN)
    draw.text((x, y + 184), "KES per voice contact", font=fonts["strong_sm"], fill=GREEN)
    draw.text((x, y + 206), "Baseline cost to serve", font=fonts["tiny"], fill=MUTED)
    _pill(draw, (x, y + 230), "illustrative inputs", fonts["tiny"])


def _draw_social_method(image, draw, card, fonts, bundle) -> None:
    x, y, w, _h = _content_box(card)
    draw.text((x, y), "The pipeline", font=fonts["strong"], fill=GREEN)
    steps = [title for title, _subtitle, _icon in _method_steps(bundle)]
    cursor = y + 36
    for index, title in enumerate(steps):
        _require(fonts["strong_sm"], title, w - 8, title)
        draw.text((x, cursor), title, font=fonts["strong_sm"], fill=GREEN)
        if index < len(steps) - 1:
            arrow = _v_arrow(14)
            _paste(image, arrow, (x + 8, cursor + 22))
        cursor += 48


def _draw_social_result(image, draw, card, fonts, bundle, payback: str, roi: str) -> None:
    x, y, w, _h = _content_box(card)
    draw.text((x, y), payback, font=fonts["social_num"], fill=GREEN)
    draw.text((x, y + 36), "months payback", font=fonts["tiny"], fill=MUTED)
    _require(fonts["social_num"], roi, w // 2 - 8, "social roi")
    draw.text((x + w // 2, y), roi, font=fonts["social_num"], fill=GREEN)
    draw.text((x + w // 2, y + 36), "year-1 ROI", font=fonts["tiny"], fill=MUTED)
    small = dict(fonts)
    small["strong"] = fonts["tiny"]
    _draw_roi_chart(image, draw, (x, y + 62, w, 168), _roi_rows(bundle), small)
    note = "Base and high containment clear year 1."
    _require(fonts["tiny"], note, w, "social result note")
    draw.text((x, y + 236), note, font=fonts["tiny"], fill=MUTED)
    _pill(draw, (x, y + 258), "illustrative inputs", fonts["tiny"])


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


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        nargs="+",
        choices=("hero", "social", "charts", "gif"),
        help="Render a subset. The default renders every visual.",
    )
    args = parser.parse_args(argv)
    want = set(args.only) if args.only else {"hero", "social", "charts", "gif"}
    _fonts()
    raw, assumptions = load_assumptions(ROOT / "assumptions.yaml")
    rows, meta = load_taxonomy(ROOT / "data" / "bitext_by_intent.csv", ROOT / "data" / "bitext_meta.json")
    bundle = compute(raw, assumptions, rows, meta)
    if "hero" in want:
        render_hero(bundle)
    if "charts" in want:
        render_unit_costs(bundle)
        render_class_costs(bundle)
        render_payback(bundle)
    if "social" in want:
        render_social(ASSETS / "hero.png", bundle)
    if "gif" in want:
        render_gif()
    for name in ("hero.png", "unit_costs.png", "class_costs.png", "payback_months.png", "social-preview.png"):
        path = ASSETS / name
        if path.exists() and path.suffix == ".png":
            print(f"{name} {path.stat().st_size} bytes {Image.open(path).size}")


if __name__ == "__main__":
    main()
