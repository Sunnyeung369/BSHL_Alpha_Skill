"""Recompute golden fixtures and validate all public JSON Schemas."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jsonschema import Draft7Validator, FormatChecker
from bshl.cards import markdown
from bshl.engine import build_card
from bshl.market import load_dataset
from bshl.share import render_svg

root = Path(__file__).resolve().parents[1]
for path in (root / "schemas").glob("*.json"):
    Draft7Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
validator = Draft7Validator(json.loads((root / "schemas/research_card.schema.json").read_text(encoding="utf-8")), format_checker=FormatChecker())
for scenario in ("breakout", "no-stop", "overheated", "pullback-rebound", "breakdown"):
    name = scenario if scenario in ("pullback-rebound", "breakdown") else ("overheated" if scenario == "overheated" else "breakout")
    assets = root / "bshl/assets"
    dataset = load_dataset(assets / (name + ".csv"), assets / (name + ".metadata.json"))
    context = json.loads((assets / "demo.context.json").read_text(encoding="utf-8"))
    if scenario == "no-stop":
        context.pop("stop_loss_price")
    if scenario == "breakdown":
        context["stop_loss_price"] = 119.5
    expected = build_card(dataset, context)
    folder = root / "examples/current" / scenario
    actual = json.loads((folder / "card.json").read_text(encoding="utf-8"))
    validator.validate(actual)
    if actual != expected or (folder / "card.md").read_text(encoding="utf-8") != markdown(expected) or (folder / "share.svg").read_text(encoding="utf-8") != render_svg(expected):
        sys.exit(f"Stale or tampered public example: {scenario}")
print("All schemas valid; five public cards, Markdown and SVG match frozen inputs")
