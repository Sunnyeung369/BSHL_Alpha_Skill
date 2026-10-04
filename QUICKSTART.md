# Quickstart / 快速开始

## Environment

Python 3.10+ and Git. Clone this repository and enter its directory:

```shell
git clone https://github.com/Sunnyeung369/BSHL_Alpha_Skill.git
cd BSHL_Alpha_Skill
```

Use an isolated environment. On Windows installation includes `tzdata` for IANA timezones. JSON Schema validation is a development dependency:

```shell
python -m venv .venv
```

Windows PowerShell: `.venv\Scripts\python -m pip install -e ".[dev]"`.
Linux/macOS: `.venv/bin/python -m pip install -e ".[dev]"`.
Use that same interpreter for verification. Schema tests explicitly report a skip if the optional validator is absent.

```shell
python -m bshl demo --scenario breakout --output outputs/demo
python -m unittest discover -s tests -v
python scripts/check_repository.py
```

Replace `python` with the environment interpreter, or activate the environment first. The demo writes `card.md` and `card.json`. A synthetic breakout can report `simulation_status: Trade Ready`, but its real `final_status` remains `Research Only`. Try `--scenario no-stop` and `--scenario overheated` to see blockers.

For your own CSV, provide metadata and research context following [the data contract](docs/DATA_CONTRACT.md):

```shell
python -m bshl analyze --csv prices.csv --metadata prices.metadata.json --context research.json --as-of 2025-05-23T20:00:00+00:00 --output outputs/my-analysis
```

## Load the skill

Use a folder named `bshl-alpha` containing this repository, including SKILL.md and its relative resources. For Codex, place it in `~/.codex/skills/bshl-alpha`; for Claude Code, `~/.claude/skills/bshl-alpha`. Keep code and references together. Restart/reload the target agent's skill discovery as needed and verify the displayed skill before relying on automatic routing.

Start with an explicit request: “Use bshl-alpha to organize evidence for this asset; list missing data and risk blockers.” Loading instructions does not configure a market-data provider.

## Data boundaries

Legacy Yahoo, SEC, news and Crypto adapter names do not imply working API integrations. Mock sources must be explicitly selected and marked. Missing data cannot establish Trade Ready or Pass. Imported daily CSV is available; live providers are not implemented. See the [roadmap](VERSION_ROADMAP.md) for acceptance.
