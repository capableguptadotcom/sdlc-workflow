---
name: learn
description: Pause a development or requirements session, create a focused teaching handoff, learn one blocking concept, and return with the result. Use when the user explicitly invokes learn or says they cannot continue because they do not understand a relevant concept. Do not use for ordinary codebase research that the active workflow can perform directly.
---

# Learn

Keep the primary workstream clean while resolving a knowledge gap.

1. Name the exact concept and the decision or task it blocks.
2. Follow `../handoff-and-teach/SKILL.md` to capture a redacted teaching handoff.
3. Teach from first principles, then connect the concept to the current code or
   design. Prefer a small worked example over a broad course.
4. Check understanding with one transfer question or a tiny exercise.
5. Record the conclusion, remaining uncertainty, and its effect on the original
   work.
6. Return to the prior workflow at the exact decision point; do not restart it.

Do not turn every uncertainty into a teaching detour. Use source inspection or
`implement-slice` research when the missing fact is narrow and operational.
