---
name: evidence-contract
description: Use when an engineering or simulation result needs a bounded, testable evidence contract before interpretation or publication.
---

# Evidence contract

## When to use

Use this skill before extracting a number, drafting a result sentence, or comparing a model with a baseline. It is especially useful when several people or tools will exchange files and the phrase “the result” could refer to different steps, regions, or frames.

## Inputs

- The question or proposed claim.
- Model, load case, step, region, coordinate system, and frame/time scope.
- Expected observable fields or histories and their units.
- Source artifacts and the review gates that must be closed.

## Outputs

Create a small contract with `artifact_id`, `scope`, `inputs`, `solver_status`, `evidence`, and `claims`. Add an explicit list of open gates and a verdict of `PASS`, `CONDITIONAL`, or `BLOCKED`. Keep unknown values unknown; do not fill them with plausible defaults.

## Safety gates

- A claim must name its scope before a value is accepted.
- Every input and observation must have a stable source identifier.
- Units, sign convention, coordinates, and frame/time are mandatory for reported values.
- Solver completion is not physical validation; retain a separate review state.
- Keep private paths, databases, and credentials outside the public contract.

## Example prompts

- “Draft a contract for the crown displacement at the final mechanical frame and list every missing scope field.”
- “Turn these proposed tunnel claims into IDs with required evidence and explicit review gates.”
- “Compare two candidate contracts and report which one has the narrower, reproducible scope.”

## Common failures

- Treating a whole ODB or report as evidence without naming a frame or region.
- Mixing a solver status with a physical-review verdict.
- Copying a maximum value without its location, sign convention, or units.
- Allowing a claim to reference a file path that is not stable or shareable.

## Acceptance checklist

- [ ] The question, artifact, scope, and comparison boundary are explicit.
- [ ] Inputs have source IDs, digests, and units.
- [ ] Each observation has a field, source, coordinate system, and frame/time.
- [ ] Each claim resolves to one or more evidence IDs.
- [ ] Open gates and the current verdict are visible to a reviewer.
