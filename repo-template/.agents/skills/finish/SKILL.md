---
name: finish
description: Prepare an existing code diff for human review by running deterministic verification, reviewing against the specification and standards, simplifying safely, and recording evidence. Use when implementation is substantially complete or the user explicitly invokes finish. Do not use to invent missing requirements or to approve unverified work.
---

# Finish

Use the same order for every completed code change, but scale the checks and
artifact work to the diff. A tiny change may need only focused checks, a bounded
review, and a no-op simplification assessment.

1. Establish the intended diff and exclude unrelated user changes.
2. Read applicable specs, plans, ADRs, `AGENTS.md`, and configured commands.
3. Run deterministic checks first. If they fail, stop review-oriented polishing
   and report or diagnose the failure. When the change produces a publishable
   artifact, inspect its actual contents and size as well as the command status;
   flag unintended internal guidance, specs, evals, handoffs, or secrets.
   A runtime check that starts a long-running process must own its complete
   start/check/stop lifecycle in one bounded command or tool session, use
   failure-safe cleanup such as a shell trap or `finally`, and produce a
   terminal event for every started command. Verify the process or listener is
   gone afterward. Any active process or command without a terminal event makes
   the verdict `not-ready`, even when the probe itself succeeded.
4. Follow `../review-change/SKILL.md` against the verified diff.
5. Resolve blocking correctness findings when authorized, then rerun checks.
6. Assess changed code for behavior-preserving simplification. Follow
   `../simplify-change/SKILL.md` only when a useful in-scope simplification
   exists, then rerun affected checks.
7. Trigger security, UI, accessibility, motion, documentation, or migration
   review only when the diff matches that scope.
8. Update verification evidence and consequential documentation. Treat stale
   required public or operational documentation as not ready.
9. Check whether the diff introduced or replaced an architecture decision. An
   ADR is warranted only when the decision is hard to reverse, surprising
   without context, and the result of a real trade-off.
10. Perform a compact final diff review and rerun affected checks after every
    edit.

Return a concise readiness verdict: `ready`, `ready-with-advisories`, or
`not-ready`, with commands, evidence, blockers, and limitations.

Commit, push, open a pull request, deploy, or merge only when that exact action
is authorized and the readiness verdict permits it.
