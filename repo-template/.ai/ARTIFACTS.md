# Progressive artifacts

Artifacts exist to reduce rework and help people and agents resume accurately.
Use the lightest level that makes the work reliable.

| Level | Use when | Create |
| --- | --- | --- |
| Routine | Clear, local, reversible, low-risk edit | Request or PR intent plus command results |
| Bounded behavior | A normal feature or unresolved expected behavior | `spec.md` and `verification.md` |
| Multi-slice change | Dependency-ordered increments, migration, compatibility, rollout, or material risk | Bounded behavior artifacts plus `plan.md`; tickets only when useful |
| Initiative | Several coordinated outcomes or decision tracks cannot remain one coherent spec or session | Initiative map first, then one spec per coherent outcome |

ADRs and domain context are separate from these levels:

- Create `CONTEXT.md` only when the first stable, project-specific term needs a
  canonical definition.
- Create an ADR only when a decision is hard to reverse, surprising without its
  context, and the result of a real trade-off.
- Create tracker tickets only after spec acceptance, when slices are
  independently assignable or resumable, and after explicit authorization.

## Artifact ownership

- `ai-sdlc.yaml`, context, specs, plans, tasks, initiatives, ADRs, and product
  documentation are project-owned.
- Files under `.ai/templates/` and `specs/_template/` are kit-managed examples.
- `.ai/kit.lock.json` will be machine-managed installation state.
- `.ai/skills.lock.json` remains third-party skill provenance; it is not
  installation state.

## Lifecycle

- Only explicit human confirmation marks a material spec, plan, or ADR
  accepted.
- Material changes to accepted behavior, scope, risk, rollout, dependencies, or
  human gates return the affected spec or plan to `draft`.
- Supersede accepted decisions with a new linked artifact. Do not rewrite
  historical rationale.
- Keep transient handoffs redacted and disposable after durable artifacts are
  current.

Templates are references, not installation instructions. Do not generate empty
context, decision, or initiative directories during adoption.
