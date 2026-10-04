"""Self-contained SVG cards. All input is escaped; no remote assets or scripts."""
from html import escape
from pathlib import Path
import textwrap
from .workspace import validate_card


def render_svg(card):
    card = validate_card(card)
    plan = card.get("trade_plan", {})
    label = "MOCK / SYNTHETIC" if card["is_mock"] else card["data_mode"].upper()
    rows = [f"{card['symbol']}  |  {card['final_status']}", f"{label}  |  As of {card['as_of']}",
            f"Structure: {card.get('technical_structure', {}).get('state', 'unknown')}",
            f"Rule: {card['rule_version']}", f"Analysis ID: {card['analysis_id']}",
            f"Selected stop: {plan.get('stop_loss_price')}  |  Target: {plan.get('target_price')}",
            "Invalidation: selected stop breached or available thesis kill switch",
            "Blockers: " + (", ".join(card.get("blockers", [])) or "No recorded blockers")]
    rows += textwrap.wrap("Source (user supplied): " + card.get("source", {}).get("url", "unknown"), width=115)
    rows += ["Research assistance. Heuristic points are not return probabilities.",
             "Synthetic outputs do not establish a trading edge. No orders placed."]
    texts = []
    for index, row in enumerate(rows):
        texts.append(f'<text x="64" y="{110 + index * 37}" font-size="{30 if index == 0 else 16}" fill="{"#8ee5ce" if index == 0 else "#dce7f3"}">{escape(row)}</text>')
    height = max(630, 145 + len(rows) * 37)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}">'
            '<rect width="1200" height="100%" rx="20" fill="#101b2c"/>'
            '<g font-family="Segoe UI, Arial, sans-serif">' + "".join(texts) + '</g></svg>\n')


def write_share(card, path):
    target = Path(path)
    content = render_svg(card)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8") as handle:
            handle.write(content)
    except FileExistsError:
        if target.read_text(encoding="utf-8") != content:
            raise ValueError("Share output exists with different content; use a new path")
    return target
