"""Explicitly refresh the three repository fixtures after reviewed rule changes."""
from pathlib import Path
import tempfile
from run_demo import run

root = Path(__file__).resolve().parents[1]
destination = root / "examples/current"
if not destination.resolve().is_relative_to(root.resolve()):
    raise RuntimeError("Examples must stay inside this repository")
with tempfile.TemporaryDirectory(prefix="bshl-examples-") as temporary:
    run(temporary)
    for scenario in ("breakout", "no-stop", "overheated"):
        folder = destination / scenario
        if not folder.resolve().is_relative_to(destination.resolve()):
            raise RuntimeError("Fixture folder resolves outside examples")
        folder.mkdir(parents=True, exist_ok=True)
        for name in ("card.json", "card.md", "share.svg"):
            target = folder / name
            if not target.resolve().is_relative_to(destination.resolve()):
                raise RuntimeError("Fixture target resolves outside examples")
            target.write_bytes((Path(temporary) / scenario / name).read_bytes())
print("Reviewed fixture outputs refreshed; run validate_examples.py and inspect the diff")
