# Operating model

## Recommendation

Maintain one versioned **AI Developer Kit** repository. Projects consume a
released snapshot through an ordinary update pull request. Do not let every
project independently install and modify the same community skills.

The model has three scopes:

| Scope | Owns | Evolves when |
| --- | --- | --- |
| Organization kit | Shared workflow contracts, canonical skills, adapters, evaluations, provenance | A recurring problem or upstream improvement is proven across projects |
| Project root | Commands, architecture constraints, risk policy, local exceptions | A stable fact about that repository changes |
| Subtree | Commands or constraints true only below that directory | A genuine package or subsystem difference exists |

`AGENTS.md` belongs at the project root. Keep it short, durable, and specific to
the repository. Create a nested `AGENTS.md` only for a real subtree override;
do not distribute a copy into every folder. `CLAUDE.md` and Copilot instructions
are compatibility adapters, not separate policy documents.

## One canonical skill, several entry points

| Consumer | Entry point | Policy source |
| --- | --- | --- |
| Codex and Agent Skills-compatible agents | `.agents/skills/<name>/SKILL.md` | Canonical |
| Claude Code | `.claude/commands/<name>.md` | Thin adapter that reads the canonical skill |
| GitHub Copilot | `.agents/skills/` plus `.github/copilot-instructions.md` | Canonical skill and pointer to `AGENTS.md` |

Never keep two editable active copies. Symlinks work in some agents but are
fragile in archives, Windows environments, and tools that materialize files;
small text adapters are easier to review.

## Skill lifecycle

1. **Collect evidence.** Open a candidate only for recurring friction, repeated
   review feedback, a costly failure, or a missing stable workflow.
2. **Sandbox the source.** Review it outside the active discovery directories.
   Record repository, exact commit, license, files, scripts, and network or
   mutation behavior.
3. **Classify it.** Identify one purpose, positive trigger, negative trigger,
   overlap, authorization boundary, and required evidence.
4. **Choose a strategy.** Use an unmodified mirror only when the source is
   narrow, correct, licensed, and already matches team policy. Otherwise write
   a team-owned derived skill and retain provenance. Reject concepts that add
   no distinct decision or procedure.
5. **Evaluate it.** Run positive and negative routing cases plus behavior cases
   that test safety, evidence, and output quality. Compare it with the current
   baseline on the same tasks.
6. **Review a PR.** Include the source diff, rubric, evaluation results,
   migration impact, adapters, and rollback plan.
7. **Release the kit.** Version the baseline and update projects through normal
   PRs. A project may defer a release with an explicit reason.
8. **Observe and prune.** Track false triggers, missed triggers, review value,
   failures, and maintenance cost. Merge or remove skills that no longer earn
   their place.

## Upstream updates

`.ai/skills.lock.json` records the exact commits used as provenance anchors.
The read-only update checker reports movement on an upstream default branch; it
does not replace local files.

For an update:

1. compare the reviewed commit with the candidate commit;
2. inspect source, dependencies, license, scripts, and behavioral changes;
3. port only improvements that still fit the team-owned purpose;
4. rerun routing and behavior evaluations;
5. merge through review and advance the pinned commit.

Use `npx skills` for discovery or a temporary evaluation workspace. If the
GitHub CLI skill preview is available, an exact tag or commit can make that
workspace reproducible. Neither command should update the organization
baseline to `latest`, run from a Git hook, or overwrite a derived skill. The
source project remains upstream; the reviewed organization behavior remains
the product.

If legal or audit needs require a source snapshot, store it under a
non-discoverable `vendor/` path with its license. Do not activate both the
snapshot and the derived skill.

## Enforcement and learning

- Pre-commit and pre-push run deterministic, local checks only.
- CI and protected branches enforce required tests, policy, and evidence.
- A statement that a skill ran is not evidence that a change is correct.
- Networked AI review is advisory unless a repository explicitly defines a
  stable policy gate with deterministic inputs and a human appeal path.
- Every guidance PR names the observed problem and adds or updates an example
  that would have caught it.

Suggested owners are one kit maintainer, one security reviewer for high-risk
changes, a UI/accessibility reviewer for UI profiles, and rotating project
representatives. Review the baseline quarterly and immediately after a costly
guidance-related incident.
