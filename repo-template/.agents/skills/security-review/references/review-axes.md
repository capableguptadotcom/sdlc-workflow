# Security review axes

Load only the sections relevant to the changed boundary.

## Identity and authority

- Authentication state, session lifecycle, impersonation, recovery, and token
  handling.
- Authorization on every object and action; tenant isolation; deny-by-default
  behavior.
- Privilege changes, service identities, and least-privilege permissions.

## Input and execution

- Injection into SQL, shells, templates, logs, headers, paths, and agent tools.
- SSRF, redirects, DNS rebinding, URL allowlists, egress controls, and response
  size/time limits.
- Upload type, size, storage path, parsing, decompression, and malware handling.
- Prompt injection and confused-deputy paths across retrieved or tool-provided
  content.

## Data and secrets

- Collection minimization, encryption, retention, redaction, and deletion.
- Secret storage, rotation, accidental logs, client exposure, and CI handling.
- Multi-tenant queries, row-level policy, exports, backups, and analytics.

## Supply chain and operations

- New packages, install scripts, lockfile changes, provenance, and advisories.
- Safe defaults, rate limits, resource exhaustion, alerting, incident evidence,
  and rollback.

Use OWASP or stack-specific primary guidance as a reference, but judge the
actual repository and deployed boundary rather than applying a generic list.
