# Skill source audit

Audit date: **2026-07-15**

## Executive decision

Do not install any reviewed repository wholesale. The strongest result is a
small team-owned composition: three front doors, eight general engineering
primitives, and two narrowly triggered UI profile skills. Community sources remain pinned
provenance and research inputs; they are not allowed to update active behavior
automatically.

| Pack layer | Included skills |
| --- | --- |
| Front doors | `develop`, `finish`, `learn` |
| Engineering primitives | `shape-change`, `plan-change`, `implement-slice`, `diagnose-failure`, `review-change`, `simplify-change`, `security-review`, `handoff-and-teach` |
| UI profile | `ui-quality`, `review-web-motion` |

This gives developers memorable named workflows while retaining precise
automatic triggers for specialist work. The active implementations are under
`.agents/skills/`; the source-to-skill mapping is in
`.ai/skills-catalog.json`.

## Method

The audit used the author-owned repository at an exact commit, not an
aggregator's rendered copy. For each candidate it reviewed:

- purpose and positive/negative trigger;
- overlap and contradictory guidance;
- factual and version correctness;
- procedure, deterministic evidence, and runtime verification;
- mutation, network, credential, prompt-injection, and authorization risk;
- portability across Agent Skills, Claude, Codex, and Copilot;
- license, update mechanism, test/evaluation evidence, and maintenance cost.

Status terms:

- **Absorb** — retain the useful procedure in a team-owned skill.
- **Profile** — useful only when the repository has the named stack or need.
- **Experimental** — unique value, but safety or behavior evidence is not ready.
- **Contributor** — useful for maintainers of this kit, not product repositories.
- **Reject raw** — do not place the upstream package in an active skill path.

## Source-level findings

| Source | Reviewed commit | Overall decision |
| --- | --- | --- |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | `e9fcdf95b402d360f90f1db8d776d5dd450f9234` | Highest general engineering signal; absorb the diagnosis, modeling, spec, ticket, TDD, review, research, grilling, and handoff ideas |
| [Addy Osmani agent-skills](https://github.com/addyosmani/agent-skills) | `98967c45a42b88d6b8fb3a88b7ff6273920763d6` | Strong breadth and the best evaluation infrastructure; absorb selected spec, incremental, source-driven, API, simplify, security, ADR, and observability practices |
| [Emil Kowalski skills](https://github.com/emilkowalski/skills) | `6bf24434f7730ad169077756cf9c7cd7bd675fc6` | Good motion expertise; consolidate rather than installing overlapping motion skills |
| [Jakub Krehel skills](https://github.com/jakubkrehel/skills) | `f8a1574b08319685705a82e3c28139d1c935af9e` | Useful UI and typography heuristics; correct absolutes and color facts, then absorb |
| [David Ondřej skills](https://github.com/davidondrej/skills) | `d88deb06d2d16770833d148207fffaf33033e6e7` | A personal toolbox, not a safe team baseline; retain a few handoff, research, authoring, folder-guidance, and goal-loop concepts |
| [Dhruv's ten-skill X shortlist](https://x.com/dhruvtwt_/status/2077068765150453905?s=20) | Post dated 2026-07-14 | Valuable discovery list, not quality evidence; only adapted accessibility/UI/motion concepts enter the default pack |

All five named GitHub collections were MIT-licensed at the reviewed commits.
The active pack is rewritten and consolidated because installing every source
would create conflicting triggers and policy.

## Matt Pocock collection

Matt's active engineering/productivity skills contain the best reusable
workflow skeletons. They still need team authorization rules: `implement` and
merge-conflict flows can commit automatically, setup is personal, and several
skills overlap.

| Upstream skill | Decision | Destination or reason |
| --- | --- | --- |
| `ask-matt` | Reject raw | Persona-specific, not an organization capability |
| `code-review` | Absorb | `review-change`; require bounded diff, evidence, severity, and no invented findings |
| `codebase-design` | Experimental | Interesting architecture lens, but subjective and broad |
| `diagnosing-bugs` | Absorb | `diagnose-failure`; strongest distinctive procedure in the collection |
| `domain-modeling` | Absorb | Domain language and scenarios in `shape-change` |
| `grill-with-docs` | Merge | One-question-at-a-time requirements interview in `shape-change` |
| `implement` | Reject raw | Auto-commit and scope assumptions violate the shared authority boundary |
| `improve-codebase-architecture` | Experimental | Broad, high-blast-radius, and overlaps design/review |
| `prototype` | Profile | Useful for one bounded uncertainty, not routine delivery |
| `research` | Absorb | Primary-source/version checks in shaping and implementation |
| `resolving-merge-conflicts` | Reject raw | “Never abort” and automatic commit are unsafe defaults |
| `setup-matt-pocock-skills` | Reject | Personal installer, not product workflow |
| `tdd` | Absorb | Test-at-behavioral-seam guidance in `implement-slice` |
| `to-spec` | Absorb | `shape-change` and the feature spec template |
| `to-tickets` | Absorb | Tracer-first vertical slices in `plan-change` |
| `triage` | Profile | Useful for queue operations only when a tracker policy exists |
| `wayfinder` | Experimental | Potential orientation value; not enough distinct measured benefit yet |
| `grill-me` | Merge | Same requirements-interview purpose as `grill-with-docs` |
| `grilling` | Absorb | Focused challenge and one material question at a time |
| `handoff` | Absorb | Redacted, state-aware `handoff-and-teach` |
| `teach` | Merge | Teaching mode in `handoff-and-teach`/`learn` |
| `writing-great-skills` | Contributor | Useful to kit maintainers; not a runtime project skill |

Deprecated, in-progress, misc, and personal folders are not baseline
candidates. They can be reconsidered only when promoted upstream and a local
problem requires them.

## Addy Osmani collection

This repository has the most mature structural checks: the reviewed snapshot
had consistent package structure and a broad routing test suite. Its lexical
trigger evaluation is useful regression evidence, not proof of real task
quality. Several skills are large umbrellas or duplicate stronger specialists.

| Upstream skill | Decision | Destination or reason |
| --- | --- | --- |
| `api-and-interface-design` | Absorb | Compatibility and contract checks in shape/plan/review |
| `browser-testing-with-devtools` | Profile | Enable only when browser inspection tooling and a test policy exist |
| `ci-cd-and-automation` | Profile | Repository-specific commands and deployment authority must dominate |
| `code-review-and-quality` | Merge | `review-change` |
| `code-simplification` | Absorb | `simplify-change`, bounded to verified changed code |
| `context-engineering` | Contributor | Helps kit/workflow authors, not ordinary feature delivery |
| `debugging-and-error-recovery` | Merge | `diagnose-failure` |
| `deprecation-and-migration` | Profile | Valuable for compatibility-sensitive projects |
| `documentation-and-adrs` | Absorb | Consequential docs and ADR gate in `finish` |
| `doubt-driven-development` | Merge | Falsifiable hypotheses and source verification already covered |
| `frontend-ui-engineering` | Reject raw | Overbroad mega-skill; selected UI ideas belong in `ui-quality` |
| `git-workflow-and-versioning` | Reject raw | Risky automatic Git behavior and organization-specific policy |
| `idea-refine` | Merge | Early outcome clarification in `shape-change` |
| `incremental-implementation` | Absorb | Thin vertical slices in `plan-change`/`implement-slice` |
| `interview-me` | Merge | Requirements interview in `shape-change` |
| `observability-and-instrumentation` | Absorb | Boundary evidence and missing-observability handling in diagnosis/review |
| `performance-optimization` | Profile | Require profiling and stack-specific budgets |
| `planning-and-task-breakdown` | Merge | `plan-change` |
| `security-and-hardening` | Absorb | `security-review` with human ownership for Tier 0 |
| `shipping-and-launch` | Profile | Needs explicit external-operation authority and local rollout policy |
| `source-driven-development` | Absorb | Installed-version and primary-source verification |
| `spec-driven-development` | Absorb | Spec gate, templates, and criteria mapping |
| `test-driven-development` | Merge | `implement-slice` |
| `using-agent-skills` | Contributor | Useful adoption material, not a runtime task skill |

## Emil Kowalski collection

Emil's work has strong motion judgment but six packages fragment one domain.
Hard numeric values and taste preferences should remain heuristics; motion
claims need a live preview, accessibility checks, and profiling.

| Upstream skill | Decision | Destination or reason |
| --- | --- | --- |
| `review-animations` | Absorb | Main basis for `review-web-motion` |
| `improve-animations` | Absorb | Implementation guidance consolidated into the same skill |
| `animation-vocabulary` | Reference-only | Useful teaching vocabulary, not a separate recurring workflow |
| `apple-design` | Experimental | Gesture-heavy Apple-style profile only |
| `find-animation-opportunities` | Merge | Motion opportunities are advisory inside UI/motion review |
| `emil-design-eng` | Reject raw | 679-line overlapping umbrella with a promotional no-op response |

Adaptations made in the active pack include reduced-motion and non-drag
alternatives, interruption and pointer cancellation, real-device checks,
measured performance, and advisory treatment of taste.

## Jakub Krehel collection

| Upstream skill | Decision | Destination or reason |
| --- | --- | --- |
| `better-typography` | Absorb | Typography checks in `ui-quality`; project tokens/fonts come first |
| `better-ui` | Absorb | Hierarchy, states, interaction, and responsive checks in `ui-quality` |
| `better-colors` | Reject raw | Useful ideas, but factual and conformance claims need correction |

Corrections include: Tailwind's default palettes have eleven steps rather than
nine; Display P3's area is not safely summarized as “about 50% larger”; WCAG
2.2 remains the current conformance basis while APCA is supplemental; color
conversion and gamut/contrast claims must come from deterministic tools; dark
mode is not a reversed light palette. Global font smoothing, font synthesis,
heading count, exact easing, scale, radius, and shadow values are contextual.

## David Ondřej collection

David's repository is a useful view into one developer's personal environment,
but many skills assume specific tools, accounts, terminals, paid services, or
high-impact operations. That makes the collection unsuitable as a shared
install.

| Upstream skill | Decision | Reason or destination |
| --- | --- | --- |
| `agent-self-scheduling` | Reject raw | External scheduling and persistence need platform policy |
| `cmux` | Reject | Environment-specific terminal orchestration |
| `codex-subagent` | Reject raw | Vendor-specific orchestration belongs in an adapter |
| `delegating-to-agents` | Reject raw | Generic runtime behavior, not a portable project skill |
| `fable-safe-prompt` | Reject | Safety-bypass framing is incompatible with team policy |
| `goal-loop` | Experimental | Potential bounded execution loop; needs stop/authority evaluations |
| `handoff` | Absorb | `handoff-and-teach` |
| `launch-subagent` | Reject raw | Vendor/runtime-specific |
| `run-deep-swe` | Reject raw | External service and broad mutation assumptions |
| `anti-sleep` | Reject | Machine-level side effect, unrelated to project guidance |
| `create-readonly-db-role` | Reject | Dangerous privilege assumptions, including `BYPASSRLS` concerns |
| `cyber-audit` | Reject raw | High-risk broad audit needs vetted tooling and security ownership |
| `global-agent-guardrails` | Reject raw | Global machine policy cannot be inferred from a project |
| `google-safe-browsing` | Profile at most | Requires service credentials and a concrete product use case |
| `pi-custom-model` | Reject | Personal runtime configuration |
| `setup-help` | Reject | Personal environment setup |
| `vps-server-management` | Reject raw | Consequential production operations |
| `browser-harness` | Reject raw | Can expose authenticated Chrome sessions |
| `deep-research` | Reject raw | Paid/external service dependency and broad routing |
| `deepapi` | Reject raw | Large self-updating API workflow with excessive scope |
| `online-shopping` | Reject | Consumer task, not developer baseline |
| `pi-web-search` | Reject | Runtime-specific search adapter |
| `research-prompt` | Absorb | Focused primary-source research pattern |
| `youtube-transcript` | Reject | Narrow external content utility |
| `distribute-skill-to-all-agents` | Reject | Multi-copy/symlink distribution creates drift |
| `effective-agent-skills` | Contributor | Useful authoring concepts for kit maintainers |
| `folder-specific-claude-and-agents-md` | Absorb | Closest-scope guidance rule in `AGENTS.md` |
| `push-skill-to-github` | Reject raw | Automatic publish/push exceeds normal authority |
| `brain-to-docs` | Profile at most | Documentation capture needs a defined destination and review |
| `level-up` | Reject | Vague purpose and result contract |
| `prompt-me` | Merge | One-question interview in `shape-change` |
| `read-all-adrs` | Merge | Relevant ADR inspection in planning/review, not always-on reading |
| `remind` | Reject | Automation belongs to the host platform, not this pack |
| `save-idea` | Profile at most | Requires a team-owned idea destination |
| `short` | Reject | Global style preference, not a task workflow |
| `teach` | Merge | `handoff-and-teach`/`learn` |

## The ten-skill X shortlist

The visible post listed, in order: `emil-design-eng`,
`make-interfaces-feel-better`, `12-principles-of-animation`,
`fixing-accessibility`, `shadcn`, `vercel-react-best-practices`,
`react-doctor`, `vitest`, `pnpm`, and `playwright-cli`.

| Candidate | Canonical source and reviewed commit | Decision |
| --- | --- | --- |
| `emil-design-eng` | [emilkowalski/skills](https://github.com/emilkowalski/skills) `6bf24434f7730ad169077756cf9c7cd7bd675fc6` | Reject raw; consolidate selected motion guidance |
| `make-interfaces-feel-better` | [jakubkrehel/skills](https://github.com/jakubkrehel/skills) `f8a1574b08319685705a82e3c28139d1c935af9e` | Do not install beside `better-ui`; absorb corrected ideas into `ui-quality` |
| `12-principles-of-animation` | [raphaelsalaja/skill](https://github.com/raphaelsalaja/skill) `dc9eef22f13635df77d9b9e67c82aa85d52a97b7` | Reject raw; misleading scope and conflicting hard-coded motion laws |
| `fixing-accessibility` | [ibelick/ui-skills](https://github.com/ibelick/ui-skills) `ce91b85952f76ec738242bcf8aefa8c68653592c` | Absorb after correcting its WCAG-compliance overclaim |
| `shadcn` | [shadcn-ui/ui](https://github.com/shadcn-ui/ui) `6a5e6da78cad8c501f6b30830af0bbb56ba48867` | Adapted project-local profile when `components.json` is present; strongest of the three React/UI tools |
| `vercel-react-best-practices` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) `f8a72b9603728bb92a217a879b7e62e43ad76c81` | Do not include raw; prune into an explicit, measured React performance review after licensing is clarified |
| `react-doctor` | [millionco/react-doctor](https://github.com/millionco/react-doctor) `5915a58231c3ba640d2d17e3c703511b8c9c2746` | Experimental tool pilot only after legal/privacy approval; never fetch its live playbook at runtime |
| `vitest` | [antfu/skills](https://github.com/antfu/skills) `a74f281a27dadc02397bc1a174b0f2c97531b6ae` | Reject raw; consider a small version-aware profile only for Vitest repositories |
| `pnpm` | [antfu/skills](https://github.com/antfu/skills) `a74f281a27dadc02397bc1a174b0f2c97531b6ae` | Reject raw; contains reversed filter semantics and mixed pnpm 10/11 behavior |
| `playwright-cli` | [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) `eee5a185c98e6b04d88f580d45a854e9692ab50b` | Experimental adapted capability, not default; pre-1.0 and security-sensitive |

### Important X-list details

- `12-principles-of-animation` does not actually operationalize Disney's twelve
  principles. It statically enforces universal timing, scale, spring, and
  stagger values, omits reduced-motion/runtime evidence, and conflicts with
  both Emil and Jakub.
- `fixing-accessibility` has a good minimal-fix boundary and useful common HTML
  checks, but a static checklist cannot establish WCAG conformance. The active
  `ui-quality` adaptation adds composite-widget nuance, keyboard/focus/runtime
  evidence, target and pointer behavior, reflow/zoom, forced colors, and an
  explicit no-certification statement.
- The Antfu `vitest` and `pnpm` packages are thousands of lines of generated,
  version-sensitive reference text. The Vitest material mixes stable and beta
  APIs. The pnpm material reverses official dependency/dependent ellipsis
  filter semantics and exposes destructive or publishing operations without a
  sufficient confirmation boundary.
- The official Playwright CLI skill has real value—stateful sessions, semantic
  snapshots, traces, and test attachment—but the reviewed `0.1.17` package pins
  an alpha Playwright build. An adaptation must use a pinned project dependency,
  isolated ephemeral profiles, untrusted-page rules, explicit authorization
  for authenticated/consequential actions, and sensitive-artifact handling.
- The official shadcn package has the clearest stack trigger and good CLI-backed
  inspection, dry-run, and diff procedures. Its adaptation must use the
  project's pinned/local CLI instead of `@latest`, remove vendor-only
  frontmatter and command substitution, allowlist registries, protect private
  registry tokens, and treat many “always/never” styling rules as detected
  project policy rather than correctness.
- Vercel's React corpus contains 70 prioritized rules and useful waterfall,
  bundle, server/client boundary, serialization, and rerender guidance. It is
  too broad for every React edit, includes version-sensitive and contradictory
  patterns, duplicates a 108 KB compiled document, and lacks behavioral proof.
  A smaller profile must detect React/Next/router/RSC/compiler versions and
  require profiler, bundle, or Web Vitals evidence. Redistribution is unresolved:
  files declare MIT, but the reviewed repository contains no license text.
- React Doctor's analyzer has substantial deterministic rule tests, but the
  wrapper is not safe as reviewed. It runs moving `@latest` code, enables
  external telemetry/supply-chain services by default, uses a coarse score,
  and fetches a mutable hosted playbook. At audit time that playbook had grown
  branch, commit, push, PR, and issue actions that contradicted the checked-in
  “no commit/PR” boundary. Its modified-MIT license also requires legal review
  for AI evaluation/training pipelines and some hosted uses. A pilot must pin a
  release and reviewed playbook, disable telemetry and supply-chain calls by
  default, gate only introduced errors, and keep external GitHub actions in a
  separately authorized workflow.

The UI Skills catalog is useful for discovery but should not be the vendoring
source: catalog pages can rewrite descriptions and omit fields. Pin the
author-owned repository instead.

## Compatibility evidence

The folder format follows the open [Agent Skills specification](https://agentskills.io/specification):
one directory per skill with `SKILL.md` and only portable `name` and
`description` frontmatter. Codex and GitHub Copilot discover `.agents/skills`;
Claude project skills conventionally use `.claude/skills`, while legacy
`.claude/commands` continue to work as explicit commands. The kit therefore
keeps one canonical `.agents` copy and uses small Claude command adapters.
Claude's documented memory import syntax lets `CLAUDE.md` import `@AGENTS.md`.

References:

- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude Code memory and imports](https://code.claude.com/docs/en/memory)
- [GitHub Copilot agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- [VS Code agent skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [`npx skills` installer](https://github.com/vercel-labs/skills)
- [`gh skill install` preview](https://cli.github.com/manual/gh_skill_install)
- [`gh skill update` preview](https://cli.github.com/manual/gh_skill_update)

## Follow-up candidates

Do not add another baseline skill until usage evidence identifies the missing
purpose. The most plausible opt-in pilots are:

1. a secure, pinned `playwright-cli-browser` capability;
2. a pinned, project-local `shadcn-ui` profile when shadcn is actually present;
3. a measured, version-aware React performance review after its license and
   rule corpus are corrected;
4. a React Doctor error-only pilot only after legal/privacy approval and removal
   of live instructions and default external calls;
5. a version-aware test-runner profile when a team standardizes on Vitest;
6. a pnpm repository-policy profile only after pinning pnpm 11+ and verifying
   all command semantics;
7. a bounded architecture or goal-loop experiment with explicit stop
   conditions.

Each pilot must pass the rubric and evaluation requirements before moving into
an active discovery directory.
