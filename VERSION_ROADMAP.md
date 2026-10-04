# Six-batch implementation roadmap

This is the single maintained capability/status roadmap. Version milestones are acceptance labels, not claims of profitability.

| Batch | Deliverable | Acceptance | Status |
|---|---|---|---|
| 1 / 0.5.1 | Imports, strict risk/numeric gates, schemas, persistence, truthful documentation | Regression tests; unknown checks cannot Pass; no stop cannot be ready | Accepted — original 56-case integrity milestone |
| 2 / 0.6 | Provenance-aware CSV, closed bars, deterministic structure | Repeatable output; no future-bar repainting; explicit mock data | Accepted — CSV, structure, card CLI and schema gates |
| 3 / 0.7 | Event replay, exits, costs, equity and baseline | No future outcome leakage; repeat runs match; holdout separation | Accepted — cash mechanics and fixed splits; performance unvalidated |
| 4 / 0.8 | Watchlists, snapshots, review and candidate rules | Save/reload/review round trip; immutable original decision | Accepted — immutable journal, sizing, comparison and recovery |
| 5 / 0.9 | Offline demo, bilingual landing, share card and Release | Documented demo reproduces; published release matches tested commit | Demo/cards/docs accepted; [v0.9.1 prerelease](https://github.com/Sunnyeung369/BSHL_Alpha_Skill/releases/tag/v0.9.1); cover upload still pending |
| 6 / 0.9 | Failure/adapter contribution templates and ongoing checks | Contribution fixtures validated; no invented feedback | Accepted — 147 tests, issue forms, adapter boundary, golden fixtures and clean-wheel CI |

Verification: 147 local tests, strict public fixture comparison, skill metadata validation and clean-wheel install. The implementation passes Windows/Linux/macOS CI on Python 3.10/3.13. [Current workflow runs](https://github.com/Sunnyeung369/BSHL_Alpha_Skill/actions/workflows/ci.yml) identify the checked commit. Accurate Topics are configured, and focused [good first issues](https://github.com/Sunnyeung369/BSHL_Alpha_Skill/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22) are open.

Remaining repository setup: the [Social Preview asset](assets/social-preview.png) is delivered and visually checked, but its Settings upload is unverified because the desktop browser's settings page/control read failed. This is a distinct unfinished item in batch 5; the six code/document milestones do not imply that setting succeeded.

First market target: explicit daily US equity/ETF profiles. Other assets require their own calendars, lot sizes, cost and data semantics. Real-time trading, autonomous execution and universal multi-market performance are outside the verified scope.

The [0.9.1 deep audit](docs/AUDIT_2026-10-04.md) records corrections missed by initial milestone checks and remaining validation boundaries.
