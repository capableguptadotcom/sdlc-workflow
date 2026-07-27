---
name: simplify-change
description: Simplify recently changed code while preserving observable behavior and public contracts. Use after correctness and relevant deterministic checks pass, when the diff contains unnecessary indirection, duplication, branching, or abstraction. Do not use for broad architecture redesign, speculative cleanup, or behavior changes.
---

# Simplify change

1. Limit scope to the current diff and the smallest surrounding context needed
   to understand it.
2. State the behavior, contracts, and tests that must remain unchanged.
3. Before removing an unusual construct, inspect its history or callers and
   explain the problem it solves.
4. Prefer deletion, direct control flow, existing helpers, and local names over
   new abstractions.
5. Remove duplication only when the shared concept is stable; do not unify code
   that merely looks similar.
6. Make one coherent simplification at a time and rerun focused checks.
7. Compare the final diff with the verified pre-simplification behavior.

Return changes made, behavior preserved, commands run, and opportunities
declined because their risk or scope exceeded this review.
