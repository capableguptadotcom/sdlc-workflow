# AI Developer Kit

This repository contains a governed, cross-agent starter kit for AI-assisted
software development. It is the source of the shared kit, not a second
repository that every developer must clone.

Open the
[interactive workflow walkthrough](repo-template/.ai/workflow-walkthrough.html)
for scenario-based tutorials, example prompts, routing visuals, artifact
guidance, and a short team practice checklist. The adopter ships this page into
each project so the team receives it through the normal repository workflow.

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

The same command will later detect whether it should install, validate, or
preview an update. Developers should not need separate commands or knowledge
of this kit's internal repository.

The command now has a local first-adoption alpha. It supports a clean Git
worktree with no existing kit lock, previews the complete payload, requires
confirmation, validates written hashes, and records `.ai/kit.lock.json`.
Existing `AGENTS.md`, `CLAUDE.md`, and Copilot instructions are preserved and
receive one clearly marked `ai-sdlc-workflow` region. The lock tracks only that
region as shared ownership. Missing, duplicated, or changed markers and all
other same-path collisions stop without changing files. Updating an installed
kit remains a later increment.

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

The public alpha release target is `@innovate-x/ai-sdlc`. After the first
release is published, a repository maintainer will adopt it with:

```bash
npx @innovate-x/ai-sdlc@alpha
```

Until that release is published, a maintainer can test the command from this
repository:

```bash
npm install
npm test
npm run build
cd /path/to/project
node /absolute/path/to/sdlc-workflow/dist/cli.js
```

For a one-or-two-repository pilot that cannot run the local CLI, one maintainer
may still apply a reviewed kit snapshot manually and complete
`.ai/ADOPTION.md`:

```bash
cp -R repo-template/. /path/to/project/
```

This manual copy is a temporary maintainer task, not team onboarding. Run it
from a reviewed kit release, inspect the resulting Git diff, and merge existing
project commands and policies instead of overwriting them.

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
