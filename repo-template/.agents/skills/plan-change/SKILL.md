---
name: plan-change
description: Convert an accepted specification into a dependency-aware implementation plan when multiple slices, migration, compatibility, rollout, or material risk warrants explicit ordering. Use when accepted behavior is stable but technical sequencing and gates need review. Do not use for a clear single-slice change, to compensate for an unclear specification, or to produce layer-only task lists.
---

# Plan change

1. Confirm the spec is `accepted`. Read it with relevant ADRs, architecture,
   code seams, tests, project commands, and existing verification design.
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
6. Create `plan.md` from the template. Keep it `draft` until the human accepts
   material risk, rollout, dependency, external-effect, and review gates.
7. Create `tasks.md` only when repository-local tasks are the chosen source of
   truth. When a configured external tracker is used, create independently
   assignable tickets only after explicit authorization; do not duplicate them
   locally.

Reject plans that organize work only by database/backend/frontend layers, rely
on a final integration phase, or cannot demonstrate progress after each slice.
A material change to risk, rollout, dependencies, external effects, or human
gates returns an accepted plan to `draft`, pauses execution, and reconciles
downstream tasks.
