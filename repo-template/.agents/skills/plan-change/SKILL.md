---
name: plan-change
description: Convert an accepted feature specification into dependency-aware, testable vertical slices and verification tasks. Use when requirements and acceptance criteria are stable enough to plan implementation. Do not use to compensate for an unclear specification or to produce layer-only task lists.
---

# Plan change

1. Read the accepted spec, relevant architecture, code seams, tests, and project
   commands.
2. Identify the smallest tracer slice that crosses the necessary boundaries and
   proves the architecture with observable behavior.
3. Decompose the remaining work into vertical slices. Each slice must name:
   - behavior delivered;
   - acceptance criteria addressed;
   - code seams likely to change;
   - deterministic verification;
   - dependencies and human review points.
4. Use expand-contract for compatibility-sensitive changes. Include safe
   defaults, feature flags, migration order, and rollback when applicable.
5. Put risky unknowns into bounded research or prototype tasks that answer one
   question. Do not disguise open design decisions as coding tasks.
6. Create `plan.md`, `tasks.md`, and `verification.md` in the feature folder
   using the repository templates.

Reject plans that organize work only by database/backend/frontend layers, rely
on a final integration phase, or cannot demonstrate progress after each slice.
