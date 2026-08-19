# Architecture

The toolkit is intentionally layered. A downstream project may use one skill in isolation, but the full workflow makes state changes explicit.

```text
source inventory -> evidence contract -> provenance ledger
                                      |
                         solver status gate
                                      |
                  result audit -> claim readiness audit
                                      |
                         reproducible report
```

For a static Abaqus review, `scripts/from_abaqus_audit.py` sits at the source
boundary: it accepts a report digest plus generalized findings and emits a
static-only 0.2 contract. It does not import an ODB or claim solver execution.

## Boundaries

- **Source inventory** identifies the artifact, owner, acquisition time, and digest. It does not copy private data into this repository.
- **Evidence contract** fixes the scope and acceptance fields before a result is interpreted.
- **Provenance ledger** preserves the link from source to observation, including unit and coordinate transforms.
- **Solver status gate** keeps calculation completion separate from physical review. A completed process can remain conditional.
- **Result audit** checks simple, explainable invariants. It should never silently repair signs, units, or coordinate systems.
- **Claim readiness audit** labels claims as ready, conditional, or blocked and requires resolvable evidence IDs.
- **Reproducible report** packages metadata and commands. It is a handoff artifact, not a publication guarantee.
- **Public-tree boundary** scans git-tracked files when a repository is available, while fallback scans exclude build outputs, worktrees, and bytecode caches but still include tests and `NOTICE`.

## Extending the contract

Add domain-specific fields under `scope`, `inputs`, `evidence`, or `claims`. Keep the core fields intact so that generic tooling can still validate the record. New fields should document units, coordinate conventions, allowed states, and an example. If a domain needs a stricter gate, implement it as a separate validator or skill rather than weakening the base contract.
