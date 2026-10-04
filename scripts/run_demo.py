"""Three offline examples; checks outcomes and reports measured runtime."""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bshl.cards import write_card
from bshl.engine import build_card
from bshl.market import load_dataset
from bshl.share import write_share


def run(output):
    started = time.perf_counter()
    assets = Path(__file__).resolve().parents[1] / "bshl/assets"
    results = []
    for scenario in ("breakout", "no-stop", "overheated", "pullback-rebound", "breakdown"):
        name = scenario if scenario in ("pullback-rebound", "breakdown") else ("overheated" if scenario == "overheated" else "breakout")
        data = load_dataset(assets / (name + ".csv"), assets / (name + ".metadata.json"))
        context = json.loads((assets / "demo.context.json").read_text(encoding="utf-8"))
        if scenario == "no-stop":
            context.pop("stop_loss_price")
        if scenario == "breakdown":
            context["stop_loss_price"] = 119.5
        card = build_card(data, context)
        assert card["is_mock"] and card["final_status"] == "Research Only"
        if scenario == "breakout":
            assert card["technical_structure"]["state"] == "Confirmed Breakout"
            assert card["simulation_status"] == "Trade Ready"
        elif scenario == "pullback-rebound":
            assert card["technical_structure"]["state"] == "Pullback Entry Zone"
            assert card["simulation_status"] == "Trade Ready"
        elif scenario == "breakdown":
            assert card["technical_structure"]["state"] == "Breakdown"
            assert card["simulation_status"] == "Veto"
        elif scenario == "no-stop":
            assert "user_stop_missing_or_invalid" in card["blockers"]
            assert card["simulation_status"] != "Trade Ready"
        else:
            assert card["technical_structure"]["state"] == "Exhaustion"
            assert card["simulation_status"] != "Trade Ready"
        write_card(card, Path(output) / scenario)
        write_share(card, Path(output) / scenario / "share.svg")
        results.append({"scenario": scenario, "analysis_id": card["analysis_id"],
                        "structure": card["technical_structure"]["state"],
                        "final_status": card["final_status"], "simulation_status": card["simulation_status"]})
    print(json.dumps({"elapsed_seconds": round(time.perf_counter() - started, 3), "cases": results}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="outputs/three-cases")
    run(parser.parse_args().output)
