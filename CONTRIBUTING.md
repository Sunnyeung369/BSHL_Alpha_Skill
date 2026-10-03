# Contributing

Run `python -m unittest discover -s tests -v` and `python scripts/check_repository.py` before submitting. Install the optional dev dependencies in an isolated environment for Schema contract tests.

Contributions need a reproducible input, expected behavior, decision time and the relevant market/data mode. Include failure cases; never submit account credentials, personal decisions or licensed datasets without permission.

For a rule: define the formula, availability time, confirmation delay, invalidation, parameter bounds and tests. A passing implementation test does not establish a trading edge. Keep decision inputs separate from outcome labels.

For an adapter: document provenance, timestamps, adjustment, session, timeouts and failure behavior. Mock responses must be explicit. Add provider fixtures rather than making CI depend on live credentials.

See [roadmap](VERSION_ROADMAP.md) for accepted scope. Ordinary rule adjustments need review; hard risk gates cannot be automatically disabled.
