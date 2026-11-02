import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_every_source_has_a_checked_license():
    config = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    allowed = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause"}
    assert all(r["license"] in allowed for r in config["repos"])


def test_eval_questions_are_well_formed():
    lines = (ROOT / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line.strip()]
    assert rows and all(r["q"] and r["gold"] for r in rows)
