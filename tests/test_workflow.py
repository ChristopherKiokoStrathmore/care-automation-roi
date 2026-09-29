import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflows" / "n8n_emergency_escalation.json"


def test_workflow_is_import_shaped_and_not_marked_active():
    document = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    assert document["active"] is False
    names = {node["name"] for node in document["nodes"]}
    for node in document["nodes"]:
        for key in ("id", "name", "type", "typeVersion", "position", "parameters"):
            assert key in node
    for source, outputs in document["connections"].items():
        assert source in names
        for group in outputs["main"]:
            for link in group:
                assert link["node"] in names
                assert link["type"] == "main"
    encoded = json.dumps(document)
    assert "emergency" in encoded
    assert "senior_agent" in encoded
    assert "credentials" not in document
    for node in document["nodes"]:
        assert "credentials" not in node


def test_workflow_readme_says_it_was_not_run():
    text = (ROOT / "workflows" / "README.md").read_text(encoding="utf-8")
    assert "has not been imported" in text
    assert "has not been executed" in text
    assert "emergency" in text
