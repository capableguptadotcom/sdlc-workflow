---
name: implement-slice
description: Implement one approved vertical slice with tests, safe integration, and deterministic evidence. Use when a specification and plan identify a bounded increment to build. Do not use for an unspecified whole feature, speculative refactoring, or production operations.
---

# Implement slice

## Establish the seam

1. Read the slice, acceptance criterion, nearby code, tests, and conventions.
2. Confirm the observable boundary where behavior can be tested.
3. For untested legacy behavior, add a characterization test before changing it
   when feasible.
4. For unfamiliar or version-sensitive APIs, inspect the installed version and
   primary documentation. Record material sources in the plan or verification
   artifact; do not rely on model memory.

## Build the increment

1. Add or adjust a failing test at the behavioral seam when a reliable test is
   practical.
2. Make the smallest change that satisfies the slice.
3. Keep incomplete behavior behind a safe default or feature flag when it could
   affect users.
4. Integrate across boundaries inside the same slice; do not leave an untested
   layer for a later integration phase.
5. Run focused checks, then the configured affected-scope checks.
6. Update the task and acceptance-evidence mapping.

Do not weaken tests to fit the implementation, silently broaden scope, add a
dependency without justification, or commit automatically.
