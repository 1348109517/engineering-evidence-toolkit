---
name: provenance-ledger
description: Use when values or files are copied, transformed, filtered, or joined and a reviewer must trace each observation back to its source.
---

# Provenance ledger

## When to use

Use this skill whenever a result moves from an ODB, CSV, test log, notebook, or analyst handoff into a table, figure, report, or claim. Use it again after unit conversion, coordinate transformation, interpolation, filtering, or baseline alignment.

## Inputs

- A source inventory with stable IDs and SHA-256 digests.
- The extraction command, script version, and operator or agent.
- Original and transformed units, coordinates, time/frame, region, and selection rule.
- Destination artifact and the observation IDs created from the source.

## Outputs

Maintain a ledger row per source and per material transformation. A useful row contains `source_id`, `parent_source_id`, `artifact_kind`, `digest`, `selection`, `transform`, `units_in`, `units_out`, `coordinates_in`, `coordinates_out`, `frame_or_time`, `created_at`, and `notes`. Use content-addressed IDs where practical.

## Safety gates

- Never replace a source digest after extraction; create a new source record.
- Record whether a transform is exact, interpolated, averaged, filtered, or manually selected.
- Preserve the original sign convention and state every change explicitly.
- A missing source or ambiguous transform blocks a publication-grade claim.
- Do not put private absolute paths or raw database content in a public ledger.

## Example prompts

- “Build a ledger for these three synthetic CSV extracts and show the unit conversion chain.”
- “Find every claim whose observation has no parent source or frame identifier.”
- “Review this transformation from local shell coordinates to global coordinates and list what must be recorded.”

## Common failures

- Hashing a report after manual edits but calling it the original source.
- Recording only the final table and losing the extraction query.
- Converting millimetres to metres without naming the conversion and checking magnitude.
- Reusing one source ID for files that differ by step, frame, or region.

## Acceptance checklist

- [ ] Every source has a stable ID and digest.
- [ ] Every observation points to a source and selection rule.
- [ ] Unit and coordinate transforms have input/output conventions.
- [ ] Frame/time and region survive every transformation.
- [ ] A reviewer can replay the chain without private files or guessed defaults.
