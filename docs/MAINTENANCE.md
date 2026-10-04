# Maintenance and real feedback

## Current verification

- Local: deterministic/domain/schema/CLI/journal/adapter tests, frozen-example checks and clean-wheel smoke installation.
- CI: Windows/Linux/macOS, Python 3.10/3.13, tests, local document/image links, exact fixture regeneration and wheel installation.
- Live providers, broker execution and investment effectiveness: unverified and outside this release.
- Agent host loading: skill format validation is not an end-to-end model test; verify the target host separately.

Before release, use [the release procedure](../GITHUB_RELEASE.md). The [roadmap](../VERSION_ROADMAP.md) is the maintained batch status. Preserve historical documents as labelled archives, not capability evidence.

## Failure sample specification

A useful case includes market/exchange, data mode, provenance/license, rule version, decision time, input availability, expected state/blocker and the minimal command. Keep future outcome labels out of signal inputs. Add a regression that fails for the demonstrated bug, then refresh examples only after reviewing changed decisions.

To refresh maintained public fixtures: `python scripts/regenerate_examples.py`, inspect the diff, then `python scripts/validate_examples.py`. Old output folders are intentionally not overwritten by ordinary CLI commands; select a new folder after a rule update.

## Feedback

Collect actual first-run failures, time to first valid output, repeat usage and contributed failure samples from voluntary issues. Do not add hidden telemetry or fabricate testimonials. Report counts with date, sample and collection method. Stars are visibility signals, not strategy validation. Small samples remain insufficient evidence even when mechanically correct.
