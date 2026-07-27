---
name: shape-change
description: Turn an ambiguous feature, behavior change, or domain problem into a shared, testable specification. Use when outcomes, actors, scenarios, constraints, terminology, failure behavior, or acceptance criteria are unclear. Do not use when an accepted specification already answers those questions or for implementation-only work.
---

# Shape change

Build shared understanding before implementation.

## Investigate first

- Read relevant code, tests, product docs, incidents, and existing specifications.
- Answer repository facts by inspection instead of asking the user.
- Create a small domain glossary when the same term may mean different things.
- Separate the user's desired outcome from a proposed implementation.

## Interview

Ask one material question at a time. For each question:

1. Explain the decision it affects.
2. State a recommendation and its trade-off.
3. Offer concrete scenarios or mutually exclusive choices when useful.
4. Record the decision before moving on.

Cover actors, starting state, action, observable result, invariants, failure and
recovery, compatibility, exclusions, and acceptance evidence. Challenge a
requested approach when evidence indicates a safer or simpler way to achieve
the outcome.

## Produce the specification

Create `specs/<feature>/spec.md` from `specs/_template/spec.md`. Keep design
choices out unless they are true constraints. Mark unresolved decisions rather
than filling them with guesses.

Stop when the user and agent can independently describe the same scenarios and
acceptance criteria. Do not implement from this skill.
