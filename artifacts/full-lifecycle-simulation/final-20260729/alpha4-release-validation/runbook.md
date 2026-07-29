# Alpha.4 release reproduction

This runbook reproduces the release gates for the immutable
`@innovate-x/ai-sdlc@0.1.0-alpha.4` candidate. Run commands from the repository
root. Publishing is intentionally separate from verification.

## Source gates

```powershell
npm ci
npm test
python -B -m unittest discover -s tests -v
python -B repo-template/scripts/validate_ai_kit.py
python -B repo-template/scripts/render_walkthrough.py --check
npm audit --omit=dev
git diff --check
```

Expected totals are 33 Node tests, 66 Python tests, 13 skills, 35 routing
cases, 25 behavior cases, 12 dialogue cases, six walkthrough scenarios, and
zero audit vulnerabilities.

## Candidate identity

```powershell
$candidate = "artifacts/full-lifecycle-simulation/candidate-package/alpha.4-runtime-cleanup/innovate-x-ai-sdlc-0.1.0-alpha.4.tgz"
$actual = (Get-FileHash -Algorithm SHA256 $candidate).Hash.ToLowerInvariant()
$expected = "9bd25aeb8b04f390db4451a69d1890039cf8bf27099b68b8e82a6e403fb91b8f"
if ($actual -ne $expected) { throw "Candidate hash mismatch: $actual" }
```

Repacking the same checkout must produce the same SHA-256, 65 entries, 79,997
packed bytes, and 306,537 unpacked bytes.

## Offline adoption

Use the retained tooling image
`ai-sdlc-tooling:node22-python3-20260729`, whose verified image ID is
`sha256:604eae0fd280e6e8cb2d0ce82e8837c4053c5f70759415db564f72cb588b5696`.
Mount a fresh committed copy of `tests/fixtures/pantry-ledger-seed` at
`/workspace` and the candidate directory read-only at `/candidate`:

```bash
set -euo pipefail
npm install --global --ignore-scripts \
  /candidate/innovate-x-ai-sdlc-0.1.0-alpha.4.tgz
ai-sdlc --dry-run
test ! -e .ai/kit.lock.json
ai-sdlc --yes
python3 -B scripts/validate_ai_kit.py
npm test
git diff --check
```

Run the same `ai-sdlc --yes` command again and compare file hashes before and
after. The retained evidence shows no byte changes. Docker networking must be
disabled for this gate.

## Live lifecycle

The full model simulation needs network access for Codex, but all work occurs
inside a disposable container. Mount this repository read-only at `/kit`, an
empty evidence directory read/write at `/results`, and the existing Codex
authentication file read-only at the container's configured authentication
location.

```bash
python3 -B /kit/scripts/run_lifecycle_simulation.py \
  --arm both \
  --output-dir /results/full-run \
  --model gpt-5.6-terra \
  --codex-package-version 0.145.0 \
  --kit-package /kit/artifacts/full-lifecycle-simulation/candidate-package/alpha.4-runtime-cleanup/innovate-x-ai-sdlc-0.1.0-alpha.4.tgz \
  --sandbox danger-full-access \
  --isolation-image node@sha256:5647be709086c696ff32edaaf1c70cd26d1da6ab2b39c32f3c7b4c4a31957e37
```

`danger-full-access` is limited to the disposable container; the inner
workspace needs local Git writes and loopback listeners. The authoritative
with-kit result completed 10 turns, 69 command attempts, zero interrupted
commands, three authorized commits, product acceptance, clean-checkout tests,
operations, rollback, retirement, and lifecycle invariants.

Model output is stochastic. Compare controlled input hashes in
`verification.json`; do not expect a byte-identical transcript.

## Independent offline replay

Mount the retained `operations_handoff` and `initial_release` checkouts
read-only into the tooling container with `--network none`, then run:

```bash
node /kit/scripts/pantry_ledger_acceptance.mjs /current --mode full
node /kit/scripts/pantry_ledger_rollback_acceptance.mjs /current /previous
```

Both commands must report `"passed": true`, and every spawned server must be
stopped before the command exits.
