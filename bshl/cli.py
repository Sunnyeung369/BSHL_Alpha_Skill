"""BSHL command line. No credentials or automatic orders."""
import argparse
from pathlib import Path
import sys
import sqlite3
from .cards import write_card
from .serialization import dumps, loads


def build_parser():
    parser = argparse.ArgumentParser(prog="bshl", description="Evidence-first research and risk cards")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Analyze a CSV with explicit metadata and research context")
    analyze.add_argument("--csv", required=True)
    analyze.add_argument("--metadata", required=True)
    analyze.add_argument("--context", required=True)
    analyze.add_argument("--as-of", help="Timezone-aware decision time")
    analyze.add_argument("--output", default="outputs/analysis")
    demo = sub.add_parser("demo", help="No-key synthetic example; not market performance")
    demo.add_argument("--scenario", choices=("breakout", "no-stop", "overheated"), default="breakout")
    demo.add_argument("--output", default="outputs/demo")
    backtest = sub.add_parser("backtest", help="Historical US cash simulation; not validated performance")
    backtest.add_argument("--csv", required=True)
    backtest.add_argument("--metadata", required=True)
    backtest.add_argument("--train-end", required=True, help="ISO date, fixed before evaluating the holdout")
    backtest.add_argument("--test-start", required=True, help="ISO date strictly after train-end")
    backtest.add_argument("--config", help="JSON overrides for BacktestConfig; split dates are supplied on CLI")
    backtest.add_argument("--compare-config", help="Run a candidate with the same fixed split; does not deploy it")
    backtest.add_argument("--output", default="outputs/backtest.json")
    journal = sub.add_parser("journal", help="Local snapshots, watchlists, user decisions and review")
    journal.add_argument("--db", default="outputs/workspace.sqlite3")
    actions = journal.add_subparsers(dest="action", required=True)
    save = actions.add_parser("save")
    save.add_argument("--card", required=True)
    save.add_argument("--watch", action="store_true")
    save.add_argument("--condition", action="append")
    show = actions.add_parser("status")
    show.add_argument("--as-of", required=True)
    decision = actions.add_parser("decide")
    decision.add_argument("--id", required=True)
    decision.add_argument("--choice", choices=("research", "wait", "approve_plan", "reject_plan"), required=True)
    decision.add_argument("--at", required=True)
    decision.add_argument("--note", default="")
    review = actions.add_parser("review")
    review.add_argument("--id", required=True)
    review.add_argument("--outcome", choices=("profit", "loss", "no_trade", "unknown"), required=True)
    review.add_argument("--at", required=True)
    review.add_argument("--r", type=float)
    review.add_argument("--costs", type=float, default=0)
    review.add_argument("--note", default="")
    event = actions.add_parser("event")
    event.add_argument("--symbol", required=True)
    event.add_argument("--name", required=True)
    event.add_argument("--at", required=True)
    event.add_argument("--source", required=True)
    proposal = actions.add_parser("propose")
    proposal.add_argument("--proposal", required=True)
    candidate = actions.add_parser("candidate-review")
    candidate.add_argument("--id", required=True)
    candidate.add_argument("--choice", choices=("approve_for_holdout", "reject"), required=True)
    candidate.add_argument("--at", required=True)
    candidate.add_argument("--note", required=True)
    export = actions.add_parser("export")
    export.add_argument("--output", required=True)
    restore = actions.add_parser("restore")
    restore.add_argument("--input", required=True)
    restore.add_argument("--target", required=True)
    size = sub.add_parser("size", help="Calculate constrained allocation from a card and account context")
    size.add_argument("--card", required=True)
    size.add_argument("--account", required=True)
    size.add_argument("--output", default="outputs/sizing.json")
    share = sub.add_parser("share", help="Export an SVG with provenance, data labels and invalidation")
    share.add_argument("--card", required=True)
    share.add_argument("--output", default="outputs/research-card.svg")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "share":
            from .share import write_share
            path = write_share(loads(Path(args.card).read_text(encoding="utf-8-sig")), args.output)
            print(dumps({"share_card": str(path)}))
            return 0
        if args.command == "journal":
            from .workspace import Workspace
            from .files import write_json
            if args.action == "restore":
                workspace = Workspace.restore(loads(Path(args.input).read_text(encoding="utf-8-sig")), args.target)
                result = {"restored": str(workspace.path)}
            else:
                workspace = Workspace(args.db)
                if args.action == "save":
                    result = workspace.save(loads(Path(args.card).read_text(encoding="utf-8-sig")), watch=args.watch, conditions=args.condition)
                elif args.action == "status":
                    result = workspace.status(args.as_of)
                elif args.action == "decide":
                    result = {"id": workspace.decide(args.id, args.choice, args.at, args.note)}
                elif args.action == "review":
                    result = {"id": workspace.review(args.id, args.outcome, args.at, realized_r=args.r, costs=args.costs, note=args.note)}
                elif args.action == "event":
                    result = {"id": workspace.schedule(args.symbol, args.name, args.at, args.source)}
                elif args.action == "propose":
                    result = {"id": workspace.propose(loads(Path(args.proposal).read_text(encoding="utf-8-sig")))}
                elif args.action == "candidate-review":
                    result = {"id": workspace.approve_candidate(args.id, args.choice, args.at, args.note)}
                else:
                    result = {"export": str(write_json(workspace.export(), args.output))}
            print(dumps(result))
            return 0
        if args.command == "size":
            from .portfolio import size_plan
            from .files import write_json
            result = size_plan(loads(Path(args.card).read_text(encoding="utf-8-sig")),
                               loads(Path(args.account).read_text(encoding="utf-8-sig")))
            print(dumps({"report": str(write_json(result, args.output))}))
            return 0
        from .market import load_dataset, parse_timestamp
        from .engine import build_card
        if args.command == "backtest":
            from datetime import date
            from .backtest import BacktestConfig, run_backtest
            from .files import write_json
            dataset = load_dataset(args.csv, args.metadata)
            config = loads(Path(args.config).read_text(encoding="utf-8-sig")) if args.config else {}
            setup = BacktestConfig(train_end=date.fromisoformat(args.train_end),
                                   test_start=date.fromisoformat(args.test_start), **config)
            result = run_backtest(dataset, setup)
            if args.compare_config:
                candidate = loads(Path(args.compare_config).read_text(encoding="utf-8-sig"))
                candidate_setup = BacktestConfig(train_end=setup.train_end, test_start=setup.test_start, **candidate)
                alternative = run_backtest(dataset, candidate_setup)
                result = {"baseline": result, "candidate": alternative, "automatically_applied": False,
                          "split_identical": True, "is_mock": dataset.is_mock, "performance_validated": False,
                          "trade_count": result["trade_count"]}
            path = write_json(result, args.output)
            print(dumps({"report": str(path), "is_mock": result["is_mock"],
                         "performance_validated": False, "trade_count": result["trade_count"]}))
            return 0
        if args.command == "demo":
            assets = Path(__file__).with_name("assets")
            scenario = "overheated" if args.scenario == "overheated" else "breakout"
            dataset = load_dataset(assets / (scenario + ".csv"), assets / (scenario + ".metadata.json"))
            context = loads((assets / "demo.context.json").read_text(encoding="utf-8-sig"))
            if args.scenario == "no-stop":
                context.pop("stop_loss_price")
            as_of = None
        else:
            dataset = load_dataset(args.csv, args.metadata)
            context = loads(Path(args.context).read_text(encoding="utf-8-sig"))
            as_of = parse_timestamp(args.as_of) if args.as_of else None
        card = build_card(dataset, context, as_of=as_of)
        path = write_card(card, args.output)
        print(dumps({"card": str(path), "state": card["final_status"], "is_mock": card["is_mock"], "analysis_id": card["analysis_id"]}))
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, sqlite3.Error) as exc:
        print(f"BSHL: {exc}", file=sys.stderr)
        return 2

