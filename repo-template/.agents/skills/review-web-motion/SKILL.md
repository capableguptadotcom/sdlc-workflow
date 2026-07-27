---
name: review-web-motion
description: Review a diff or running web interaction that changes animation, transitions, gestures, scrolling effects, or motion tokens. Use only when motion behavior is present or explicitly requested. Do not use as a general UI review, to add decorative animation by default, or to certify subjective feel without a live preview or recording.
---

# Review web motion

Read `references/motion-standards.md` before judging implementation.

1. Establish the changed interaction, existing motion language, input methods,
   and intended feedback.
2. Review the bounded diff and run the relevant preview. Use slow-motion or
   frame-by-frame evidence for timing, continuity, and interruption claims.
3. Check purpose, frequency, duration, easing, spatial continuity, interruption,
   exit behavior, and perceived latency.
4. Verify reduced-motion behavior, keyboard and simple-pointer alternatives,
   pointer cancellation, focus behavior, and real-device touch interaction.
5. Profile representative interactions before claiming a performance regression.
6. Classify findings:
   - `block` for broken interaction, accessibility failure, documented-system
     violation, or measured regression;
   - `advisory` for taste or polish improvements.
7. Return exact evidence, before/after recommendation, and
   `approve`, `approve-with-advisories`, or `request-changes`.

Do not make a house-style preference a merge blocker.
