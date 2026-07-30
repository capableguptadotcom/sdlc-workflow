# AI SDLC

AI SDLC installs a governed, cross-agent development workflow into an existing
Git repository. It gives AI assistants durable project instructions, focused
skills, progressive specifications, and deterministic quality gates.

It does not install or authenticate an AI assistant. Set up Codex, Claude, or
another compatible assistant separately.

## Quick start

Requirements: Node.js 22 or newer, Git, and a clean committed worktree.

```bash
# Preview without writing
npx @innovate-x/ai-sdlc@alpha --dry-run

# Adopt the workflow
npx @innovate-x/ai-sdlc@alpha --yes

# Validate the installed kit
python scripts/validate_ai_kit.py
```

Review the generated diff and the project commands detected in
`ai-sdlc.yaml`, run those commands, then commit the adoption. Everyone else
receives the workflow through the normal repository clone or pull—no separate
kit checkout is required.

Re-running the same package version performs a read-only integrity check.

## Use it

Describe work normally. The assistant routes through three entry points:

- `develop` — orient, shape, plan when needed, implement, and verify.
- `finish` — run relevant checks, review the diff, and report limitations.
- `learn` — pause for contextual teaching, preserve a handoff, then resume.

Invocation syntax depends on the assistant: Claude uses `/develop`, `/finish`,
and `/learn`; Agent Skills-compatible tools may use `$develop`, a skill picker,
or an explicit natural-language request.

## Read next

- [Complete field guide](tutorial.html) — isolated adoption, real lifecycle
  transcript, examples, results, OpenAI model architecture, operations, and
  rollback.
- [Installed workflow walkthrough](repo-template/.ai/workflow-walkthrough.html)
  — concise scenario-based team practice.
- [Adoption checklist](repo-template/.ai/ADOPTION.md) — repository setup and
  ownership review.
- [Operating model](governance/OPERATING_MODEL.md) — maintenance, governance,
  and release policy.
- [Skill audit](research/SKILL_AUDIT.md) — provenance and inclusion decisions.

## Current alpha boundary

The public release is
[`@innovate-x/ai-sdlc@0.1.0-alpha.4`](https://www.npmjs.com/package/@innovate-x/ai-sdlc/v/0.1.0-alpha.4).
It is intended for fresh-adoption pilots.

Cross-version updates are not supported. If a repository already contains a
different kit version in `.ai/kit.lock.json`, the installer stops without
writing. Test alpha.4 in a fresh branch or repository instead.

For repositories that publish artifacts, inspect the real package manifest
after adoption—for example, `npm pack --dry-run --json`—and intentionally
include or exclude internal workflow files.

## Maintainers

```bash
npm ci
npm test
python -B -m unittest discover -s tests -v
python -B repo-template/scripts/validate_ai_kit.py
python -B repo-template/scripts/render_walkthrough.py --check
```

Lifecycle simulation and release reproduction instructions are in
[`simulations/pantry-ledger/README.md`](simulations/pantry-ledger/README.md)
and the
[`alpha.4 runbook`](artifacts/full-lifecycle-simulation/final-20260729/alpha4-release-validation/runbook.md).

License: [MIT](LICENSE).
