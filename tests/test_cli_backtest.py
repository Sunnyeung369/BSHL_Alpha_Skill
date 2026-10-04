from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from bshl.cli import main

ASSETS = Path(__file__).resolve().parents[1] / "bshl/assets"


class BacktestCliTests(unittest.TestCase):
    def test_candidate_comparison_keeps_identical_split_without_deploying(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "candidate.json"
            config.write_text('{"lookback": 10}')
            output = Path(folder) / "comparison.json"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["backtest", "--csv", str(ASSETS / "breakout.csv"),
                    "--metadata", str(ASSETS / "breakout.metadata.json"),
                    "--train-end", "2025-04-30", "--test-start", "2025-05-01",
                    "--compare-config", str(config), "--output", str(output)]), 0)
            report = json.loads(output.read_text())
            self.assertEqual(report["baseline"]["split_protocol"], report["candidate"]["split_protocol"])
            self.assertFalse(report["automatically_applied"])

    def test_report_round_trip_and_idempotence(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "simulation.json"
            args = ["backtest", "--csv", str(ASSETS / "breakout.csv"),
                    "--metadata", str(ASSETS / "breakout.metadata.json"),
                    "--train-end", "2025-04-30", "--test-start", "2025-05-01", "--output", str(output)]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
                self.assertEqual(main(args), 0)
            result = json.loads(output.read_text())
            self.assertFalse(result["performance_validated"])
            self.assertTrue(result["is_mock"])
            self.assertIn("parameters", result)
            output.write_text("{}")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(args), 2)
            self.assertEqual(output.read_text(), "{}")
