"""Portable text cards; preserve data labels in every export."""
from pathlib import Path
from .serialization import dumps


def markdown(card):
    lines = [f"# BSHL research card — {card.get('symbol', 'unknown')}", "",
        f"**State:** {card.get('final_status', 'Research Only')}",
        f"**Data:** {'MOCK / SYNTHETIC' if card.get('is_mock') else card.get('data_mode', 'unknown')}",
        f"**As of:** {card.get('as_of', 'unknown')}",
        f"**Analysis ID:** {card.get('analysis_id', 'unknown')}", "",
        "## Reasons / blockers", ""]
    reasons = card.get("blockers", []) or card.get("reasons", [])
    lines.extend("- " + str(item) for item in reasons)
    lines.extend(["", "## Reproducible details", "", "```json", dumps(card), "```", "",
        "Research preparation only. Synthetic results do not establish a trading edge.", ""])
    return "\n".join(lines)


def write_card(card, output):
    folder = Path(output)
    folder.mkdir(parents=True, exist_ok=True)
    contents = {"card.json": dumps(card) + "\n", "card.md": markdown(card)}
    for name, content in contents.items():
        path = folder / name
        if path.exists() and path.read_text(encoding="utf-8") != content:
            raise FileExistsError(f"Choose a new output folder; existing card differs: {path}")
    for name, content in contents.items():
        (folder / name).write_text(content, encoding="utf-8")
    return folder / "card.md"

