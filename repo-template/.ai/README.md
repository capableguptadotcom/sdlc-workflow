# AI Developer Kit

> Workflow alpha. The repository guidance and structural checks are installed;
> use them with project-specific validation and evidence.

Describe the work normally. The assistant investigates the repository, asks only for decisions that belong to you, chooses the lightest reliable workflow, and shows evidence before calling the work ready.

Start with the [interactive workflow walkthrough](workflow-walkthrough.html) for visual, scenario-based tutorials and copyable example prompts.

## How to work with it

1. **Describe the goal** — State the outcome, problem, question, or uncertainty in ordinary language. The assistant will recognize whether this is orientation, change, failure, learning, or finish work.
2. **Inspect before asking** — Do not reconstruct facts the repository already contains. The assistant will read relevant code, tests, instructions, specifications, context, and decisions.
3. **Settle only important decisions** — Choose product policy, acceptable risk, and durable trade-offs. The assistant will own routine implementation choices and bring recommendations for consequential decisions.
4. **Build the smallest useful slice** — Review material behavior contracts and plans when they are warranted. The assistant will keep tiny work tiny, implement accepted behavior in verifiable slices, and adapt when evidence changes scope.
5. **Finish with evidence** — Authorize commits, pushes, pull requests, or other external actions explicitly. The assistant will run relevant checks, review correctness, simplify only when useful, recheck, and report readiness.

## Things you can say

| You say | The assistant |
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

## Examples in context

### Start when the implementation approach is unknown

**Developer:** I want users to access recent records offline, but I have no idea how to implement it.

**Assistant:** I will inspect the current data loading, caching, authentication, and mutation paths before asking you to make decisions.

**Assistant:** This is one coherent feature, not an initiative. The product decision is whether offline access is read-only or also queues writes. I recommend read-only first because queued writes require synchronization and conflict policy. Which behavior do you need?

**Developer:** Start with read-only offline access.

**Assistant:** I will own the routine implementation choices. If repository evidence cannot settle a measurable technical question, I will run a bounded prototype; if one durable choice has several defensible options, I will compare them and bring you a recommendation. I will now draft the behavior and verification contract for review.

### Shape a fuzzy brownfield feature

**Developer:** Add team invitations.

**Assistant:** I will inspect the current roles, user flow, email provider, and related decisions before asking you for product choices.

**Assistant:** The repository does not say who may invite. I recommend Owners and Admins, while only Owners may invite another Owner. Should we use that rule?

**Developer:** Yes. Invitations expire after 72 hours.

**Assistant:** I will draft the behavior and verification contract. I will not implement until you accept it.

### Make a clear tiny change

**Developer:** Change the settings dialog button from Save to Save changes and update the test.

**Assistant:** This is clear, local, reversible, and low risk. I will make the smallest edit and run the focused UI test; no feature folder or planning ceremony is needed.

**Assistant:** The label and assertion are updated. The focused test passes, the diff contains only the requested change, and no simplification was useful. Readiness: ready.

### Diagnose and fix an existing failure

**Developer:** Some checkout retries charge the customer twice. Find the cause and fix it.

**Assistant:** I am diagnosing the failure before changing product code. I will reproduce it and inspect the checkout boundary, tests, history, specs, and relevant ADRs.

**Assistant:** The timeout retry creates a new idempotency key, violating the existing payment decision. I will add a regression test, make the smallest causal fix, and rerun affected checkout checks.

**Assistant:** The regression was red before the fix and is green now. The affected suite passes and no new ADR is needed. Readiness: ready.

### Finish before committing

**Developer:** Looks good. Commit it.

**Assistant:** That authorizes the commit, but I will finish first: run configured checks, review against intent and repository standards, simplify only verified changed code when useful, and rerun affected checks.

**Assistant:** The checks and final review pass. Readiness: ready. I will create the requested commit, but I will not push or open a pull request unless asked.
