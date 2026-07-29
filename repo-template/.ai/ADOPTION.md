# Adoption checklist

Complete this once when adopting the kit into a repository.

- [ ] Confirm Node.js 22 or newer and Git are installed, and begin from a clean,
      committed worktree.
- [ ] Review the install diff and the detected command mapping before committing
      the adoption.
- [ ] Fill every applicable command list in `ai-sdlc.yaml`.
- [ ] Replace generic project assumptions in `AGENTS.md` with proven local
      constraints; keep the workflow and authorization rules.
- [ ] Run `python scripts/validate_ai_kit.py`.
- [ ] Run every applicable project check configured in `ai-sdlc.yaml`.
- [ ] If the repository publishes an artifact, inspect its actual manifest
      (for example, `npm pack --dry-run --json`) and intentionally include or
      exclude AI workflow files with the project's existing packaging rules.
      A successful pack command alone does not prove that internal guidance,
      specs, evals, or handoffs are safe to publish.
- [ ] Confirm `.ai/kit.lock.json` records the adopted `kit_version`, package,
      release digest, and managed-unit hashes; do not edit the lock manually.
- [ ] Re-run the same installer version and confirm its read-only lock
      validation reports no changes.
- [ ] Install and authenticate each supported AI assistant separately; the kit
      installer does not install or sign in to Codex or another assistant.
- [ ] Test `/develop`, `/finish`, and `/learn` in each supported agent.
- [ ] Run at least one positive and one negative trigger case for every enabled
      specialist skill.
- [ ] Configure deterministic local hooks separately from networked AI review.
- [ ] Add required CI checks and protected-branch rules.
- [ ] Assign owners for guidance, security, UI, and upstream skill review.
- [ ] Add the configured transient handoff path (default
      `artifacts/ai/handoffs/`) to the repository's existing ignore rules.
- [ ] Verify the agent-specific invocation syntax: Claude `/develop`; Codex or
      another Agent Skills client may use `$develop`, a picker, or an explicit
      natural-language request.

Do not install community skills directly into `.agents/skills/`. Add candidates
to the central kit, review their license and behavior, evaluate them, and ship a
new kit version through a normal project update PR. The alpha installer does
not yet apply updates to an installed kit.
