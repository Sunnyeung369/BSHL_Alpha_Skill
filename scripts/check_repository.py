"""Compile source and reject dangling local Markdown links or unsafe tracked data."""
from pathlib import Path
import re
import subprocess
import sys
import yaml

root = Path(__file__).resolve().parents[1]
errors = []
for path in root.rglob("*.py"):
    if any(part in {".venv", "build", ".git", "outputs"} for part in path.parts):
        continue
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except (SyntaxError, UnicodeError) as exc:
        errors.append(str(exc))
for path in root.rglob("*.md"):
    if any(part in {".venv", "build", ".git", "outputs"} for part in path.parts):
        continue
    for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
        target = link.split("#", 1)[0].split(" \"", 1)[0].strip("<>")
        if not target or ":" in target or target.startswith("/"):
            continue
        if not (path.parent / target).exists():
            errors.append(f"Dangling link: {path.relative_to(root)} -> {target}")
tracked = subprocess.run(["git", "ls-files"], cwd=root, text=True, capture_output=True, check=True).stdout.splitlines()
for name in tracked:
    if name == ".env" or name.endswith(("decisions.jsonl", "rules.json", ".sqlite3", ".sqlite3-journal")) or name.startswith("outputs/"):
        errors.append(f"Private/generated file tracked: {name}")
for path in (root / ".github/ISSUE_TEMPLATE").glob("*.yml"):
    form = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(form, dict) or not form.get("name") or not form.get("description") or not isinstance(form.get("body"), list):
        errors.append(f"Invalid issue form: {path.name}")
        continue
    ids = [item.get("id") for item in form["body"]]
    if None in ids or len(ids) != len(set(ids)):
        errors.append(f"Issue form needs unique field IDs: {path.name}")
workflow = yaml.safe_load((root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
if workflow.get("permissions") != {"contents": "read"}:
    errors.append("Verification workflow must use read-only repository permissions")
skill = (root / "SKILL.md").read_text(encoding="utf-8")
from bshl import __version__
if not re.search(r'(?m)^version = "' + re.escape(__version__) + r'"$', (root / "pyproject.toml").read_text(encoding="utf-8")):
    errors.append("Package and Python versions differ")
if not skill.startswith("---\n") or not re.search(r"(?m)^name: bshl-alpha$", skill) or not re.search(r"(?m)^description: .+", skill):
    errors.append("Skill needs name and description frontmatter")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("Repository compilation, links, skill entrypoint and tracked-file checks passed")

