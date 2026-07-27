# Matt Pocock skills: current grilling and delivery flow

Research date: **2026-07-26**

Upstream examined: [`mattpocock/skills`](https://github.com/mattpocock/skills)
default branch at
[`ed37663cc5fbef691ddfecd080dff42f7e7e350d`](https://github.com/mattpocock/skills/commit/ed37663cc5fbef691ddfecd080dff42f7e7e350d).
The supplied AI Hero v1.1 page was used as the comparison baseline.

## Decision

Do **not** add raw copies of `grill-me` or `grill-with-docs` as additional
developer-facing commands. Their current upstream behavior should be derived
into the kit's existing `shape-change` primitive and selected automatically by
`develop`.

Keep `diagnose-failure` as the automatic route for reported defects. Debugging
is an evidence-gathering workflow, not a grilling session. Invoke
`shape-change` only if diagnosis exposes a genuine product, compatibility, or
architecture decision that the human must make.

Do not adopt the unreleased round-based grilling change yet. Test it against
the current one-question-at-a-time behavior before deciding whether it is more
comfortable for this team.

## What exists upstream now

| Upstream capability | Current location and invocation | Current role |
| --- | --- | --- |
| `grill-me` | [`skills/productivity/grill-me`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/productivity/grill-me/SKILL.md); user-invoked only | A two-line, stateless wrapper that runs `grilling`. It has **not** been removed or renamed. |
| `grill-with-docs` | [`skills/engineering/grill-with-docs`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/grill-with-docs/SKILL.md); user-invoked only | A thin wrapper that runs `grilling` together with `domain-modeling`, which maintains `CONTEXT.md` and offers sparse ADRs. It has **not** been replaced. The actual name is `grill-with-docs`, not `grill-me-with-docs`. |
| `grilling` | [`skills/productivity/grilling`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/productivity/grilling/SKILL.md); model-invoked | The reusable interview primitive: inspect facts, put decisions to the human, ask one question at a time with a recommendation, and stop before action until the human confirms shared understanding. |
| `wayfinder` | [`skills/engineering/wayfinder`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/wayfinder/SKILL.md); user-invoked only | A deliberately heavier planning on-ramp for an effort that is both foggy and larger than one agent session. Its issue map contains decision tickets, not implementation tickets. It uses grilling, domain modeling, research, and prototypes, then hands off to `to-spec`. |
| `diagnosing-bugs` | [`skills/engineering/diagnosing-bugs`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/diagnosing-bugs/SKILL.md); model-invoked | The defect route. It requires a tight, red-capable feedback loop before forming theories, then minimises, ranks falsifiable hypotheses, instruments, fixes, and regression-tests. It reads relevant context and ADRs but does not invoke `grill-with-docs`. |
| `ask-matt` | [`skills/engineering/ask-matt`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/ask-matt/SKILL.md); user-invoked only | A memory aid that tells a user which explicit skill to run. It performs no work itself. |

Upstream intentionally distinguishes user-invoked wrappers from model-invoked
primitives. Its Codex metadata sets `allow_implicit_invocation: false` for
`grill-me` and `grill-with-docs`, while `grilling` and `diagnosing-bugs` remain
implicitly reachable; the policy is documented in
[`invocation.md`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/.agents/invocation.md).
Therefore, copying the wrappers would reproduce the user's concern: developers
would still need to remember their names.

## What changed relative to the supplied v1.1 page

The page remains accurate about the v1.1 renames and the central ideas:

- `to-prd` became `to-spec`;
- `to-plan` and `to-issues` became `to-tickets`;
- grilling gained the facts-versus-decisions distinction and a confirmation
  gate;
- Wayfinder became the large, multi-session planning route.

The latest stable GitHub release is still
[`v1.1.0`](https://github.com/mattpocock/skills/releases/tag/v1.1.0), at commit
[`d574778`](https://github.com/mattpocock/skills/commit/d574778f94cf620fcc8ce741584093bc650a61d3).
Since that tag:

- the `grill-me` and `grill-with-docs` wrappers have not changed;
- `grilling` was generalized from “a plan or design” to any “plan, decision,
  or idea” in
  [`170ad48`](https://github.com/mattpocock/skills/commit/170ad48655825783d0193e850e31a9aac957bb95);
- Wayfinder now calls its units **decision tickets** and can dispatch research
  tickets to subagents in
  [`2602257`](https://github.com/mattpocock/skills/commit/260225724133c4a204489599f04642aa089259a0);
- local `to-tickets` output changed from one combined `tickets.md` to one file
  per ticket.

There is an important unreleased development. Draft
[`PR #593, Release v1.2`](https://github.com/mattpocock/skills/pull/593) changes
the `grilling` primitive from one question at a time to **frontier-sized
rounds**, folds the experimental `batch-grill-me` behavior into it, and deletes
that experiment. The PR is open and draft, and commit
[`b8fd9af`](https://github.com/mattpocock/skills/commit/b8fd9afa42a6eebcfdcfc5007c42ef2367911000)
is not contained in a release tag. This is likely the replacement the user
remembered: the wrappers remain, but their shared primitive is proposed to
change.

On the default branch, `batch-grill-me` still lives under
[`skills/in-progress`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/in-progress/README.md),
whose own README says those skills are not ready to ship and are excluded from
the plugin. Since this kit's previous audit pin
`e9fcdf95b402d360f90f1db8d776d5dd450f9234`, none of the promoted grilling,
Wayfinder, or diagnosis skills changed; the relevant default-branch changes
were the in-progress `batch-grill-me` addition and `to-tickets` cleanup.

## Current upstream flow

The current
[`ask-matt` router](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/ask-matt/SKILL.md)
is more nuanced than a mandatory five-step chain:

```text
Ordinary change, one session:
grill-with-docs → optional prototype → implement → code-review

Ordinary change, multiple implementation sessions:
grill-with-docs → optional prototype → to-spec → to-tickets
  → fresh implement session per ticket → code-review

Huge and foggy, multiple discovery sessions:
wayfinder → to-spec → to-tickets → implement → code-review

Hard bug or performance regression:
diagnosing-bugs → causal fix + regression test
  → architecture follow-up only if the diagnosis exposes a bad seam
```

Wayfinder is not a general replacement for grilling. Its own instructions say
to stop if the opening interview exposes no fog; the ordinary route is
`grill-with-docs`. Conversely, `grill-with-docs` is not the right default for
debugging. A bug report initially presents facts to establish through
reproduction. A human decision enters only if the expected behavior,
compatibility policy, or acceptable trade-off is genuinely unresolved.

## Recommended mapping into this kit

| Upstream input | Local action | Reason |
| --- | --- | --- |
| `grill-me` | Do not add | Its useful behavior is already part of `shape-change`; another public name increases choice without adding capability. |
| `grill-with-docs` | Derive into `shape-change` plus the local context/ADR policy | The project-aware interview and paper trail are valuable, but should be the default behavior of shaping a repository change, not a command users must remember. |
| `grilling` | Absorb its facts/decisions split, recommendation per question, dependency order, and confirmation gate | These are precise safeguards against self-grilling and premature implementation. |
| Draft v1.2 round-based grilling | Evaluate, do not ship by default | Batching independent decisions may be faster, but it conflicts with the kit's current developer-comfort rule of one material question at a time. Test both modes on the same scenarios first. |
| `wayfinder` | Keep as a `develop` escalation, initially guarded/experimental | It has distinct value only when discovery itself spans sessions. Do not expose it as the normal feature path. |
| `diagnosing-bugs` | Continue deriving into `diagnose-failure` | The current local skill already retains the important reproduce/minimise/hypothesise/evidence loop and safer diagnosis-only authorization. |
| `ask-matt` | Do not import | `develop` should be the active router. A separate persona-specific router merely tells the user which command to remember next. |
| `to-spec` / `to-tickets` | Continue deriving into `shape-change` / `plan-change` | The local design can preserve specs and vertical slices without forcing tracker publication or upstream auto-commit behavior. |

### Required `develop` routing contract

The user should be able to say “add team invitations,” “this checkout is
failing,” or “help me think through a new platform” without naming a skill.
`develop` should classify and invoke the primitive from repository evidence:

1. **Reported broken behavior and unknown cause** → `diagnose-failure`.
2. **Huge, multi-session discovery with unresolved decision dependencies** →
   propose/escalate to Wayfinder.
3. **Unclear outcome, scenarios, terminology, constraints, or evidence** →
   `shape-change`.
4. **Accepted specification but no executable slices** → `plan-change`.
5. **Accepted bounded slice** → `implement-slice`.

For a bug fix, the route should be:

```text
develop → diagnose-failure
  → shape-change only if expected behavior requires a human decision
  → regression test + smallest causal fix → finish
```

Within `shape-change`, the upstream grilling behavior should be explicit rather
than left to model memory:

1. inspect code, tests, docs, context, and ADRs for facts;
2. build a dependency-ordered decision tree;
3. ask the human only for decisions, with a recommendation;
4. default to one material question at a time;
5. update domain terminology and offer an ADR only under the kit's ADR gate;
6. require explicit confirmation of shared understanding before producing an
   accepted spec or implementing.

This makes the skill files—not either the user or the model's memory—the source
of routing behavior.

## License, release pinning, and provenance

The upstream repository is
[`MIT licensed`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/LICENSE).
Literal copies or substantial derived copies must retain the copyright and
license notice. Even for rewritten behavior, retain a provenance record so
future maintainers can distinguish upstream ideas from team policy.

Do not use `main`, `@latest`, or an auto-updating plugin as the behavioral pin
for the governed kit:

- for the last stable upstream baseline, pin `v1.1.0` /
  `d574778f94cf620fcc8ce741584093bc650a61d3`;
- for the exact source state reviewed here, pin
  `ed37663cc5fbef691ddfecd080dff42f7e7e350d`;
- do not promote draft v1.2 behavior until it is released and locally
  evaluated.

There is currently a transitional version mismatch on the default branch:
[`package.json`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/package.json)
still says `1.1.0`, while
[`plugin.json`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/.claude-plugin/plugin.json)
says `1.2.0`, and GitHub has no `v1.2.0` release. Use the immutable tag or
commit, not a version field copied from one manifest.

For each absorbed behavior, record:

- upstream repository, exact commit, and source path;
- license and retained notice location;
- local destination skill;
- whether text was copied, adapted, or independently rewritten;
- team-specific deviations and the evaluation that justified them.

The existing `research/candidates.lock.json` already follows this model. It can
be advanced from its earlier Matt Pocock commit only in the later implementation
change, after this routing decision is accepted.
