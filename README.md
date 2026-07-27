# AI Developer Kit

This repository contains a governed, cross-agent starter kit for AI-assisted
software development. Copy the contents of `repo-template/` into a project
root, then complete the adoption checklist in `.ai/ADOPTION.md`.

```bash
cp -R repo-template/. /path/to/project/
```

Run that command from a reviewed kit release and inspect the resulting Git diff
before accepting it. Existing project commands and policies must be merged, not
blindly overwritten.

The design has four rules:

1. `AGENTS.md` is the durable repository contract.
2. `.agents/skills/` is the single canonical skill source.
3. Agent-specific files are thin adapters, not independent copies.
4. Deterministic checks and repository evidence enforce quality; skill use
   itself is never treated as proof.

Read `governance/OPERATING_MODEL.md` before changing the baseline. Read
`research/SKILL_AUDIT.md` before importing another community skill.

## Layout

- `repo-template/` — copy these contents into a project root.
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
