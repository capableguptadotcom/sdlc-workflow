# AI Developer Kit walkthrough (draft)

> Tabletop design only. This walkthrough describes the accepted product
> contract; it does not claim the active skills implement every scenario yet.

Describe work normally. The assistant inspects the repository, announces what
it is doing in plain language, and uses the lightest reliable workflow.

## The developer mental model

Describe the work normally. The assistant investigates the repository, asks only for decisions that belong to you, chooses the lightest reliable workflow, and shows evidence before calling the work ready.

1. **Describe the goal** — Developer: State the outcome, problem, question, or uncertainty in ordinary language. Assistant: Recognize whether this is orientation, change, failure, learning, or finish work.
2. **Inspect before asking** — Developer: Do not reconstruct facts the repository already contains. Assistant: Read relevant code, tests, instructions, specifications, context, and decisions.
3. **Settle only important decisions** — Developer: Choose product policy, acceptable risk, and durable trade-offs. Assistant: Own routine implementation choices and bring recommendations for consequential decisions.
4. **Build the smallest useful slice** — Developer: Review material behavior contracts and plans when they are warranted. Assistant: Keep tiny work tiny, implement accepted behavior in verifiable slices, and adapt when evidence changes scope.
5. **Finish with evidence** — Developer: Authorize commits, pushes, pull requests, or other external actions explicitly. Assistant: Run relevant checks, review correctness, simplify only when useful, recheck, and report readiness.

## Things developers can say

| Developer says | Assistant does |
| --- | --- |
| Give me an overview of this project. Do not change files. | Inspects and explains the repository without editing. |
| Rename this button and update its test. | Makes the bounded change and runs the focused check without creating planning artifacts. |
| Add team invitations. | Inspects existing roles, asks only unresolved product questions, and drafts a behavior contract before material implementation. |
| I want offline access, but I have no idea how to implement it. | Separates product behavior from technical uncertainty, owns routine engineering choices, and uses evidence for the rest. |
| Polling, webhooks, and server-sent events all seem viable. | Compares the consequences from relevant perspectives, recommends one option, and leaves the durable choice to the developer. |
| We do not know whether IndexedDB meets the latency target. | Runs a bounded prototype for that named empirical question. |
| Build the customer platform across channels, regions, identity, and billing. | Proposes an initiative map because several coordinated outcomes cannot remain one coherent spec. |
| Checkout retries sometimes charge twice. Find the cause and fix it. | Reproduces and diagnoses before making the smallest causal fix. |
| Pause and teach me this migration pattern, then return here. | Preserves the workstream, teaches the needed concept, checks understanding, and resumes. |
| Finish this and commit it. | Completes checks and review before making only the authorized Git action. |

## How the assistant classifies uncertainty

| Signal | Example | Response | Internal route |
| --- | --- | --- | --- |
| A repository fact is missing | How is authentication implemented here? | Inspect the repository instead of asking the developer. | `repository inspection` |
| Product behavior or policy is missing | Should offline mode allow queued writes? | Ask one focused question with a recommendation and trade-off. | `shape-change with grilling behavior` |
| A routine technical choice is unresolved | Which existing serializer pattern should this field use? | Follow repository evidence and make the engineering choice. | `agent-owned implementation decision` |
| An external or version-sensitive fact is missing | Does the supported SDK version expose this capability? | Verify the primary source and record the relevant limitation. | `bounded research` |
| A measurable implementation question is unresolved | Can IndexedDB meet the required query latency? | Run a throwaway experiment that answers only the named question. | `bounded prototype` |
| One durable decision has several defensible answers | Should delivery use polling, webhooks, or server-sent events? | Compare relevant perspectives, recommend a choice, and let the human decide. | `simulated discussion inside shaping` |
| Discovery contains several coordinated outcomes or decision tracks | Build one customer platform spanning identity, billing, regions, and channels. | Propose an initiative map and return each coherent outcome for its own spec. | `guarded Wayfinder initiative mapping` |

## Visible modes

- Checking the existing project
- Settling an important behavior decision
- Making the implementation order explicit
- Building the accepted slice
- Diagnosing the failure before editing
- Mapping a larger initiative
- Finishing verification and review
- Teaching the needed concept, then returning
- Checking the installed workflow safely

## Adopt an existing repository

**Developer:** Run npx @innovate-x/ai-sdlc@alpha in an existing repository.

**Kit:** I found the existing stack, instructions, hooks, CI, and project commands. No files have changed. Review this adoption preview and confirm whether I should apply it.

**Developer:** Apply it.

**Kit:** Adoption is applied and validated. Existing project guidance and hooks were preserved. Next, ask your assistant for a read-only project overview.

- Route: inspect repository -> preview adoption -> confirm -> apply transaction -> validate
- Creates: reviewed workflow files, thin host adapters, human walkthrough, project command mapping, installation lock
- Skips: feature spec, implementation plan, tracker tickets, ADR
- Human gates: confirm the complete adoption preview before any mutation
- Checks: structural validation, mapped project validation when configured
- Must not: ask the developer to classify the repository by stack, require multiple setup commands
- Terminal state: `adopted`

## Start when the implementation approach is unknown

**Developer:** I want users to access recent records offline, but I have no idea how to implement it.

**Assistant:** I will inspect the current data loading, caching, authentication, and mutation paths before asking you to make decisions.

**Assistant:** This is one coherent feature, not an initiative. The product decision is whether offline access is read-only or also queues writes. I recommend read-only first because queued writes require synchronization and conflict policy. Which behavior do you need?

**Developer:** Start with read-only offline access.

**Assistant:** I will own the routine implementation choices. If repository evidence cannot settle a measurable technical question, I will run a bounded prototype; if one durable choice has several defensible options, I will compare them and bring you a recommendation. I will now draft the behavior and verification contract for review.

- Route: develop -> inspect repository -> shape unresolved product behavior -> resolve technical uncertainty with evidence -> accept spec -> plan only if warranted -> implement -> finish
- Creates: spec.md and verification.md after behavior is settled, plan.md only when multiple slices or risk warrant it
- Skips: initiative map for one coherent outcome, ADR unless a durable decision passes the ADR gate, tracker tickets unless useful and authorized
- Human gates: choose unresolved product behavior, accept the behavioral spec, choose a durable contested trade-off only when one exists
- Checks: repository-specific checks mapped to accepted behavior, bounded prototype measurement only when an empirical question remains, configured finish checks
- Must not: ask the developer to design routine implementation details, trigger initiative mapping merely because the developer is uncertain, debate a question that repository evidence or a small experiment can answer
- Terminal state: `ready`

## Shape a fuzzy brownfield feature

**Developer:** Add team invitations.

**Assistant:** I will inspect the current roles, user flow, email provider, and related decisions before asking you for product choices.

**Assistant:** The repository does not say who may invite. I recommend Owners and Admins, while only Owners may invite another Owner. Should we use that rule?

**Developer:** Yes. Invitations expire after 72 hours.

**Assistant:** I will draft the behavior and verification contract. I will not implement until you accept it.

- Route: develop -> inspect facts -> shape change -> accept spec -> plan change -> implement slices -> finish
- Creates: spec.md, verification.md, plan.md
- Skips: tracker tickets unless separately authorized, ADR unless the decision passes the ADR gate, CONTEXT.md unless a stable domain term needs definition
- Human gates: confirm unresolved product policy, accept the behavioral spec, accept the multi-slice plan, authorize any external tracker mutation
- Checks: checks mapped to every accepted criterion, affected checks after each slice, configured finish checks
- Must not: ask for repository facts that can be inspected, create an ADR for reversible expiry policy
- Terminal state: `ready`

## Make a clear tiny change

**Developer:** Change the settings dialog button from Save to Save changes and update the test.

**Assistant:** This is clear, local, reversible, and low risk. I will make the smallest edit and run the focused UI test; no feature folder or planning ceremony is needed.

**Assistant:** The label and assertion are updated. The focused test passes, the diff contains only the requested change, and no simplification was useful. Readiness: ready.

- Route: develop -> implement from inline brief -> adaptive finish
- Creates: request and verification evidence in the change summary
- Skips: feature folder, spec.md, plan.md, tracker tickets, ADR
- Human gates: none
- Checks: focused UI test
- Must not: requirements interview, planning artifact generation
- Terminal state: `ready`

## Diagnose and fix an existing failure

**Developer:** Some checkout retries charge the customer twice. Find the cause and fix it.

**Assistant:** I am diagnosing the failure before changing product code. I will reproduce it and inspect the checkout boundary, tests, history, specs, and relevant ADRs.

**Assistant:** The timeout retry creates a new idempotency key, violating the existing payment decision. I will add a regression test, make the smallest causal fix, and rerun affected checkout checks.

**Assistant:** The regression was red before the fix and is green now. The affected suite passes and no new ADR is needed. Readiness: ready.

- Route: develop -> diagnose failure -> regression test -> causal fix -> affected checks -> finish
- Creates: regression test, verification evidence
- Skips: new ADR, feature spec when expected behavior is already settled
- Human gates: none
- Checks: red-capable reproduction, focused checkout checks, affected checkout suite
- Must not: guess and patch the first suspicious line, leave broad permanent instrumentation
- Terminal state: `ready`

## Finish before committing

**Developer:** Looks good. Commit it.

**Assistant:** That authorizes the commit, but I will finish first: run configured checks, review against intent and repository standards, simplify only verified changed code when useful, and rerun affected checks.

**Assistant:** The checks and final review pass. Readiness: ready. I will create the requested commit, but I will not push or open a pull request unless asked.

- Route: finish -> deterministic checks -> correctness review -> authorized fixes and recheck -> scoped simplification and recheck -> final diff review -> authorized commit
- Creates: verification evidence, authorized Git commit
- Skips: new planning artifacts, pull request unless separately requested
- Human gates: authorize commit, separately authorize push or pull request
- Checks: configured relevant project checks, affected checks after any review fix or simplification
- Must not: commit a known-broken diff, treat AI review as deterministic evidence
- Terminal state: `committed`
