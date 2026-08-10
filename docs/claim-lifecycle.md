# Claim lifecycle

Every public engineering sentence should pass through the same visible states:

1. **Proposed** — the claim is a question, not a result.
2. **Scoped** — model, step, region, load case, coordinate system, units, and frame/time are explicit.
3. **Bound** — source IDs, digests, and observation IDs resolve through the provenance ledger.
4. **Audited** — signs, units, ranges, baselines, and independent checks have been reviewed.
5. **Conditional** — the structure is sound but a physical review, calibration, or reconciliation gate is still open.
6. **Ready** — a reviewer can reproduce the path from claim to source without guessing.
7. **Blocked** — a required source, gate, or consistency check failed.

`PASS` from the CLI only means the contract is structurally complete and its declared physical-review state is accepted. It is not a promise that the model is physically valid or that a manuscript should be submitted.

## Reviewer questions

- What exact artifact and frame support this sentence?
- Are the reported quantity, sign convention, units, and coordinate system explicit?
- Is the baseline or comparison case identified and comparable?
- Which gate is still conditional, if any?
- Can another person locate the source without receiving private files?
