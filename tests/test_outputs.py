"""Committed reports and the README block match a fresh run of the model."""

import tempfile
from pathlib import Path

from care_roi.assumptions import load_assumptions
from care_roi.report import BEGIN, END, assert_directory_matches, compute, write_reports
from care_roi.taxonomy import load_taxonomy

ROOT = Path(__file__).resolve().parents[1]


def test_committed_reports_match_a_fresh_run():
    raw, assumptions = load_assumptions(ROOT / "assumptions.yaml")
    rows, meta = load_taxonomy(ROOT / "data" / "bitext_by_intent.csv", ROOT / "data" / "bitext_meta.json")
    bundle = compute(raw, assumptions, rows, meta)
    with tempfile.TemporaryDirectory() as tmp:
        write_reports(bundle, Path(tmp))
        assert_directory_matches(ROOT / "reports", Path(tmp))


def test_readme_contains_the_generated_block_exactly():
    block = (ROOT / "reports" / "readme_block.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert block.startswith(BEGIN)
    assert END in block
    assert block in readme
