"""Install a built wheel into a clean temporary venv and exercise its entrypoint."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--wheel", required=True)
args = parser.parse_args()
wheel = Path(args.wheel).resolve()
if not wheel.is_file() or wheel.suffix != ".whl":
    raise ValueError("Expected a built wheel")
root = Path(__file__).resolve().parents[1]
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
    subprocess.run([str(python), "-c", "import bshl, scoring, data, replay; assert bshl.__version__ == '0.9.0'; print('Installed version:', bshl.__version__)"], cwd=folder, env=environment, check=True)
    entrypoint = bin_dir / ("bshl.exe" if os.name == "nt" else "bshl")
    subprocess.run([str(entrypoint), "demo", "--output", str(folder / "demo")], cwd=folder, env=environment, check=True)
print("Wheel installed in a clean environment; imports and packaged CLI/assets passed")
