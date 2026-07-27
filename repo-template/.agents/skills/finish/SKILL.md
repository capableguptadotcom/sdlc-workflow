---
name: finish
description: Prepare an existing code diff for human review by running deterministic verification, reviewing against the specification and standards, simplifying safely, and recording evidence. Use when implementation is substantially complete or the user explicitly invokes finish. Do not use to invent missing requirements or to approve unverified work.
---

# Finish

Prepare the change; do not merely polish its presentation.

1. Establish the intended diff and exclude unrelated user changes.
2. Read the applicable specification, plan, `AGENTS.md`, and configured commands.
3. Run deterministic checks first. If they fail, stop review-oriented polishing
   and report or diagnose the failure.
4. Follow `../review-change/SKILL.md` against the verified diff.
5. Resolve blocking correctness findings when authorized, then rerun checks.
6. Follow `../simplify-change/SKILL.md` only after correctness passes.
7. Trigger `security-review`, `ui-quality`, or `review-web-motion` only when the
   change actually matches those scopes.
8. Update verification evidence and consequential documentation. Create an ADR
   only for a durable, surprising, or hard-to-reverse decision.
9. Rerun affected checks after every edit.

Return a concise readiness verdict: `ready`, `ready-with-advisories`, or
`not-ready`, with commands, evidence, blockers, and limitations.
