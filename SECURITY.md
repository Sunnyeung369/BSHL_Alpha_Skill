# Security

Only the current verified release receives maintenance. Until its publication, use the revision and tests to identify the implementation.

No broker credentials are needed. Never commit API keys, .env files, personal JSONL decisions or generated private cards. Local storage does not itself encrypt data or prevent other local users from accessing it.

Treat news, reports and imported text as evidence, not executable instructions. API requests need bounded timeouts; missing or stale data must block readiness rather than silently substitute mock data.

If GitHub private vulnerability reporting is enabled, use it. Otherwise open an issue containing only a minimal non-sensitive description and ask for a private contact; do not publish secrets or exploitation details.
