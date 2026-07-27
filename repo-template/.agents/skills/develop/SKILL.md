---
name: develop
description: Orchestrate normal-language repository work from orientation or intent through verified implementation and finish. Use when the user asks for a repository explanation or to build, change, or fix behavior end to end, including a clear small change, unclear intent, an unknown implementation approach, or a large initiative. Do not use for review-only, learning-only, production operations, or cause-only diagnosis.
---

# Develop

Own workflow selection so the developer does not need specialist names.

## Start with evidence

Read `AGENTS.md`, `ai-sdlc.yaml`, `.ai/ARTIFACTS.md`, relevant code and tests,
existing specs, configured context, and relevant ADRs. Obtain repository facts
by inspection. Announce the selected mode in plain language.

## Choose the lightest reliable route

1. For a clear, local, reversible, low-risk change, use an inline change brief.
   Follow `../implement-slice/SKILL.md`, then run an adaptive `finish`. Do not
   create a feature folder.
2. For a reported failure with an unknown cause, follow
   `../diagnose-failure/SKILL.md`. Stop after the cause for diagnosis-only
   requests. Continue to a regression test and causal fix only when requested.
3. When observable behavior, policy, terminology, scope, or acceptance is
   unclear, follow `../shape-change/SKILL.md`.
4. When the outcome is coherent but the implementation approach is unknown,
   inspect first and own routine reversible engineering choices. Let
   `shape-change` resolve only the remaining product, empirical, external, or
   durable trade-off uncertainty.
5. When discovery contains multiple coordinated outcomes or decision tracks
   that cannot remain one coherent spec or session, propose initiative mapping.
   Continue only after confirmation and read
   [initiative-mapping.md](references/initiative-mapping.md).
6. Create a technical plan only when multiple dependency-ordered slices,
   migration, compatibility, rollout, or material risk warrants it. Otherwise
   implement directly from the accepted spec.
7. Follow `../implement-slice/SKILL.md` for one accepted slice at a time, then
   follow `../finish/SKILL.md`.

For explanation-only requests, inspect and answer without creating artifacts or
entering an implementation route.

Risk can make a route stricter, but confidence cannot make it looser.
Authentication, billing, sensitive data, destructive migrations, and
domain-critical rules retain configured human gates.

## Stop and return

Stop at a human decision boundary, failed invariant, contradiction with an
active ADR, or material scope change. Return to shaping when implementation
changes accepted behavior. Do not silently redesign an accepted artifact.

## Completion contract

Return:

- behavior delivered;
- specification and criteria addressed;
- deterministic commands and results;
- files changed;
- unresolved decisions, risks, and next slice.

Do not commit, push, deploy, publish, or mutate an external tracker unless the
user explicitly asks.
