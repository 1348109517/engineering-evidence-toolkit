---
name: claim-readiness-audit
description: Use when prose claims, captions, or conclusions must be checked against a complete chain of scoped and audited evidence.
---

# Claim readiness audit

## When to use

Use before a result sentence, figure caption, executive summary, thesis paragraph, or release note is treated as final. It is the last evidence-chain review before reproducible packaging.

## Inputs

- Candidate claims with stable IDs and precise wording.
- Evidence IDs and provenance rows supporting each clause.
- Result-audit outcomes and solver-status gate state.
- The strength of language intended by the author, such as observed, suggests, supports, or validates.

## Outputs

Create a claim matrix with claim text, scope, evidence IDs, audit status, open gates, and readiness. Use `READY`, `CONDITIONAL`, or `BLOCKED`. Record a weaker wording when the evidence supports only an observation or association.

## Safety gates

- Every factual clause needs a resolvable evidence path.
- Do not upgrade “observed” to “caused”, “validated”, or “general” without a matching design and gate.
- A missing baseline, calibration, uncertainty, or physical review keeps the claim conditional.
- Keep negative or contradictory evidence attached to the same claim.
- Do not remove a blocker by deleting the observation that exposed it.

## Example prompts

- “Audit these three conclusions and rewrite any sentence that is stronger than its evidence.”
- “Map the caption to frame, region, units, source, and result-audit rows.”
- “Return a claim matrix and identify the minimum evidence needed to move each conditional claim to ready.”

## Common failures

- Treating a statistical or numerical association as causation.
- Citing a whole report without a field, frame, region, or source ID.
- Hiding a conditional status in a footnote while using definitive language in the title.
- Reusing one evidence row to support incompatible claims.

## Acceptance checklist

- [ ] Each claim has a stable ID and explicit scope.
- [ ] Every clause resolves to evidence and provenance rows.
- [ ] Solver and result-audit gates are visible.
- [ ] Language strength matches the evidence and uncertainty.
- [ ] Blocked or conditional claims have a concrete next action.
