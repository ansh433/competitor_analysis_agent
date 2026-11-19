# Security

## Tenant isolation

Every workspace, conversation, company, run, evidence, comparison, and tracking lookup is filtered by authenticated user ID or joined through a resource owned by that user. Non-owned identifiers return 404 to avoid confirming their existence. Tool runtime identity is explicit.

## Authentication and secrets

Passwords use Argon2 through `pwdlib`. Access and reset JWTs have distinct purposes and expirations. Recovery responses do not reveal whether an email exists. No default administrator password exists. `.env`, authorization headers, provider keys, and passwords are excluded from version control and logs.

Gemini key rotation stores key values only in typed settings and passes them to provider clients. Errors and operational messages expose safe labels/task names and attempted-key counts, never key material. Provider retries are disabled so the application controls the retry budget.

## Web retrieval

Only HTTP and HTTPS URLs without embedded credentials are allowed. The fetcher rejects localhost, internal suffixes, nonstandard ports, and every resolved address that is not globally routable. Redirects are revalidated, response time and byte size are bounded, and only supported text content types are extracted. DNS validation and connection resolution remain separate operations; deployments with hostile DNS requirements should add network-level egress controls or a pinned outbound proxy.

Retrieved markup is reduced to text, delimited as untrusted evidence, and never appended to the system prompt as instructions.

## Browser and transport

CORS uses the configured allowlist. SSE payloads are validated Pydantic objects before Protobuf encoding. Markdown raw HTML is disabled, external links use safe protocols, and citation details are loaded through authenticated APIs.

Optional Sentry and SMTP integrations activate only when configured. Sentry events must be reviewed for organizational data-retention requirements before production enablement.

