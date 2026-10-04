# Six-batch implementation roadmap

This is the single maintained capability/status roadmap. Version milestones are acceptance labels, not claims of profitability.

| Batch | Deliverable | Acceptance | Status |
|---|---|---|---|
| 1 / 0.5.1 | Imports, strict risk/numeric gates, schemas, persistence, truthful documentation | Regression tests; unknown checks cannot Pass; no stop cannot be ready | Locally verified: 56 tests |
| 2 / 0.6 | Provenance-aware CSV, closed bars, deterministic structure | Repeatable output; no future-bar repainting; explicit mock data | Locally verified: 27 additional tests; CSV CLI and schema gates |
| 3 / 0.7 | Event replay, exits, costs, equity and baseline | No future outcome leakage; repeat runs match; holdout separation | Locally verified: 18 simulation/CLI tests; performance remains unvalidated |
| 4 / 0.8 | Watchlists, snapshots, review and candidate rules | Save/reload/review round trip; immutable original decision | Locally verified: 15 journal/sizing/comparison tests |
| 5 / 0.9 | Offline demo, bilingual landing, share card and Release | Documented demo reproduces; published release matches tested commit | Local demo/cards/docs accepted; GitHub publication is the final acceptance step |
| 6 / 0.9 | Failure/adapter contribution templates and ongoing checks | Contribution fixtures validated; no invented feedback | Planned |

First market target: explicit daily US equity/ETF profiles. Other assets require their own calendars, lot sizes, cost and data semantics. Real-time trading, autonomous execution and universal multi-market performance are outside the verified scope.
