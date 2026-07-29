# Alpha.4 clean adoption evidence

`workspace/` is a fresh committed Pantry Ledger seed adopted from the retained
alpha.4 tarball. The candidate directory was mounted read-only and Docker
networking was disabled.

The evidence covers dry-run no-write behavior, non-interactive installation,
installed-kit validation, the seed project's test suite, Git whitespace
checks, package-manifest inspection, and a byte-for-byte unchanged
same-version rerun. `workspace.bundle` preserves the original seed history.

See `verification.json` for the immutable package and tooling identities.
