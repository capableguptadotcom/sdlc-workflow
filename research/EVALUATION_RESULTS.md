# Initial evaluation results

Evaluation date: **2026-07-15**

These are release-candidate checks for the team-owned pack, not claims that the
skills are universally reliable. Projects must rerun the included cases in each
supported agent during adoption.

## Structural and coverage validation

Command:

```bash
python repo-template/scripts/validate_ai_kit.py
```

Result:

```text
WARNING: ai-sdlc.yaml still contains empty command lists; complete adoption
Validated 13 skills, 26 routing cases, and 13 behavior cases.
```

The warning is intentional in the shared template because each project must
provide its own commands. `--strict` turns it into a failure after adoption.

The validator checks portable frontmatter, canonical/adaptor parity, catalog
and provenance references, exact routing coverage, behavior-case coverage, and
the shared-instruction pointers.

## Blind routing test

An independent agent received only the 13 canonical skill descriptions and 13
unlabeled prompts—one clear case per skill. It was explicitly prevented from
opening the expected-answer file.

Result: **13/13 primary routes matched**.

The agent noted two legitimate near-neighbor relationships but selected the
narrower intended skill:

- `learn` rather than `handoff-and-teach` for a deliberate teaching detour;
- `review-web-motion` rather than `ui-quality` for a draggable transition.

This is a promising first pass, not a production routing rate. The full
`evals/routing-cases.json` also contains negative cases and must be executed by
the actual supported runtimes.

## Diagnosis behavior test

Fixture: a cache stores numeric `0`, but a truthiness-based hit test reloads it.
Request: determine the failure's root cause and do not fix or modify anything.

Observed result:

- reproduced the failing assertion with a smaller equivalent runner;
- observed the cache boundary and compared a truthy control value;
- identified the causal chain rather than only the assertion line;
- reported high confidence and no unresolved credible alternative;
- made no source edit or fix.

The test exposed two instruction gaps. Test runners can create caches and other
artifacts even in “read-only” work, and “instrument one variable” could be read
as permission to edit. `diagnose-failure` was changed to prefer ephemeral
observation, suppress or disclose incidental artifacts, and allow an equivalent
narrow runner only when it preserves relevant setup and the failing assertion.

## UI behavior test

Fixture: a static settings page with a clickable `div`, unlabeled email input,
low-contrast text, missing document language/title, and a possibly dynamic
status container. Request: review without editing; no preview was available.

Observed result:

- found the native-control, label, measured contrast, language, and title
  issues with exact locations;
- kept the status announcement conditional on actual runtime use;
- did not invent a replacement color without design tokens;
- separated confirmed findings from checks unavailable without CSS, JavaScript,
  a preview, or assistive technology;
- explicitly declined to claim WCAG conformance;
- made no edit.

The test exposed mode and output ambiguity. `ui-quality` was changed to branch
between read-only review and authorized improvement; label source-only claims;
avoid runtime/visual conclusions without a preview; use repository tooling
before adding dependencies; and return a consistent severity, evidence,
confidence, recommendation, verification, and verdict contract. Its reference
now links the applicable WCAG and ARIA primary guidance.

## Remaining release evidence

Before organization-wide rollout, run:

1. all positive and negative routing cases in Claude, Codex, and the selected
   Copilot surface;
2. behavior tasks on representative frontend, backend, legacy, and monorepo
   projects;
3. Windows/macOS/Linux adapter smoke tests where those platforms are supported;
4. prompt-injection and credential-artifact cases for browser/security skills;
5. a baseline comparison measuring missed findings, false findings, task time,
   and review acceptance—not only whether a skill triggered.

Record every confirmed failure as a durable regression case before changing a
description or procedure.
