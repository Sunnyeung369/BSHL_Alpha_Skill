# BSHL v0.9.1 — imported-card and recovery hardening

This prerelease closes demonstrated gaps found in a deeper audit of v0.9.0. It does not introduce a live provider or validated trading performance.

- Recompute imported scores, evidence and risk checks; reject conflicting mock labels, invalid sources, altered plan fields and stale readiness.
- Recheck freshness/evidence when recording human approval. Preserve the original decision and older journal history; require current research before new approval/sizing.
- Recompute restored candidate sample counts, approval chronology and change reasons. Reject calendar URLs with embedded credentials.
- Block missing or unavailable declared sessions in research history; reject missing internal daily bars in simulation without changing prior-cutoff results.
- Enforce account exposure containment and datetime domain types. Accept Windows BOM JSON and reject duplicate keys.
- Align seven active skill pages with executable gates; preserve old templates as historical archives.
- Remove hardcoded wheel versions and exercise the installed journal/recovery/share loop in CI.

Acceptance: 150 local tests, exact public card/schema/Markdown/SVG checks, skill validation, repository compilation/links and a clean wheel installation. Windows/Linux/macOS × Python 3.10/3.13 CI identifies the final checked commit. Rules: readiness-0.6.4; old release/tag/assets remain preserved.

Sources and context remain user-supplied; validation checks internal consistency, not authentic market truth. No broker, autonomous order execution, background monitor or proven edge. Social Preview PNG is delivered, but its Settings upload is still unfinished after another browser timeout.

[Detailed audit](AUDIT_2026-10-04.md) · [Prior release](RELEASE_v0.9.0.md)
