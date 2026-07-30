# AI Developer Kit

This repository contains a governed, cross-agent starter kit for AI-assisted
software development. It is the source of the shared kit, not a second
repository that every developer must clone.

Open the
[interactive workflow walkthrough](repo-template/.ai/workflow-walkthrough.html)
for scenario-based tutorials, example prompts, routing visuals, artifact
guidance, and a short team practice checklist. The adopter ships this page into
each project so the team receives it through the normal repository workflow.

For the complete evidence-backed guide—from isolated first adoption through the
Pantry Ledger lifecycle, model architecture, release operations, rollback, and
the pain points that shaped alpha.4—open [tutorial.html](tutorial.html).

## Team adoption: no extra clone

The intended distribution flow is:

1. One repository maintainer runs a single adoption command in an existing
   project.
2. The command inspects the project, previews the proposed merge, and asks for
   confirmation before changing files.
3. The maintainer reviews and commits the installed repository contract.
4. Everyone else receives it through the project's normal clone or pull.
5. AI assistants read the committed `AGENTS.md`, skills, and project context
   directly from that project.

The command distinguishes first adoption from same-version validation.
First adoption supports a clean Git worktree with no existing kit lock,
previews the complete payload, requires confirmation, verifies the installed
payload hashes, and records `.ai/kit.lock.json`.
Existing `AGENTS.md`, `CLAUDE.md`, and Copilot instructions are preserved and
receive one clearly marked `ai-sdlc-workflow` region. The lock tracks only that
region as shared ownership. Missing, duplicated, or changed markers and all
other same-path collisions stop without changing files.

Re-running the same kit version is a read-only integrity check: it validates
every lock-recorded kit-owned file and shared managed region, while leaving
project-owned files such as `ai-sdlc.yaml` alone. A missing or changed managed
unit fails validation and lists the affected path. Installing a different kit
version and updating an installed kit remain out of scope for this alpha.

The adopter maps recognized existing `package.json` scripts and explicit
Python tool sections from `pyproject.toml` into `ai-sdlc.yaml`. It uses script
names such as `lint`, `typecheck`, `test:unit`, and `build`, plus configured
Ruff, Black, Mypy, Pytest, and Bandit tools. Mixed repositories receive command
arrays for both ecosystems. Absent or ambiguous roles remain empty; the
adopter never asks whether the repository is frontend or backend.

Pre-commit composition is intentionally conservative. An existing Husky hook
receives a managed region only when the project defines an explicit
`precommit`, `pre-commit`, or `lint:staged` script. An existing Python
`.pre-commit-config.yaml` remains the project source of truth. When both
managers exist, the adopter preserves both and skips composition to avoid
running checks twice. It never installs a hook manager or promotes generic
format, lint, test, typecheck, build, security, or AI commands into pre-commit.

The kit does not ship `.claudeignore`, `.codexignore`, or `.copilotignore`
files. They are not a consistent cross-agent contract. Use `.gitignore` for
generated repository noise, concise scoped instructions for focus, and each
host's permissions or sandbox only for genuine sensitive-path enforcement.

## Install the published alpha

The public alpha is live as `@innovate-x/ai-sdlc`. Before adopting it, install
Node.js 22 or newer and Git, run the command from the root of an existing Git
repository, and commit the current project so the worktree is clean. A dirty
worktree can be previewed, but the installer will not apply changes.

A repository maintainer adopts the kit with:

```bash
npx @innovate-x/ai-sdlc@alpha
```

Installing the repository kit is separate from installing and authenticating
an AI assistant. The adoption command does not install Codex or another
assistant, create an account, or sign it in. Set up and authenticate the
assistant through its own supported flow before using the committed guidance.

After confirmation, the installer re-reads the files it owns and compares
their SHA-256 hashes with the release payload. That verifies the installation
write; it does not run the repository's structural validator or project
commands. Review the Git diff and detected command mapping, then explicitly
run:

```bash
python scripts/validate_ai_kit.py
```

Run the applicable project checks listed in `ai-sdlc.yaml`, then commit the
reviewed adoption. Re-running the same published version performs the
lock-based read-only validation described above without prompting or writing.
For a repository that publishes an artifact, also inspect the real package
manifest (for example, `npm pack --dry-run --json`). Adoption adds internal
workflow files; use the project's existing `files` or ignore policy to decide
whether they belong in the published artifact.

For installer development against this checkout, a maintainer can run:

```bash
npm install
npm test
npm run build
cd /path/to/project
node /absolute/path/to/sdlc-workflow/dist/cli.js
```

For an exceptional pilot that cannot run the published CLI, one maintainer may
still apply a reviewed kit snapshot manually and complete `.ai/ADOPTION.md`:

```bash
cp -R repo-template/. /path/to/project/
```

This manual copy is a temporary maintainer task, not team onboarding. Run it
from a reviewed kit release, inspect the resulting Git diff, and merge existing
project commands and policies instead of overwriting them.

## Isolation and live evaluation

A disposable container with Node.js 22 or newer and Git is useful for testing
first adoption against a clean, committed fixture without contaminating a
developer worktree. The small executable behavior evaluator uses the locally
signed-in Codex session on the host by default; CI uses its fake-agent path for
deterministic coverage.

The Pantry Ledger full-lifecycle simulation has a stricter verified topology:
the complete harness and live assistant run inside a disposable container,
with the kit source and authentication input read-only and only the scenario
workspace/evidence mount writable. See
[`simulations/pantry-ledger/README.md`](simulations/pantry-ledger/README.md)
and its retained runbook. Keep authentication out of generic adoption-only
containers and never copy it into retained evidence.

The design has four rules:

1. `AGENTS.md` is the durable repository contract.
2. `.agents/skills/` is the single canonical skill source.
3. Agent-specific files are thin adapters, not independent copies.
4. Deterministic checks and repository evidence enforce quality; skill use
   itself is never treated as proof.

Read `governance/OPERATING_MODEL.md` before changing the baseline. Read
`research/SKILL_AUDIT.md` before importing another community skill.

## Layout

- `repo-template/` — the install payload for an adopted project.
- `governance/` — lifecycle, quality bar, ownership, and update policy for the
  shared kit.
- `research/` — source-by-source audit, inclusion decisions, pinned candidates,
  and initial evaluation results.
- `scripts/` — checks used by the shared kit repository.

The template deliberately contains three memorable front doors—`develop`,
`finish`, and `learn`—plus narrower skills that those workflows route to. It is
not an instruction to invoke every skill on every change.

Invocation syntax varies by agent: Claude exposes the adapters as `/develop`,
`/finish`, and `/learn`; other Agent Skills-compatible tools may use a skill
picker, `$develop`, or a natural-language request to use the named skill.

## Maintainer checks

The repository uses only the Python standard library for its current
validation:

```bash
python -m unittest discover -s tests -v
python repo-template/scripts/render_walkthrough.py --check
python repo-template/scripts/validate_ai_kit.py
```

CI runs the same commands. The validator warning about empty command lists is
expected in the shared template; adopted repositories must map their real
commands.

## Executable behavior evaluations

Maintainers can run one workflow scenario against an isolated copy of the
`brownfield-mini` fixture:

```bash
python scripts/run_behavior_evals.py \
  --scenario repository-overview \
  --output-dir artifacts/behavior-evals/repository-overview
```

The runner currently defines five high-value boundaries: repository overview,
tiny change, fuzzy-feature first turn, diagnosis-only, and finish-before-commit.
It records the structured agent result, filesystem changes, and local commit
state, then evaluates them against `repo-template/evals/executable-cases.json`.

The default live model is `gpt-5.6-terra`. Override it with `--model` or
`AI_SDLC_EVAL_MODEL`. If the installed CLI is behind the selected model, add
`--codex-package-version <version>` to run a reviewed CLI version through
`npx` without replacing the global installation. A live run consumes the
signed-in Codex account's allowance and is intentionally not part of CI. CI
runs the same public runner against a fake agent process so isolation and
safety assertions remain deterministic.

Add `--all-turns` to the fuzzy-feature scenario to preserve the task after its
first product question, provide the decision, and evaluate the resulting draft
specification and verification contract:

```bash
python scripts/run_behavior_evals.py \
  --scenario fuzzy-team-invitations \
  --all-turns \
  --output-dir artifacts/behavior-evals/fuzzy-team-invitations
```

The deterministic harness verifies resumed prompt delivery, sandbox selection,
required and forbidden file changes, commit state, and the final human gate.
On the current Windows test environment, Codex CLI `0.145.0` preserves the
conversation but resumes it with read-only filesystem access despite the
requested `workspace-write` sandbox. The live scenario therefore fails
accurately on its two missing draft files; the harness does not treat that
blocked state as success.
