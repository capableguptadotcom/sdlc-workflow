# Skill quality rubric

Score each axis `0` (unacceptable), `1` (usable with material gaps), or `2`
(strong). A default skill needs at least **13/16**, with no zero for scope,
safety, correctness, or verification. A profile skill needs at least **12/16**
and an explicit owner. Scores guide judgment; they do not replace evaluation.

| Axis | A score of 2 means |
| --- | --- |
| Distinct purpose | It owns one recurring decision or procedure that is not already covered |
| Trigger precision | Description states observable positive and negative triggers and routes cleanly |
| Procedure quality | Steps are executable, ordered, bounded, and use progressive disclosure |
| Correctness | Claims are current, contextual, source-backed where necessary, and avoid false absolutes |
| Safety and authority | Read/write boundaries, risky operations, untrusted input, and stop conditions are explicit |
| Evidence and verification | It requires deterministic checks or concrete artifacts appropriate to its claims |
| Portability | Canonical instructions are vendor-neutral; adapters contain vendor syntax |
| Maintenance value | Expected benefit exceeds overlap, token cost, dependencies, and update burden |

## Status gates

| Status | Meaning | Promotion requirement |
| --- | --- | --- |
| Rejected | Unsafe, duplicative, incorrect, or not valuable enough | Reframe the purpose and repeat the audit |
| Experimental | Plausible but evidence is incomplete | Named owner, bounded users, and collected evaluations |
| Profile | High quality for a particular stack or discipline | Project opts in and provides required tools |
| Core | Broad, stable, and proven across projects | Passing rubric and behavior/routing evidence |

## Required evaluation set

Every enabled skill needs:

- at least two prompts that should trigger it;
- at least two near-neighbor prompts that should not trigger it;
- one behavior task that tests its output contract;
- one safety or authorization task when it can edit or operate;
- a regression case for every confirmed false trigger, missed trigger, or
  harmful behavior.

Evaluate the selected skill, the non-selected alternatives, and the result—not
just whether the expected name appeared. Prefer blind comparison against the
current baseline for subjective UI or writing skills.

## Removal test

At each review ask: “What concrete failure becomes more likely if we remove
this skill?” If the answer is indistinguishable from another skill, merge them.
If there is no observed answer after two review cycles, remove it from the
default pack.
