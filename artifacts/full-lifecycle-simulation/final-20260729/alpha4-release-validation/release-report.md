# AI SDLC alpha.4 release decision

**Decision: release-ready for the intended alpha channel.**

The immutable, unpublished candidate is
`@innovate-x/ai-sdlc@0.1.0-alpha.4`, SHA-256
`9bd25aeb8b04f390db4451a69d1890039cf8bf27099b68b8e82a6e403fb91b8f`.
Publishing, tagging, pushing, and deployment remain separate operator actions
and were not performed.

## Release gates

- Source: 33/33 Node tests and 66/66 Python tests passed.
- Content: 13 skills, 35 routing cases, 25 behavior cases, and 12 dialogue
  cases validated; all six walkthrough scenarios rendered.
- Supply chain: `npm audit` found zero vulnerabilities; the candidate contains
  65 reviewed files.
- Adoption: a fresh committed seed installed from the read-only tarball with
  Docker networking disabled. Dry-run wrote nothing, the project remained
  healthy, and a same-version rerun changed no bytes.
- Approval boundary: the two-turn probe produced draft specification evidence
  without product changes or commits.
- Full lifecycle: the with-kit arm completed all 10 turns and every phase gate,
  with 69 command attempts and zero interrupted commands.
- Release/operations: final tests, the independent product oracle, a clean
  release checkout, the operations runbook, cross-version rollback, lifecycle
  invariants, retirement, and the clean-worktree gate all passed.
- Independent replay: the full product and rollback oracles passed again in a
  separate Docker invocation with networking disabled.

The nine failed commands recorded in the with-kit transcript are retained
evidence from deliberate red tests, negative probes, or failures corrected
within their owning turn. None was interrupted, every command has a terminal
event, and all phase and final gates passed.

## Comparative finding

The no-kit baseline stopped after five turns. Its local tests passed, but the
independent restart oracle found that its maintenance release could not read
the persisted data shape. Because that gate failed, the harness correctly
withheld operations and rollback. This is comparative evidence, not a
candidate blocker: the alpha.4 with-kit arm passed the same oracle and
completed the remaining lifecycle.

## Resolved release blocker

The alpha.3 exercise exposed a long-running verification command without a
terminal event. Alpha.4 adds explicit bounded ownership, failure-safe cleanup,
process/listener shutdown verification, and a behavior regression. The live
implementation-and-finish turn completed without interruption or an orphaned
runtime.

## Evidence map

- `verification.json`: machine-readable decision and immutable identities.
- `runbook.md`: exact source, adoption, lifecycle, and offline replay commands.
- `boundary-probe/`: focused approval-boundary transcript and report.
- `full-run/comparison.md`: paired summary.
- `full-run/with-kit/report.json`: authoritative lifecycle result.
- `full-run/with-kit/transcript.md`: preserved human/assistant conversation.
- `independent-offline-oracles.log`: network-disabled product and rollback
  replay.
- `with-kit-workspace.bundle`: complete successful simulation repository.
- `../final-package-adoption-alpha4/`: clean offline installation evidence.

## Remaining limitations

- The candidate is intentionally an alpha and is not published.
- Model output is stochastic; the evidence fixes model, harness, scenario,
  package, and oracle identities but does not promise byte-identical future
  transcripts.
- The simulated browser contract is deterministic and includes UI retry
  behavior; it is not a manual assistive-technology certification.
- Registry credentials, provenance attestation, release tag, remote CI, and
  external publishing require an explicitly authorized release operation.
