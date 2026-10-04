"""Explainable cash sizing; never turns a research card into an order."""
from scoring.position_risk_score import PositionRiskScorer
from .serialization import to_jsonable
from .workspace import validate_card


def size_plan(card, account):
    card = validate_card(card)
    if not isinstance(account, dict):
        raise ValueError("account must be an object")
    if "stop_loss_fraction" in account:
        raise ValueError("Stop distance is derived from the selected card stop")
    account = dict(account)
    if account.pop("currency", None) != card["source"]["currency"]:
        raise ValueError("Account currency must explicitly match the asset currency; FX is unsupported")
    plan = card["trade_plan"]
    stop_fraction = (plan["entry_price"] - plan["stop_loss_price"]) / plan["entry_price"] if plan["stop_loss_defined"] else None
    result = to_jsonable(PositionRiskScorer().score(**account, stop_loss_fraction=stop_fraction))
    gated = card["final_status"] != "Trade Ready"
    additional = 0 if gated else result["recommended_additional_size"]
    return {"analysis_id": card["analysis_id"], "currency": card["source"]["currency"],
            "is_mock": card["is_mock"], "readiness_gate_blocked": gated,
            "score": result, "permitted_research_increment": additional,
            "whole_share_cap": int(additional / plan["entry_price"]), "orders_placed": False,
            "assumptions": "Same account/asset currency; unlevered cash; stops may gap; costs need a separate budget"}
