"""Compile source and reject dangling local Markdown links or unsafe tracked data."""
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
errors = []
for path in root.rglob("*.py"):
    if any(part in {".venv", "build", ".git"} for part in path.parts):
        continue
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except (SyntaxError, UnicodeError) as exc:
        errors.append(str(exc))
for path in root.rglob("*.md"):
    if any(part in {".venv", "build", ".git"} for part in path.parts):
        continue
    for link in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
        target = link.split("#", 1)[0].split(" \"", 1)[0].strip("<>")
        if not target or ":" in target or target.startswith("/"):
            continue
        if not (path.parent / target).exists():
            errors.append(f"Dangling link: {path.relative_to(root)} -> {target}")
tracked = subprocess.run(["git", "ls-files"], cwd=root, text=True, capture_output=True, check=True).stdout.splitlines()
for name in tracked:
    if name == ".env" or name.endswith(("decisions.jsonl", "rules.json")) or name.startswith("outputs/"):
        errors.append(f"Private/generated file tracked: {name}")
skill = (root / "SKILL.md").read_text(encoding="utf-8")
if not skill.startswith("---\n") or not re.search(r"(?m)^name: bshl-alpha$", skill) or not re.search(r"(?m)^description: .+", skill):
    errors.append("Skill needs name and description frontmatter")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("Repository compilation, links, skill entrypoint and tracked-file checks passed")

