---
name: develop
description: Orchestrate a repository change from intent through verified vertical slices. Use when the user explicitly invokes develop or asks for end-to-end implementation of new or changed behavior. Do not use for explanation-only, review-only, diagnosis-only, operations, or a trivial non-behavioral edit.
---

# Develop

Own the end-to-end change while keeping each phase explicit and reviewable.

## Route the work

1. Read `AGENTS.md`, `ai-sdlc.yaml`, relevant code, tests, and existing specs.
2. Classify risk and decide whether the change needs a feature folder.
3. If intent or acceptance evidence is unclear, follow
   `../shape-change/SKILL.md` before planning.
4. If a specification exists but executable slices do not, follow
   `../plan-change/SKILL.md`.
5. Follow `../implement-slice/SKILL.md` for one slice at a time.
6. After every slice, run the smallest relevant deterministic checks and map
   evidence to its acceptance criterion.
7. Stop at a human decision boundary, a failed invariant, or a material scope
   change. Do not silently redesign the accepted specification.

## Completion contract

Return:

- behavior delivered;
- specification and criteria addressed;
- deterministic commands and results;
- files changed;
- unresolved decisions, risks, and next slice.

Do not commit, push, deploy, publish, or mutate an external tracker unless the
user explicitly asks.
