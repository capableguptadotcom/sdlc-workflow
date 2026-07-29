# Pantry Ledger project instructions

- Keep the runtime dependency-free unless the maintainer explicitly approves a
  package.
- Use Node.js 22 built-ins and `node:test`.
- Inject persistence paths in tests; never write test data into the repository.
- Preserve the `/health` response for local probes.
