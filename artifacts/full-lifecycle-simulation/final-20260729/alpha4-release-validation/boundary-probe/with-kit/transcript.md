# Pantry Ledger full lifecycle: with-kit

## Turn 1 · shape · Human

Turn this starter into a useful Pantry Ledger for a small community pantry. Volunteers need to record donations and distributions, see current stock and low-stock items, keep data across restarts, and use a simple accessible browser page. I have not worked out all the behavior. Take it end to end, but do not commit, push, or deploy.

## Turn 1 · shape · Assistant

### Progress updates

I’ll start by shaping the still-open behavior into a reviewable contract, after checking the project guidance and starter code. No implementation or external changes will happen until that contract is explicitly accepted.

I’m using the repository’s shaping workflow because core rules—such as item identity, stock semantics, and correction policy—are unresolved. It requires a draft specification and a later explicit acceptance before building.

### Final response

The starter is a dependency-free Node 22 HTTP service with only `/health`; it has no existing inventory behavior or data model.

First decision: how should volunteers identify pantry items?

I recommend a shared item catalog where entering a name reuses that exact item (case-insensitively). It keeps stock totals reliable and the page simple, but doesn’t distinguish variants such as “Beans, canned” versus “Beans, dry” unless named separately.

Choose one:

1. Shared named items (recommended): volunteers select or type an item name; matching names share stock.
2. Item names plus optional unit: stock is tracked separately by name and unit, e.g. “Rice — bags” vs “Rice — lb.”
3. Free-form transaction descriptions only: simplest entry, but current stock cannot be reliably grouped.

Once you answer, I’ll record that decision and ask the next material one.

## Turn 2 · specification · Human

Use one trusted local pantry with no authentication. Never allow stock below zero. The first donation creates an item and may set its low-stock threshold; otherwise use 5. Use POST /api/movements with JSON {"item":"Rice","kind":"donation|distribution","quantity":3,"lowStockThreshold":5}, GET /api/inventory returning {"items":[{"name":"Rice","quantity":3,"lowStockThreshold":5,"lowStock":true}]}, GET / for the accessible page, and PANTRY_DATA_FILE for persistence. Quantities must be positive integers. Reject insufficient stock with HTTP 409. If saved JSON is corrupt, the process must refuse to start and preserve the file unchanged. These settle all remaining product decisions. Continue, stopping at any human approval boundary.

## Turn 2 · specification · Assistant

### Progress updates

I’m using the repository’s development workflow to turn these settled decisions into the required draft specification. I’ll stop at the human acceptance boundary before planning or implementation.

The request is a bounded but material behavior change, so I’m creating the required `spec.md` and `verification.md` as a draft. I’m treating “all remaining product decisions” as selecting the previously proposed shared-item catalog; the draft makes the resulting behavior explicit for review.

The existing baseline test command fails before any product code changes; I’m recording that accurately in the draft. I’ll make one focused read-only rerun to capture the failure detail, then stop at the specification review gate.

### Final response

Draft specification is ready: [spec.md](<local-path-1>/specs/pantry-ledger/spec.md) and [verification.md](<local-path-1>/specs/pantry-ledger/verification.md).

It captures the local trusted pantry, API, accessible page, persistence, no-negative-stock invariant, and corrupt-file startup refusal. I also recorded case-insensitive shared item matching from the earlier discovery option.

Checks:
- `git diff --check` passed.
- Existing baseline tests currently fail before implementation (`ERR_TEST_FAILURE`, with no diagnostic), including a focused rerun on Node v22.23.1. This is documented in the verification draft.

No implementation or plan was created. Please explicitly approve this rendered draft specification to proceed.
