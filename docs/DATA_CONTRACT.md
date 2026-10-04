# Daily CSV and research context

## Required inputs

CSV headers, in order: `timestamp,open,high,low,close,volume,available_at,is_closed` with optional final `session_open`.
`timestamp` means session close; `available_at` means complete record availability. Both use ISO datetimes with explicit offsets. `is_closed` is literal `true`/`false`. Prices must be positive, volume nonnegative and OHLC coherent. Duplicate or unsorted closes fail; missing values are not filled.

Metadata fields: `symbol`, `market`, `timeframe` (`1d`), `currency`, IANA `timezone`, `adjustment` (`unadjusted`, `split_adjusted`, `total_return`), HTTP(S) `source_url`, `data_mode` (`csv`/`mock`), `is_mock`, `asset_type`, `retrieved_at`. Optional `session_dates` is the sorted provider-declared exchange calendar. For simulation, supply unadjusted US/USD stock or ETF data and an explicit `session_open` for every bar, or metadata `session_open_times` keyed by declared date. A weekday list is not a verified exchange calendar.

Use the bundled [metadata](../bshl/assets/breakout.metadata.json) and [context](../bshl/assets/demo.context.json) for field shape only. They are fictional fixtures.

## Context and evidence

Alpha and pricing scores are human-supplied research judgments, not inferred financial facts. Each supplied score object must contain exactly its scorer's public keys. A missing layer stays unknown. A historical context must represent information known at that decision time; the engine cannot authenticate a human's score history.

`risk_checks` accepts the ten named boolean-or-null gates. Missing gates cannot Pass. Supply a chosen `stop_loss_price` and `target_price`; suggested structural stops are not adopted automatically. Ready requires reward/risk >= 2, trade points >= 85 and all gates. Measured overheat, ATR > 5% or stop distance > 10% tighten manual checks. These are experimental limits, not calibrated risk estimates.

Evidence needs a claim, HTTP(S) source URL, `published_at`, `available_at`, `source_type`, `evidence_strength`, and `supports_or_refutes`. Strong supporting sources are filing, transcript, company_release or industry_report. An available `kill_switch: true` vetoes the thesis. Optional `expires_at` removes stale support. Future and expired evidence stays in the audit record but cannot support or veto the decision. Source authenticity is user-supplied and not independently verified.

## Deterministic structure

Daily MA20/50, Wilder ATR14, strict pivots with two bars on each side. Pivot confirmation needs the right bars already available. Breakout: closed close above last confirmed resistance + 0.1%, prior close <= resistance, volume >= 1.3 times prior 20 bars, sufficient history and completed parent-week UP direction. Pullback checks the last five bars and a 0.5 ATR tolerance. Overheat is > 3 ATR above MA20.

Parent weeks require all declared sessions and coverage beyond the week boundary. Missing calendar blocks parent confirmation. Rules do not invent exchange holidays. The result describes this ruleset; it is not a universal definition of technical analysis.

## Output

[Research-card schema](../schemas/research_card.schema.json) documents the JSON. `analysis_id` hashes visible inputs, provenance, context and rule version. Repeated identical inputs yield identical cards. Future bar values cannot change an earlier card; changing metadata or stored context creates a different audit identity even if the decision stays the same. Output refuses to overwrite a different card.
