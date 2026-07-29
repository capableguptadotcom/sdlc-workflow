---
name: shape-change
description: Turn an ambiguous feature, behavior change, domain problem, or consequential unresolved choice into shared, testable intent. Use when outcomes, actors, policy, scenarios, constraints, terminology, failure behavior, acceptance, or one durable trade-off is unclear. Do not use when an accepted specification already answers the questions, for routine implementation choices, or for implementation-only work.
---

# Shape change

Build shared understanding before implementation.

## Investigate first

- Read relevant code, tests, product docs, incidents, existing specifications,
  configured context, and relevant ADRs.
- Answer repository facts by inspection instead of asking the user.
- Separate established facts, assumptions, and human decisions.
- Separate the user's desired outcome from a proposed implementation.
- Detect whether the request follows, extends, conflicts with, or replaces an
  accepted decision.
- Order unresolved decisions by dependency so later questions do not assume
  answers that have not been settled.

## Resolve decisions

Ask one material question at a time. For each question:

1. Explain the decision it affects.
2. State a recommendation and its trade-off.
3. Offer concrete scenarios or mutually exclusive choices when useful.
4. Record the decision before moving on.

Cover actors, starting state, action, observable result, invariants, failure and
recovery, compatibility, exclusions, and acceptance evidence. Challenge a
requested approach when evidence indicates a safer or simpler way to achieve
the outcome.

Own routine reversible engineering choices. When one unresolved question needs
external research, an experiment, or comparison of defensible perspectives,
read [decision-resolution.md](references/decision-resolution.md). These are
internal procedures, not commands the developer must know.

Add or update configured domain context only when a stable, project-specific
term is resolved. Keep it a glossary; do not put specifications or
implementation details in it.

Offer an ADR only when the decision is hard to reverse, surprising without its
context, and the result of a real trade-off. Use `.ai/templates/adr.md`. Keep a
new ADR `proposed` until explicit human acceptance. Supersede an accepted ADR
with a new ADR and update both status links atomically; never rewrite the
accepted historical body.

## Produce the specification

For a material behavior change, create `specs/<feature>/spec.md` and
`verification.md` from the templates. Keep design choices out unless they are
true constraints. Map every acceptance criterion to intended evidence. Mark
unresolved decisions instead of guessing.

Stop when the user and agent can independently describe the same scenarios and
acceptance criteria. Ask the human to review the draft. Only explicit
confirmation changes `status` to `accepted` and records `accepted_at` and
`accepted_via`.

Answers to discovery questions, “all decisions are settled,” or an earlier
request to take work end to end are not acceptance of a specification the
human has not yet reviewed. After producing or materially revising a draft,
show the contract and stop at its review boundary. A new specification's
creation turn ends with `status: draft`; changing `draft` to `accepted`
requires a later explicit human message that refers to the rendered contract.
Do not mark it accepted, plan, or implement in the creation turn.

A material edit to accepted behavior, scope, criteria, invariants, failure
policy, or risk returns the spec to `draft`, pauses affected implementation,
and requires downstream plan, task, and evidence reconciliation. Do not
implement from this skill.
