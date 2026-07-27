---
name: diagnose-failure
description: Determine the root cause of a reproducible bug, failing test, runtime error, regression, or unexpected system behavior. Use when the cause is unknown and evidence must distinguish hypotheses. Do not use for feature planning or to apply a guessed fix without diagnosis.
---

# Diagnose failure

1. State the observed failure, expected behavior, impact, and current evidence.
2. Reproduce it with the smallest reliable command, input, or scenario. If it is
   not reproducible, identify the missing observability instead of guessing.
   In diagnosis-only mode, suppress incidental caches, snapshots, coverage
   files, and build artifacts when practical; disclose any unavoidable writes.
3. Minimize the reproduction while preserving the failure.
4. Write a small set of falsifiable hypotheses ranked by evidence.
5. Change or instrument one variable at a time. In read-only mode, use
   ephemeral commands or external observation rather than persistent source
   edits. Prefer boundary observations, state diffs, logs, traces, and
   assertions over broad debug output.
6. Reject or strengthen each hypothesis using new evidence.
7. Identify the root cause and the causal chain, not merely the failing line.
8. When the user also asked for a fix, add a regression test, implement the
   smallest causal fix, rerun relevant checks, and remove temporary diagnostics.

Return the reproduction, evidence, root cause, confidence, fix status, and any
unresolved alternatives. Do not modify code when the request is diagnosis-only.
If the normal runner is unavailable, a narrower equivalent reproduction is
acceptable only when it preserves the relevant setup and failing assertion.
