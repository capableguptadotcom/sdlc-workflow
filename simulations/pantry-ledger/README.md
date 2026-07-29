# Pantry Ledger lifecycle simulation

This scenario compares the same committed Node.js seed with and without the AI
SDLC kit. The product is intentionally small enough to finish but broad enough
to exercise requirements, specifications, planning, domain behavior,
persistence, HTTP input, an accessible UI, deterministic checks, incident
diagnosis, learning/handoff, maintenance, and a local release gate.

Each live turn uses an isolated repository workspace and replays the redacted
conversation into a fresh ephemeral Codex session. The verified topology runs
the complete harness inside a disposable Linux container with the kit source
read-only, one evidence directory writable, and the existing Codex
authentication file mounted read-only. This avoids contaminating the host and
works around the observed Codex 0.145.0 Windows resume/sandbox regression.

The harness itself does not create a container. `--isolation-image` records
provenance only; the caller is responsible for launching the harness inside
that image. See the
[reproduction runbook](../../artifacts/full-lifecycle-simulation/final-20260729/runbook.md)
for the exact verified container commands and mount boundary.

For a host-only, one-turn development probe, run both arms after building the
adopter:

```powershell
npm run build
python scripts/run_lifecycle_simulation.py `
  --arm both `
  --turn-limit 1 `
  --sandbox workspace-write `
  --model gpt-5.6-terra `
  --codex-package-version 0.145.0 `
  --output-dir "<empty-output-directory>"
```

The output contains retained workspaces, path-redacted raw model events, a
self-contained Markdown/JSONL transcript, per-turn Git and command evidence,
and a paired comparison report.

The full run also invokes local HTTP services and creates authorized Git
commits. It therefore requires an explicit `--sandbox danger-full-access`, used
only inside the disposable container topology in the runbook. Do not grant that
sandbox to the host run, and do not present a host-only or turn-limited probe as
isolated full-lifecycle evidence.
