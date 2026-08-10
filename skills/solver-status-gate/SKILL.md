---
name: solver-status-gate
description: Use when an analysis run must be classified without confusing datacheck success or solver completion with physical correctness.
---

# Solver status gate

## When to use

Use after a solver process, datacheck, restart, or post-processing job finishes and before describing the model as validated or publishable. The skill applies to Abaqus and other analysis tools because it reasons about states, not vendor-specific log wording.

## Inputs

- Datacheck or preprocessing status and log evidence.
- Analysis completion status, increment/step coverage, warnings, and termination reason.
- Physical-review status, including boundary conditions, material response, mesh, convergence, and baseline checks.
- The intended claim and its required acceptance threshold.

## Outputs

Write three independent statuses: `datacheck`, `analysis`, and `physics_review`. Produce a gate table with evidence IDs, open issues, and a verdict. Use `PASS` only when the declared physical-review gate is closed; otherwise use `CONDITIONAL` or `BLOCKED`.

## Safety gates

- A green process exit code cannot close a physics-review gate.
- A completed step with warnings or missing frames must remain conditional until reconciled.
- Do not infer physical validity from residuals, stable increments, or a plausible-looking contour alone.
- Preserve the exact termination reason and the log source.
- If a required gate failed, stop publication wording and return `BLOCKED`.

## Example prompts

- “Classify this run from the log summary and separate calculation completion from physical review.”
- “Build a gate table for datacheck pass, analysis complete, and boundary-condition review pending.”
- “What evidence is still required before the claim can say ‘validated’?”

## Common failures

- Reporting “solver success = model verified”.
- Treating a datacheck as an analysis result.
- Ignoring a cutback, incomplete frame range, or unconverged increment.
- Overwriting `CONDITIONAL` with `PASS` because the requested report is due.

## Acceptance checklist

- [ ] Datacheck, analysis, and physical review are separate fields.
- [ ] Each status cites a log, frame inventory, or review record.
- [ ] Warnings, incomplete steps, and open physics questions are retained.
- [ ] The verdict follows the strictest open gate.
- [ ] The report language matches the verdict and does not overclaim validation.
