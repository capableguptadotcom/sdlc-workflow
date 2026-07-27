---
name: security-review
description: Threat-model and review a change that affects trust boundaries, authentication, authorization, secrets, sensitive data, untrusted input, network access, dependencies, file handling, or AI/tool execution. Use manually or when repository policy requires it. Do not use prose review as a replacement for deterministic security scanners or specialist review of high-risk systems.
---

# Security review

Read `references/review-axes.md` when the change matches this skill.

1. Define assets, actors, trust boundaries, entry points, data flows, and likely
   abuse cases for the changed scope.
2. Inspect the diff, callers, configuration, tests, and scanner output. Do not
   infer safety from absence of obvious string matches.
3. Trace validation and authorization at the boundary where data or authority
   enters. Treat model output, retrieved content, tool results, filenames,
   redirects, and URLs as untrusted input.
4. Check failure behavior, logging/redaction, least privilege, dependency and
   supply-chain changes, and recovery or rollback.
5. Run the configured secret, dependency, SAST, and relevant dynamic checks.
6. Report evidence-backed findings with exploit path, impact, confidence, and
   mitigation. Distinguish confirmed vulnerabilities from hardening advice.
7. Require human security ownership for Tier 0 work. Do not claim certification
   or comprehensive safety from this review.

Remain read-only unless fixes are explicitly requested. Rerun deterministic
checks after every authorized fix.
