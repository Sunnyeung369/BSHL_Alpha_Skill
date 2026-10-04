# Local research journal

The SQLite journal is transactional. Snapshots, user decisions, reviews, calendar events, change notifications and candidate reviews are append-only. A duplicate identical record is idempotent; a different card with the same analysis ID fails. The digest checks record integrity, not source authenticity.

## A complete offline round trip

```shell
python -m bshl demo --output outputs/journal-demo
python -m bshl journal --db outputs/workspace.sqlite3 save --card outputs/journal-demo/card.json --watch --condition "Review when evidence expires"
python -m bshl journal --db outputs/workspace.sqlite3 status --as-of 2025-05-24T00:00:00+00:00
python -m bshl journal --db outputs/workspace.sqlite3 export --output outputs/workspace-export.json
python -m bshl journal restore --input outputs/workspace-export.json --target outputs/restored.sqlite3
```

Use `analysis_id` from the saved card for:

```shell
python -m bshl journal decide --id ANALYSIS_ID --choice wait --at 2025-05-24T00:00:00+00:00
python -m bshl journal review --id ANALYSIS_ID --outcome no_trade --at 2025-05-24T00:00:00+00:00 --note "Missed upside does not invalidate a hard risk gate"
python -m bshl journal event --symbol DEMO --name "Fictional earnings review" --at 2025-06-01T12:00:00+00:00 --source https://example.invalid/fixture
```

Replace `ANALYSIS_ID`; it is a placeholder, not an executable literal. The last three commands use the default `outputs/workspace.sqlite3`; add `--db` before the subcommand for another journal.

When you import a new card for a watched symbol, saving it updates the watchlist and records changes to status, structure and blockers. A new price <= the previous selected stop produces an invalidation reason. Older snapshots cannot replace a newer watchlist. Conditions are human review instructions; the software does not interpret arbitrary condition prose. Reassessment and calendar reminders run when you invoke the CLI. No background service, email or automatic monitoring is installed. `status --as-of` filters current watch rows and recorded changes/events by that time; it does not reconstruct past watch configuration.

`approve_plan` is only a recorded human choice for a non-mock Trade Ready card. It never places an order. Profit/loss review requires a signed realized R after costs, with review time >= snapshot research time. Unknown and no-trade outcomes have no fabricated return.

## Constrained position calculation

`python -m bshl size --card CARD_JSON --account ACCOUNT_JSON --output outputs/sizing.json`

Account JSON: explicit `currency` matching the asset, `single_position_size`, `sector_concentration`, `total_exposure` (fractions including existing holdings), `leverage_ratio`, `correlation_risk` and `liquidity_risk` (0–10 judgment scores), `total_capital`. Optional `current_position_size` is an amount consistent with the fraction; `risk_budget_fraction` defaults to 0.01; optional `liquidity_capital_limit` is an amount. Stop distance comes from the card. Allocation is bounded by loss budget, total/sector/single exposure, existing position and liquidity. Only non-mock Trade Ready has a positive permitted research increment. Currency conversion, gap-loss guarantees and live executions are absent.

## Candidates and recovery

Use `backtest --compare-config candidate.json` with fixed split dates to compare mechanics under two configurations. Reports retain both complete results. This comparison does not run historical Alpha or prove an edge.

`journal propose --proposal proposal.json` accepts `rule_id` in `research.` or `structure.`, a `comparison` object and existing `review_ids`. Hard-risk namespaces are rejected; proposals cannot change runtime gates. Unique decisions are counted from the journal, not supplied sample claims. Fewer than 30 are marked insufficient; 30 is a reporting floor, not statistical certification. Comparison claims remain user-supplied. `journal candidate-review --id ID --choice approve_for_holdout --at OFFSET_DATETIME --note RATIONALE` records human approval for new holdout evaluation, not production deployment.

Export keeps all records, hashes and references. Restore validates format, checksums, snapshot identity, relationships and decision/outcome gates, then publishes a complete database exclusively at a **new** path. It refuses to overwrite an existing journal. Preserve private exports yourself; SQLite is not encryption. Restore requires same-volume hard-link support (NTFS and normal CI filesystems). There is no automatic migration from the old `~/.bshl` personal store.

## Revalidation and historical recovery (0.9.1)

New plan approval revalidates the current card rules, the four-calendar-day market freshness limit and supporting evidence at the approval time. Expired support or a newly available kill switch requires reassessment; an old Trade Ready label cannot substitute for new research.

Recovery recomputes candidate sample counts from referenced decisions, rejects approvals predating their reviews, and compares recorded change reasons/times with the original cards. Calendar sources cannot embed login credentials. Resealing an export checksum does not bypass these domain checks.

Older valid journal history can be restored without rewriting its snapshots. Older/unknown Trade Ready cards must be regenerated with current rules before new approval, sizing or current-card import. Historical restoration is archival preservation, not current permission. Keep the original export and verify restored records; no overwrite or automatic conversion is performed.

Existing immutable databases created by 0.9.0 remain readable. The core strategy assumptions and hard thresholds are unchanged. New latest-bar fields change card identities under readiness-0.6.4; use new output folders and preserve old exports.
