---
name: result-audit
description: Use when extracted engineering values need a bounded review of signs, units, coordinates, frames, regions, baselines, and simple consistency checks.
---

# Result audit

## When to use

Use after extraction and before a value enters a figure, table, abstract, or claim. Use it for field and history outputs, measurements, and analytical baselines. Keep the audit narrow enough that every check can be explained and reproduced.

## Inputs

- Evidence records with source IDs, field names, values, units, coordinates, frame/time, and region.
- Sign conventions and expected physical direction.
- Mesh, boundary, material, and load-case scope relevant to the value.
- A baseline, neighboring point, conservation check, or other independent comparison when available.

## Outputs

Return an audit table with check ID, rule, observed value, expected/bounded value, result, evidence source, and reviewer note. Mark each issue as `PASS`, `CONDITIONAL`, or `BLOCKED`; never silently correct the input.

## Safety gates

- Check units before magnitudes and sign conventions before ranking.
- Keep local and global coordinates distinct.
- Name the exact frame/time and region for extrema or averages.
- A plausible contour is not an independent validation.
- If a value is outside a bound, preserve it and escalate the cause instead of clipping it.

## Example prompts

- “Audit these displacement extrema for sign, unit, frame, and region completeness.”
- “Compare the baseline and modified response without mixing local and global axes.”
- “List which checks are conditional because no independent baseline was supplied.”

## Common failures

- Comparing MPa with Pa or millimetres with metres.
- Ranking signed values by absolute value without stating the rule.
- Using a nodal maximum from one region as if it described the whole model.
- Fixing a negative value in a report instead of investigating the convention.

## Acceptance checklist

- [ ] Units and sign convention are explicit and consistent.
- [ ] Coordinate system, region, frame/time, and selection rule are recorded.
- [ ] At least one bounded or independent check is attempted when feasible.
- [ ] Outliers remain visible with a disposition.
- [ ] The audit result is linked to evidence IDs and reviewer notes.
