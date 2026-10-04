import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from bshl.cli import main


class CliTests(unittest.TestCase):
    def test_demo_stays_synthetic_and_repeats(self):
        with tempfile.TemporaryDirectory() as directory:
            outputs = []
            for _ in range(2):
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    self.assertEqual(main(["demo", "--output", directory]), 0)
                outputs.append(json.loads(stream.getvalue()))
            self.assertEqual(outputs[0], outputs[1])
            self.assertTrue(outputs[0]["is_mock"])
            self.assertEqual(outputs[0]["state"], "Research Only")
            self.assertIn("MOCK / SYNTHETIC", (Path(directory) / "card.md").read_text(encoding="utf-8"))

    def test_existing_different_card_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "card.json"
            target.write_text("user content", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["demo", "--output", directory]), 2)
            self.assertEqual(target.read_text(encoding="utf-8"), "user content")

    def test_missing_input_returns_actionable_error(self):
        with contextlib.redirect_stderr(io.StringIO()) as stream:
            self.assertEqual(main(["analyze", "--csv", "missing.csv", "--metadata", "missing.json", "--context", "missing.json"]), 2)
        self.assertIn("BSHL:", stream.getvalue())
