---
name: ui-quality
description: Review or improve a user-facing web interface for hierarchy, typography, layout, states, responsiveness, interaction clarity, and accessibility while respecting its design system. Use when a change creates or materially alters visible UI, or when the user explicitly requests a UI or accessibility audit. Do not use for backend-only work, brand redesign without product direction, or motion-only review.
---

# UI quality

Read `references/interface-checks.md` and select only applicable checks.

1. Select a mode: `review` is read-only; `improve` permits scoped edits only
   when the user requested them. The user's authorization always controls.
2. Find the current design system, tokens, component library, target users,
   supported breakpoints, and product personality in repository evidence. Do
   not invent missing context; report it and continue with supported findings.
3. Inspect the running interface before editing when a preview is available.
   Without one, label source-only findings as confirmed, conditional, or
   unverified and make no claims about rendered feel or runtime behavior.
4. Define the task hierarchy, primary action, states, and content before visual
   polish.
5. In improve mode, reuse existing primitives and tokens. Introduce a visual rule only when
   the system cannot express the requirement.
6. Implement the smallest coherent improvement across default, loading, empty,
   error, disabled, focus, and success states that apply.
7. Verify semantics, keyboard operation, focus visibility, zoom, responsive
   layout, contrast, target size, touch behavior, and reduced-motion behavior.
8. Use repository-configured automated checks first; do not add a dependency
   merely to perform a review without authorization. Render relevant
   breakpoints and compare evidence, then perform focused manual checks that
   automation cannot cover. Report unavailable checks explicitly.

Treat exact radii, shadows, scales, easing values, font smoothing, and color
spaces as context-dependent defaults, never universal laws. Do not invent color
conversion or contrast results; use deterministic tools.

For a review, report only actionable findings with severity (`block`,
`advisory`, or `question`), exact location, consequence, confidence,
recommendation, and verification method. Finish with `approve`,
`approve-with-advisories`, `request-changes`, or `insufficient-runtime-evidence`.
For an improvement, also report edits and deterministic commands/results. This
workflow finds common issues; it does not certify accessibility conformance.
