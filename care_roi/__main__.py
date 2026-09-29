"""CLI for the cost model.

    python -m care_roi
    python -m care_roi --set volume.annual_contacts=100000 --out /tmp/roi-try
    python -m care_roi --check
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from care_roi.assumptions import load_assumptions
from care_roi.report import (
    assert_directory_matches,
    compute,
    replace_readme_block,
    write_reports,
)
from care_roi.taxonomy import load_taxonomy

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Contact-centre automation ROI model")
    parser.add_argument("--assumptions", type=Path, default=ROOT / "assumptions.yaml")
    parser.add_argument("--taxonomy", type=Path, default=ROOT / "data" / "bitext_by_intent.csv")
    parser.add_argument("--meta", type=Path, default=ROOT / "data" / "bitext_meta.json")
    parser.add_argument("--out", type=Path, default=ROOT / "reports")
    parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override one numeric assumption. Repeat for several.",
    )
    parser.add_argument(
        "--write-readme",
        type=Path,
        default=None,
        help="Replace the generated-figures block in this README.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate reports in a temp directory and compare them to --out.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw, assumptions = load_assumptions(args.assumptions, args.overrides)
    rows, meta = load_taxonomy(args.taxonomy, args.meta)
    bundle = compute(raw, assumptions, rows, meta)
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            actual = Path(tmp)
            write_reports(bundle, actual)
            assert_directory_matches(args.out, actual)
            if args.write_readme is not None:
                block = (actual / "readme_block.md").read_text(encoding="utf-8")
                text = args.write_readme.read_text(encoding="utf-8")
                if block not in text:
                    raise SystemExit("README is missing the generated figures block")
        print("reports match")
        return 0
    write_reports(bundle, args.out)
    if args.write_readme is not None:
        block = (args.out / "readme_block.md").read_text(encoding="utf-8")
        replace_readme_block(args.write_readme, block)
    base = next(item for item in bundle.scenarios if item.scenario_id == "bot_base")
    print(
        f"bot_base cost_per_contact={base.cost_per_contact} "
        f"payback_months={base.economics.payback_months} "
        f"year1_roi={base.economics.year1_roi}"
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
