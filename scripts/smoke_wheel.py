"""Install a built wheel into a clean temporary venv and exercise its entrypoint."""
import argparse
import re
import os
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser()
selection = parser.add_mutually_exclusive_group(required=True)
selection.add_argument("--wheel")
selection.add_argument("--wheel-dir")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
expected = re.search(r'(?m)^__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"$',
                     (root / "bshl/__init__.py").read_text(encoding="utf-8")).group(1)
wheel = (Path(args.wheel) if args.wheel else Path(args.wheel_dir) / f"bshl_alpha-{expected}-py3-none-any.whl").resolve()
if not wheel.is_file() or wheel.suffix != ".whl":
    raise ValueError("Expected a built wheel")
output = root / "outputs"
output.mkdir(exist_ok=True)
environment = os.environ.copy()
environment.pop("PYTHONPATH", None)
environment["PYTHONUTF8"] = "1"
with tempfile.TemporaryDirectory(prefix="wheel-smoke-", dir=output) as temporary:
    folder = Path(temporary).resolve()
    if not folder.is_relative_to(output.resolve()):
        raise RuntimeError("Smoke environment must stay inside outputs")
    subprocess.run([sys.executable, "-m", "venv", str(folder / "env")], check=True)
    bin_dir = folder / "env" / ("Scripts" if os.name == "nt" else "bin")
    python = bin_dir / ("python.exe" if os.name == "nt" else "python")
    subprocess.run([str(python), "-m", "pip", "install", str(wheel)], cwd=folder, env=environment, check=True)
    subprocess.run([str(python), "-c", f"import bshl, scoring, data, replay; assert bshl.__version__ == {expected!r}; print('Installed version:', bshl.__version__)"], cwd=folder, env=environment, check=True)
    entrypoint = bin_dir / ("bshl.exe" if os.name == "nt" else "bshl")
    subprocess.run([str(entrypoint), "demo", "--output", str(folder / "demo")], cwd=folder, env=environment, check=True)
    commands = [
        ["journal", "--db", str(folder / "journal.sqlite3"), "save", "--card", str(folder / "demo/card.json"), "--watch"],
        ["journal", "--db", str(folder / "journal.sqlite3"), "export", "--output", str(folder / "export.json")],
        ["journal", "restore", "--input", str(folder / "export.json"), "--target", str(folder / "restored.sqlite3")],
        ["share", "--card", str(folder / "demo/card.json"), "--output", str(folder / "share.svg")],
    ]
    for command in commands:
        subprocess.run([str(entrypoint), *command], cwd=folder, env=environment, check=True)
print("Clean-wheel imports, packaged demo, journal save/export/restore and share passed")
