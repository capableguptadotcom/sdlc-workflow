---
name: handoff-and-teach
description: Capture enough redacted state to resume work safely or teach one concept in a separate focused context. Use when pausing, transferring ownership, switching agents, escalating, or creating a learning detour from an active workflow. Do not use for a generic progress summary or as a substitute for committed specifications and decisions.
---

# Handoff and teach

## Capture state

Write a transient handoff under the configured `transient_handoffs` path unless
the user requests a durable project artifact. Include:

- objective and current status;
- accepted specification and decisions;
- relevant files, commands, artifacts, and evidence;
- approaches tried, results, and dead ends;
- pending question or next action;
- constraints, risks, and stop conditions.

Redact credentials, personal data, tokens, private URLs, and unnecessary logs.
Reference large artifacts by safe path instead of copying them into the handoff.

## Teaching mode

When the handoff exists to resolve a knowledge gap:

1. Name the exact concept and why it blocks the work.
2. Explain it from first principles with one concrete example tied to the
   current system.
3. Contrast the nearest confusing alternative.
4. Ask one transfer question that requires applying the idea.
5. Append the learned conclusion and its effect on the pending decision.

The receiving workflow must inspect current repository state again before
acting; a handoff is context, not proof that the workspace is unchanged.
