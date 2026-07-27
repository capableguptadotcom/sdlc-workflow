# Adoption checklist

Complete this once when copying the kit into a repository.

- [ ] Fill every applicable command list in `ai-sdlc.yaml`.
- [ ] Replace generic project assumptions in `AGENTS.md` with proven local
      constraints; keep the workflow and authorization rules.
- [ ] Run `python scripts/validate_ai_kit.py`.
- [ ] Test `/develop`, `/finish`, and `/learn` in each supported agent.
- [ ] Run at least one positive and one negative trigger case for every enabled
      specialist skill.
- [ ] Configure deterministic local hooks separately from networked AI review.
- [ ] Add required CI checks and protected-branch rules.
- [ ] Assign owners for guidance, security, UI, and upstream skill review.
- [ ] Record the adopted kit version in `.ai/kit-version.json`.
- [ ] Add the configured transient handoff path (default
      `artifacts/ai/handoffs/`) to the repository's existing ignore rules.
- [ ] Verify the agent-specific invocation syntax: Claude `/develop`; Codex or
      another Agent Skills client may use `$develop`, a picker, or an explicit
      natural-language request.

Do not install community skills directly into `.agents/skills/`. Add candidates
to the central kit, review their license and behavior, evaluate them, and ship a
new kit version through a normal project update PR.
