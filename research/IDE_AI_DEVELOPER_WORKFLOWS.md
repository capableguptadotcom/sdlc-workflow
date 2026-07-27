# AI-assisted developer workflows in IDEs and coding agents

Research date: **2026-07-26**

## Decision

Current coding-agent products converge on the same broad working rhythm:

```text
describe the outcome in ordinary language
  → inspect repository context
  → clarify only material decisions
  → review a plan when the work is complex
  → implement against executable feedback
  → review the diff and evidence
  → commit or open a PR only after human acceptance
```

The AI-SDLC kit should make that rhythm the product. Developers should not
need to remember `shape-change`, `diagnose-failure`, `grill-me`, or any other
internal skill name. They should describe the work, see a short plain-language
status, answer only decisions the repository cannot answer, and review durable
artifacts at meaningful gates.

The vendors expose similar ideas through different files and controls. The kit
should promise **behavioral and artifact parity**, not identical automation:
one canonical repository contract and skill source, plus thin host adapters,
capability checks, and cross-host evaluations.

## Method and evidence boundary

This report uses first-party documentation and product guidance from OpenAI,
GitHub, Cursor, and Anthropic. These sources establish supported mechanisms and
the workflows each vendor recommends. They are not independent telemetry about
how every developer actually works, so this report does not make adoption-rate
or productivity-multiplier claims.

Product behavior is moving quickly. The implementation should pin the kit's
own behavior and continuously test supported surfaces instead of assuming a
vendor feature remains identical.

## Official-source findings

### OpenAI Codex

OpenAI recommends describing a task with a goal, relevant context,
constraints, and a concrete “done when” condition. For complex or ambiguous
work, its guidance recommends Plan mode, an interview, or a durable execution
plan before implementation. It also says not every task needs this heavier
planning path. See [Codex best practices](https://learn.chatgpt.com/guides/best-practices)
and [Using `PLANS.md` for multi-hour problem solving](https://developers.openai.com/cookbook/articles/codex_exec_plans).

Codex treats `AGENTS.md` as durable repository guidance. It builds an
instruction chain from global, repository, and nested files, with nearer files
taking precedence. The guidance recommends concise, practical instructions and
moving task-specific procedures out of an oversized root file. See
[Custom instructions with `AGENTS.md`](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Codex skills use progressive disclosure. The host first sees a skill's name and
description, then loads the body when the user explicitly invokes it or when
the description matches the task. Repository skills are discovered under
`.agents/skills`. This makes skills a better home for reusable procedures than
an always-loaded instruction file. See
[Build skills](https://learn.chatgpt.com/docs/build-skills).

Codex separates technical authority from behavioral guidance. Sandbox mode
defines what the agent can technically access; the approval policy defines when
it must stop and ask. Read-only mode is available for planning and inspection,
while workspace-write can permit ordinary edits and commands inside the active
workspace. See
[Agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security).

OpenAI's recommended completion loop includes tests, relevant deterministic
checks, diff review, and confirmation that the result matches the request.
Codex provides local diff review and branch/commit/uncommitted review targets;
its IDE surface can use open files and selections as context and display edits
in place. See [Codex best practices](https://learn.chatgpt.com/guides/best-practices),
[Codex IDE extension](https://learn.chatgpt.com/docs/codex/ide), and
[Codex code review](https://learn.chatgpt.com/docs/code-review?surface=app).

Codex lifecycle hooks can run at events such as `PreToolUse`, `PostToolUse`,
`Stop`, and `SessionStart`. Non-managed command hooks require review and trust
before they run. OpenAI lists validation at turn stop, secret checks, and audit
logging as examples. See [Codex hooks](https://learn.chatgpt.com/docs/hooks).

### GitHub Copilot

Copilot IDE chat distinguishes three developer intents:

- **Ask** for understanding and exploration;
- **Plan** for a detailed implementation plan before execution;
- **Agent** for autonomous multi-step edits, commands, and iteration.

When a plan is complete, the user can start implementation or open the plan as
Markdown. See
[Asking GitHub Copilot questions in an IDE](https://docs.github.com/en/copilot/using-github-copilot/asking-github-copilot-questions-in-your-ide).

Copilot distinguishes always-on repository instructions from focused,
reusable workflows:

- `.github/copilot-instructions.md` applies repository-wide;
- `.github/instructions/*.instructions.md` can be path-specific;
- `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` are supported on a subset of
  surfaces;
- prompt files are manually selected task templates;
- skills are loaded when relevant;
- hooks run automatically at lifecycle points.

GitHub explicitly notes that support differs by IDE, CLI, cloud agent, and code
review surface. See the
[customization cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet)
and
[custom-instructions support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support).

GitHub says custom instructions should be short, self-contained, and broadly
applicable because they accompany many interactions. It also warns that
Copilot may not follow them identically every time. Project skills can live in
`.github/skills`, `.claude/skills`, or `.agents/skills`, and Copilot can load
them based on task relevance. See
[About customizing Copilot responses](https://docs.github.com/en/copilot/concepts/prompting/response-customization)
and [About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills).

The Copilot CLI `init` flow analyzes a repository and writes or proposes
improvements to `.github/copilot-instructions.md`; it does not require the user
to author the first version from nothing. See the
[Copilot CLI command reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference).

Copilot hooks are deterministic shell commands supported by Copilot CLI and
the cloud agent. They can approve or deny tool use, record audits, run checks,
or react at session completion. They are not a universal IDE hook surface.
See [About hooks for GitHub Copilot](https://docs.github.com/en/copilot/concepts/agents/hooks).

GitHub's AI-code review guidance says to run compilation, tests, and static
analysis first; then verify intent, architecture, dependencies, edge cases, and
AI-specific mistakes. GitHub also states that Copilot review is not guaranteed
to find every issue and should be supplemented by human review. See
[Review AI-generated code](https://docs.github.com/en/copilot/tutorials/review-ai-generated-code)
and
[About Copilot code review](https://docs.github.com/en/copilot/concepts/agents/code-review).

### Cursor

Cursor's current Plan mode researches the repository, asks clarifying
questions, creates a reviewable plan with file and code references, and waits
for approval before implementation. Plans can be edited and saved to the
workspace for resumption and future agents; they remain outside the workspace
unless the developer deliberately saves them there. Cursor also says detailed
planning is unnecessary for quick, familiar changes. See
[Plan Mode](https://cursor.com/docs/agent/plan-mode) and Cursor's first-party
[agent best-practices guide](https://cursor.com/blog/agent-best-practices).

Cursor separates static and dynamic context. Project rules are versioned,
scoped instructions; `AGENTS.md` is a simpler project instruction surface;
skills are loaded for relevant task-specific procedures. Cursor recommends
short rules containing actual commands, canonical code examples, and stable
constraints. It advises against copying whole style guides, documenting every
possible command, or pre-optimizing rules before repeated friction appears.
See [Cursor Rules](https://cursor.com/docs/rules) and the
[agent best-practices guide](https://cursor.com/blog/agent-best-practices).

Cursor recommends starting a new conversation when moving to a different
feature or after completing one logical unit, while continuing the same
conversation for iteration or debugging of the current feature. Its rationale
is that long conversations accumulate irrelevant context. The agent can search
for context itself, so developers need not manually attach every potentially
relevant file. See the
[agent best-practices guide](https://cursor.com/blog/agent-best-practices).

For difficult bugs, Cursor's Debug Mode deliberately avoids an immediate fix:
it creates multiple hypotheses, instruments the program, asks the developer to
reproduce the problem, analyzes runtime evidence, makes a targeted fix, and
asks for another human verification run before removing instrumentation. See
[Debug Mode](https://cursor.com/docs/agent/debug-mode) and
[Introducing Debug Mode](https://cursor.com/blog/debug-mode).

Cursor exposes diff review during and after generation, a dedicated local
Agent Review, and PR review through Bugbot. Its own guidance states that
AI-generated code still needs careful review. See
[Cursor agent best practices](https://cursor.com/blog/agent-best-practices)
and [Agent Review](https://cursor.com/docs/agent/agent-review).

Cursor checkpoints are automatic local snapshots of agent changes. The
documentation explicitly says they track only agent edits and are not version
control; Git remains the durable history. See
[Cursor Agent overview](https://cursor.com/docs/agent/overview).

Cursor's own onboarding sequence starts with an explanation of the existing
codebase, then a small safe change whose diff and project checks the developer
reviews, and only later a larger Plan-mode task. See the
[Cursor quickstart](https://cursor.com/docs/get-started/quickstart).

Cursor also separates prompt guidance from command autonomy through Run Modes.
Its documentation explicitly says the Auto-review classifier is a convenience
layer rather than a security boundary. See
[Cursor Run Modes](https://cursor.com/docs/agent/security/run-modes).

### Claude Code

Claude Code loads organization, user, project, local, and nested `CLAUDE.md`
files at different scopes. Its `/init` flow analyzes a repository and, when a
file already exists, suggests improvements instead of replacing it. Anthropic
recommends concrete, structured instructions and targets fewer than 200 lines
per `CLAUDE.md`; path-scoped rules should carry specialized guidance. See
[How Claude remembers a project](https://code.claude.com/docs/en/memory).

Anthropic explicitly distinguishes guidance from enforcement:
`CLAUDE.md` shapes model behavior, while settings and hooks enforce technical
policy. If something must happen at a fixed point, such as before a command or
after an edit, the documentation recommends a hook rather than hoping the
model remembers an instruction. See
[How Claude remembers a project](https://code.claude.com/docs/en/memory) and
[Automate actions with hooks](https://code.claude.com/docs/en/hooks-guide).

Claude Code Plan mode is read-only: it researches and proposes changes without
editing source. The user can approve into several permission modes, continue
planning with feedback, or open the plan in an editor. See
[Choose a permission mode](https://code.claude.com/docs/en/permission-modes).

Anthropic's broader recommendation is to explore before proposing changes,
plan before coding when the work is non-trivial, and give a fresh-context
reviewer the written plan or specification when checking the result. For fuzzy
requirements, it recommends an interview that produces a self-contained spec
with scope and end-to-end verification before a fresh implementation session.
See [Claude Code best practices](https://code.claude.com/docs/en/best-practices).

Claude Code skills are reusable procedures loaded when relevant or invoked
directly. Project skills live under `.claude/skills`; plugins package versioned
skills, agents, hooks, and MCP configuration for distribution across projects.
See [Extend Claude with skills](https://code.claude.com/docs/en/skills) and
[Create plugins](https://code.claude.com/docs/en/plugins).

Anthropic's everyday bug recipe asks for the failing command, stack trace,
reproduction steps, and whether the issue is intermittent. Its testing recipe
ends by running and fixing the tests, while its refactor recipe emphasizes
small, testable increments and behavior preservation. See
[Claude Code common workflows](https://code.claude.com/docs/en/common-workflows).

Claude Code can run a local review in an isolated background context, then
return findings to the working conversation. Its hosted GitHub review is
neutral by default rather than a merge-blocking approval; teams that want a
gate must construct one around explicit outputs. See
[Claude Code Review](https://code.claude.com/docs/en/code-review).

## What the official products agree on

| Concern | Convergent pattern |
| --- | --- |
| Starting a task | State the desired result in normal language; attach exact context only when it is known and material. |
| Existing repositories | Explore the code, commands, conventions, and history before proposing a change. |
| Persistent guidance | Keep repository instructions concise, versioned, scoped, and broadly applicable. |
| Reusable procedures | Put multi-step workflows in dynamically loaded skills rather than the always-loaded root instructions. |
| Complex work | Separate exploration/planning from editing and ask for plan approval. |
| Small work | Skip ceremonial planning when intent, scope, and verification are already obvious. |
| Debugging | Reproduce, gather runtime evidence, test hypotheses, make a causal fix, and verify again. |
| Implementation | Give the agent an executable success signal such as a test, type check, build, or reproducible behavior. |
| Review | Inspect the diff, run deterministic checks, use AI review as another signal, and retain human responsibility. |
| Enforcement | Use hooks, permissions, Git hooks, CI, and branch protection for deterministic controls; instructions alone are not enforcement. |
| Long-running work | Preserve durable state in repository artifacts and use isolated sessions/worktrees for independent tasks. |
| Improvement | Add guidance after recurring friction, then review it like code. |

## Important differences the kit must absorb

1. **Instruction discovery is not uniform.** Codex has hierarchical
   `AGENTS.md`; Copilot support varies by surface; Claude has its own
   `CLAUDE.md` hierarchy; Cursor has structured project rules in addition to
   `AGENTS.md`.
2. **Skill paths are not uniform.** `.agents/skills` is native to Codex and
   supported by Copilot, while Claude's project path is `.claude/skills`.
   Host adapters or a packaged plugin are still necessary.
3. **Hooks are not uniform.** Codex, Claude Code, Copilot CLI/cloud, and Cursor
   use different configuration locations and event schemas. Copilot's IDE
   surfaces do not expose all Copilot CLI/cloud hooks.
4. **A plan is not automatically a durable specification.** Vendor Plan modes
   primarily govern proposed implementation. Some can save Markdown, but none
   defines the team's product contract, ADR lifecycle, verification record,
   or ticket hierarchy for us.
5. **Review products are advisory.** Their scope, severity, cost, trigger, and
   merge behavior differ. None is evidence that deterministic checks or human
   review can be removed.
6. **Local memory and checkpoints are not team knowledge.** A session,
   checkpoint, or machine-local memory may help continuity, but versioned
   repository artifacts remain the shareable source of truth.

## Recommendations for this AI-SDLC kit

The remainder of this report is a recommendation derived from the official
source patterns above, not a statement that a vendor already implements this
exact composition.

### 1. Give developers one conversational front door

The visible contract should be:

> Describe what you want to build, understand, fix, or finish in your own
> words. The workflow will inspect the repository and tell you the next
> meaningful step.

`develop` should own routing. It should acknowledge the route in language such
as “checking existing behavior,” “settling one product decision,”
“diagnosing before editing,” or “mapping a larger initiative.” It should not
ask the developer to select an internal skill.

### 2. Use a progressive workflow rather than a mandatory ceremony

```text
Orient
  Read active instructions, config, relevant code/tests, specs, and ADRs.

Classify
  Question/explanation | small clear change | fuzzy feature | failure |
  large initiative | finish/review.

Shape only as needed
  Establish facts from the repository.
  Ask humans only for intent, policy, priority, and trade-offs.

Accept intent
  Record the smallest durable behavior and verification contract.

Plan only as needed
  Create implementation slices when the change spans multiple bounded steps.

Execute
  Implement one slice against the smallest useful feedback loop.

Finish
  Run deterministic checks, review correctness and intent, simplify changed
  code where useful, rerun affected checks, and show evidence.
```

This preserves the products' light path for obvious changes while retaining a
strong plan gate for ambiguous, risky, or multi-step work.

### 3. Keep the artifact meanings distinct

| Artifact | Question it answers | Lifecycle |
| --- | --- | --- |
| `AGENTS.md` | How should agents work in this repository? | Concise, durable, reviewed; route to deeper material. |
| Project context/glossary | What system and domain are we working in? | Updated when stable facts or language change. |
| `spec.md` | What observable behavior are we agreeing to build? | Accepted before material implementation; amended when intent changes. |
| `verification.md` | How will we know the behavior works, and what evidence did we obtain? | Drafted with the spec; completed during delivery. |
| `plan.md` | In what technical order will we implement an accepted change? | Optional and mutable; required only for multi-step/risky work. |
| Tickets | What independently verifiable slices can be assigned or resumed? | Created after intent is accepted and only when multiple slices help. |
| ADR | Why did we choose a durable, hard-to-reverse architecture decision? | Historical after acceptance; superseded by a new ADR rather than rewritten. |
| Handoff/session note | What transient state does the next session need? | Disposable after the durable artifacts and code are current. |

Do not store the full project narrative in `AGENTS.md`, and do not call a host's
generated implementation plan a product specification without a deliberate
conversion and acceptance step.

### 4. Make host integration thin and testable

- Keep `AGENTS.md` as the canonical behavioral router.
- Keep canonical workflow content in `.agents/skills`.
- Generate or maintain thin adapters for Claude and Copilot rather than
  independently authored copies.
- Put deterministic commands in shared repository scripts; let host-specific
  hook files call those scripts where the surface supports hooks.
- Validate that every adapter points to the same kit version and canonical
  workflow.
- Run dialogue-based routing and behavior tests in every claimed surface.

### 5. Put human gates where judgment is actually required

Human confirmation should be required when:

- intent, scope, public behavior, data policy, or risk is unresolved;
- a proposed spec is ready to become the behavior contract;
- a durable architecture decision is proposed or superseded;
- a complex implementation plan is ready to execute;
- the final diff and evidence are ready for commit, PR, deployment, or merge.

Routine reads, searches, targeted tests, formatting, and other reversible work
inside the authorized workspace should not create conversational approval
fatigue. Host permissions still govern what may technically execute.

### 6. Make debugging a separate evidence loop

The brownfield bug route should be:

```text
report in ordinary language
  → establish expected vs actual behavior
  → obtain a repeatable or instrumented feedback loop
  → inspect relevant code, tests, history, specs, and ADRs
  → rank falsifiable hypotheses
  → gather evidence
  → add a regression test when feasible
  → make the smallest causal fix
  → reproduce/verify again
  → run finish
```

Questioning or ADR work enters only when diagnosis reveals an unresolved
product policy or a durable architecture trade-off. A bug does not
automatically require a new spec or ADR.

### 7. Design onboarding as a short guided success

After adoption, the installer should point to one human walkthrough and one
next action. A useful first session is:

```text
Developer: Give me an overview of this project. Do not change files.

System: I’m orienting to the repository first.
        [Returns purpose, components, commands, domain glossary,
        active specs/ADRs, and notable gaps with file references.]

Developer: Show me how a normal feature would move through our workflow.

System: [Demonstrates a small, repository-relevant example and identifies
        the points where the developer reviews intent, plan, and final diff.]
```

The generated instruction baseline should always be reviewable. Existing
`AGENTS.md`, `CLAUDE.md`, Copilot instructions, rules, hooks, and CI must be
merged or adapted, never silently replaced.

### 8. Use dialogue scenarios as acceptance tests

The walkthrough and the evaluation suite should share the same scenarios:

1. **Clear small change** — inspect, create a minimal brief, implement, verify;
   no unnecessary grilling or plan file.
2. **Fuzzy feature in an existing project** — inspect first, ask one material
   decision at a time, accept a spec, then plan/implement.
3. **Unknown legacy bug** — reproduce and diagnose before changing code.
4. **Large foggy initiative** — map decision tracks before creating individual
   specs and tickets.
5. **Architecture decision** — create an ADR only for a durable trade-off and
   later supersede it with bidirectional links.
6. **Finish before commit** — tests and review precede simplification;
   simplification triggers re-verification; commit remains explicitly
   authorized.
7. **First brownfield adoption** — preserve existing instructions and hooks,
   preview changes, and surface conflicts.
8. **Kit update with local changes** — update untouched managed files, preserve
   project-owned files, and stop on ambiguous conflicts.

Each scenario should assert the visible status, the internal route, artifacts
created or deliberately skipped, human gates, checks run, and final evidence.

## Anti-patterns to avoid

- Requiring developers to memorize a growing command or skill vocabulary.
- Asking the user for facts already discoverable in the repository.
- Running a full spec/plan/ticket ceremony for every reversible edit.
- Starting implementation while material behavior or policy is unresolved.
- Treating an implementation plan as the product contract.
- Filling `AGENTS.md` with procedures, long style guides, or transient project
  history.
- Assuming an instruction was enforced merely because it was placed in a
  Markdown file.
- Automatically running networked, file-editing AI inside Git pre-commit.
- Accepting a plausible bug fix without reproduction and post-fix evidence.
- Treating AI review as proof of correctness or a replacement for human
  approval.
- Treating IDE checkpoints, chat history, or machine-local memory as shared
  version control.
- Promising identical host behavior without capability detection and
  cross-surface evaluations.
- Letting independent adapters drift away from the canonical workflow.

## Implication for the build plan

Stabilize and test the workflow and artifact contract before building the
updater. The safest dependency order is:

1. approve developer-facing dialogue scenarios and the progressive artifact
   model;
2. implement the natural-language router and specialist workflows;
3. turn the dialogues into cross-host evaluations;
4. add validators and thin host adapters;
5. then build the state-aware, brownfield-safe distribution command.

Otherwise, the installer will efficiently distribute a workflow whose user
contract is still changing.
