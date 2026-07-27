# Web motion standards

## Purpose

Use motion to explain state, preserve spatial continuity, acknowledge input, or
reduce perceived waiting. Decline motion that is frequent, decorative, or
slower than the information it communicates.

## Interaction

- Make transitions interruptible and responsive to repeated input.
- Preserve clear entry and exit states; do not leave hidden focusable content.
- Provide non-dragging single-pointer and keyboard alternatives for gestures.
- Avoid hover-only behavior on touch-capable input paths.
- Respect `prefers-reduced-motion`; replace or remove nonessential motion rather
  than merely making every animation faster.

## Implementation and performance

- Prefer compositor-friendly properties and avoid unnecessary layout work.
- Treat transform, opacity, filters, clip paths, CSS, WAAPI, and motion-library
  paths as browser- and context-dependent; profile before declaring one always
  accelerated or always slow.
- Avoid broad `transition: all` and long-lived `will-change` hints.
- Use the project's tokens and libraries before introducing another dependency.

## Evidence

Record the interaction, device or emulation, reduced-motion mode, input method,
and any profile trace used to support a finding.
