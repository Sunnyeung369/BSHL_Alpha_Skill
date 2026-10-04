# Daily snapshot adapter contract

`MarketDataAdapter.snapshot(symbol, as_of) -> Dataset` is the provider boundary in [adapters.py](../bshl/adapters.py). `CSVSnapshotAdapter` is implemented. `validated_snapshot` checks requested identity, provenance, explicit mock opt-in and point-in-time visibility. A provider failure propagates; there is no mock fallback.

No authenticated network adapter is bundled. The legacy Yahoo/AlphaVantage/SEC/Crypto/news classes are placeholders. A name or Protocol does not establish a working API.

## Adding a provider

Implement a returned immutable Dataset under [the CSV/domain contract](DATA_CONTRACT.md). Supply exchange, timezone, source, adjustment, retrieval, availability, completed bars and declared sessions. Live API calls need explicit credentials, bounded timeout/retry and rate-limit/auth handling. Never log keys or silently change the symbol/mode. Do not infer an exchange calendar from weekdays.

Submit frozen, licensed fixtures for valid data and failures: identity mismatch, missing/provisional bars, stale snapshot, invalid OHLCV, timeout, permission denial, rate limit and delayed publication. Unit tests must run without credentials or internet. An authenticated live verification, with its date and scope, is a separate acceptance step.

New execution markets require their own currency, lot size, session, suspension/price-limit, cost and corporate-action semantics. Extending human research instructions does not extend the executable market profile.
