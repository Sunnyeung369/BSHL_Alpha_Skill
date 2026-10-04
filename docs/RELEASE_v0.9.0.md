# BSHL v0.9.0 — reproducible research and risk cards

This prerelease turns a broken research prototype into an executable offline workflow: dated daily CSV → deterministic structure → evidence/risk card → immutable journal → outcome review and recovery.

## Changes

- Strict numeric validation, unknown risk gates, required stops/closed bars, explicit mock modes and repaired imports/persistence.
- Provenance-aware CSV, Wilder ATR/MA/pivot structure and timestamped evidence/kill-switch gates. Bundled synthetic cases stay Research Only.
- US cash event simulation with next-open entries, gap/stop/target exits, bilateral costs, equity, baseline and fixed in/out-of-sample windows.
- SQLite snapshots, watchlist changes, review calendars, user choices, constrained cash sizing and append-only outcome records; exclusive export/restore.
- Candidate comparison and human approval for new holdout evaluation; hard-risk gates cannot be changed automatically.
- Bilingual introduction, no-key demo, SVG share cards, repository cover, contribution fixtures and CI.

## Validation and limits

Regression, temporal, schema, CLI, journal-recovery and fixture tests run in an isolated environment. GitHub CI uses Windows/Linux/macOS and Python 3.10/3.13. The public workflow result and tag commit are the publishing evidence.

Local suite: 130 tests passed. All six implementation CI environments passed after fixing a version-dependent MA summation difference. Public JSON/Markdown/SVG examples are strictly recomputed, and the built wheel was installed and exercised in a new environment. Topics and two focused contribution issues are configured. Social Preview PNG is supplied; its GitHub Settings upload remains unfinished due to browser/control failure.

No authenticated live provider, broker, autonomous order execution, background monitoring, corporate-action handling or validated profitability is included. Context scores and source authenticity are user-supplied. The price simulator does not recreate historical Alpha research. Synthetic demo results are engineering checks, not investment results. Real usage feedback and live Agent loading remain separate acceptance work.
