# Release procedure

A Markdown file is not a published GitHub Release. Publish only after the intended commit passes local verification and the applicable CI jobs.

1. Update package version, capability table, roadmap and changelog together.
2. Run unit/integration/schema tests and repository checks.
3. Generate the documented demo with explicit data provenance.
4. Tag the verified commit and create a Release describing actual behavior, tests and remaining limits.
5. Verify the public tag, source commit and download contents.

See [roadmap](VERSION_ROADMAP.md) for the six-batch implementation. Historical v0.5 notes are not current readiness evidence.
