# Quickstart / 快速开始

## Environment

Python 3.10+ and Git. Clone this repository and enter its directory:

```shell
git clone https://github.com/Sunnyeung369/BSHL_Alpha_Skill.git
cd BSHL_Alpha_Skill
python -m unittest discover -s tests -v
python scripts/check_repository.py
```

The runtime has no third-party dependencies. For packaging and schema tests, use an isolated environment:

```shell
python -m venv .venv
```

Windows PowerShell: `.venv\Scripts\python -m pip install -e ".[dev]"`.
Linux/macOS: `.venv/bin/python -m pip install -e ".[dev]"`.
Use that same interpreter for verification. Schema tests explicitly report a skip if the optional validator is absent.

## Load the skill

Use a folder named `bshl-alpha` containing this repository, including SKILL.md and its relative resources. For Codex, place it in `~/.codex/skills/bshl-alpha`; for Claude Code, `~/.claude/skills/bshl-alpha`. Keep code and references together. Restart/reload the target agent's skill discovery as needed and verify the displayed skill before relying on automatic routing.

Start with an explicit request: “Use bshl-alpha to organize evidence for this asset; list missing data and risk blockers.” Loading instructions does not configure a market-data provider.

## Data boundaries

Legacy Yahoo, SEC, news and Crypto adapter names do not imply working API integrations. Mock sources must be explicitly selected and marked. Missing data cannot establish Trade Ready or Pass. Live and imported-data workflows are added with documented acceptance in the [roadmap](VERSION_ROADMAP.md).
