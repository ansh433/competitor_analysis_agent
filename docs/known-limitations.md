# Known limitations

- Tracked companies store preferences but do not yet run scheduled monitoring or automatically diff new evidence.
- Live-source quality depends on Tavily coverage and publicly accessible pages. Paywalls, robots policies, client-rendered sites, and authentication can leave explicit research gaps.
- Public enterprise and negotiated prices are reported as unavailable rather than estimated.
- The HTTP fetcher validates DNS before every request and redirect, but application-level validation cannot eliminate DNS rebinding as strongly as a pinned egress proxy or network firewall.
- Research execution uses an in-process worker thread and queue. Retryable provider failures are resumable from durable checkpoints, but automatic recovery after a whole-process or host crash still requires a durable job queue and stale-run recovery policy.
- The compiled browser bundle is currently large because Markdown, KaTeX, Protobuf, and the full research UI ship together. Route-level code splitting is a future performance improvement.
- Token storage uses browser local storage. A deployment with stricter XSS requirements should move access tokens to secure, same-site HTTP-only cookies and add CSRF protection.
- Browser E2E requires local port binding. It cannot run inside managed sandboxes that reject every listening socket.

