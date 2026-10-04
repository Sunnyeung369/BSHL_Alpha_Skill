"""BSHL command line. No credentials or automatic orders."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from .cards import write_card
from .serialization import dumps


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
    backtest.add_argument("--output", default="outputs/backtest.json")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        from .market import load_dataset
        from .engine import build_card
        if args.command == "backtest":
            from datetime import date
            from .backtest import BacktestConfig, run_backtest
            from .files import write_json
            dataset = load_dataset(args.csv, args.metadata)
            config = json.loads(Path(args.config).read_text(encoding="utf-8")) if args.config else {}
            setup = BacktestConfig(train_end=date.fromisoformat(args.train_end),
                                   test_start=date.fromisoformat(args.test_start), **config)
            result = run_backtest(dataset, setup)
            path = write_json(result, args.output)
            print(dumps({"report": str(path), "is_mock": result["is_mock"],
                         "performance_validated": False, "trade_count": result["trade_count"]}))
            return 0
        if args.command == "demo":
            assets = Path(__file__).with_name("assets")
            scenario = "overheated" if args.scenario == "overheated" else "breakout"
            dataset = load_dataset(assets / (scenario + ".csv"), assets / (scenario + ".metadata.json"))
            context = json.loads((assets / "demo.context.json").read_text(encoding="utf-8"))
            if args.scenario == "no-stop":
                context.pop("stop_loss_price")
            as_of = None
        else:
            dataset = load_dataset(args.csv, args.metadata)
            context = json.loads(Path(args.context).read_text(encoding="utf-8"))
            as_of = datetime.fromisoformat(args.as_of) if args.as_of else None
        card = build_card(dataset, context, as_of=as_of)
        path = write_card(card, args.output)
        print(dumps({"card": str(path), "state": card["final_status"], "is_mock": card["is_mock"], "analysis_id": card["analysis_id"]}))
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as exc:
        print(f"BSHL: {exc}", file=sys.stderr)
        return 2

