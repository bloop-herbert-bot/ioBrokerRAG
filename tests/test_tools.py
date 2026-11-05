import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_every_source_has_an_allowed_license():
    from iobroker_rag import licenses
    config = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    policy = config["license_policy"]
    assert all(licenses.classify(r["license"], policy) == "allow" for r in config["repos"])
    generated = ROOT / config["generated"]
    if generated.exists():
        for entry in json.loads(generated.read_text(encoding="utf-8"))["repos"]:
            assert entry["policy"] in ("allow", "review") and licenses.classify(entry["license"], policy) != "deny"


def test_eval_questions_are_well_formed():
    lines = (ROOT / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line.strip()]
    assert rows and all(r["q"] and r["gold"] for r in rows)
