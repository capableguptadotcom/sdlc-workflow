# Interface checks

## Information and layout

- Make the primary task and action visually clear.
- Preserve logical reading, focus, and responsive order.
- Test narrow mobile, representative desktop, text zoom, long content, and
  localization-sensitive layouts.
- Prefer spacing and alignment from existing tokens over one-off values.

## Typography and content

- Use semantic headings appropriate to component and page context.
- Verify actual font files, weights, styles, fallbacks, wrapping, truncation,
  numerals, punctuation, and form text.
- Do not globally disable synthesis or apply smoothing without verifying the
  loaded fonts and rendered result.

## Interaction and accessibility

- Use native semantics before ARIA; ensure name, role, value, and error
  association.
- Give documents an appropriate language and title. Use persistent visible form
  labels; a placeholder is not a label.
- Support keyboard and simple-pointer operation, visible focus, pointer
  cancellation, and adequate targets.
- Follow the established keyboard pattern for composite widgets; their inner
  controls do not all need to be separate Tab stops. For modal dialogs, verify
  naming, modal semantics, initial focus, containment, Escape behavior, and
  contextual focus return.
- Check applicable WCAG 2.2 success criteria. Measure contrast with deterministic
  tooling: common AA thresholds are 4.5:1 for normal text, 3:1 for large text,
  and 3:1 for applicable UI boundaries and states. Apply the standard's scope
  and exceptions rather than treating a number alone as conformance.
- Check status, progress, busy, success, and error announcements without adding
  indiscriminate or duplicate live regions.
- Check forced-colors or high-contrast behavior, text spacing, reflow, and
  content revealed on hover or focus when the changed UI makes them relevant.
- Avoid duplicated focusable or semantic UI when visual effects clone content.

Automated checks and this review find common issues; neither is proof of WCAG
conformance. Verify behavior-dependent findings with keyboard and appropriate
assistive technology.

Primary references:

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [WAI-ARIA Authoring Practices keyboard guidance](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)
- [WAI-ARIA modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- [WCAG text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [WCAG non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)

## Visual polish

- Keep borders, shadows, radii, icons, and depth consistent with the design
  system.
- Verify light/dark tokens independently. Do not create dark mode by merely
  reversing a light palette.
- Prefer clear state changes over decorative motion. Route substantive motion
  work to `review-web-motion`.
