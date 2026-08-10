---
name: reproducible-reporting
description: Use when an evidence package needs a deterministic manifest, environment record, command log, artifact inventory, and safe handoff.
---

# Reproducible reporting

## When to use

Use at the end of an analysis or review cycle, before sharing a result with a collaborator, opening a pull request, or creating a release. Use it again when a report is regenerated after inputs or scripts change.

## Inputs

- The validated evidence contract and claim matrix.
- Source and derived artifact IDs with digests, sizes, and timestamps.
- Tool versions, operating-system details, script entry points, and command arguments.
- Redaction rules and the list of files that must remain private.

## Outputs

Produce a deterministic handoff containing a manifest, environment record, command transcript, evidence/claim index, open-gate list, and a human-readable summary. Sort entries, pin units and time conventions, and distinguish generated artifacts from reviewed artifacts.

## Safety gates

- Do not publish private paths, credentials, raw databases, or unreviewed logs.
- A reproducible package records commands; it does not imply that the commands are physically valid.
- Recompute digests after any content change and record the new artifact ID.
- Keep generated charts and tables linked to the audited observation IDs.
- Mark missing tools or unavailable proprietary solvers instead of claiming replay success.

## Example prompts

- “Assemble a clean handoff manifest for this synthetic contract and list all open gates.”
- “Make this report deterministic by sorting artifact rows and recording tool versions.”
- “Redact private paths while preserving enough provenance for a reviewer to request the source.”

## Common failures

- Reporting a command without the working directory, version, or input digest.
- Including a generated figure but not the script or evidence IDs behind it.
- Calling a package reproducible when a licensed solver or private file is missing.
- Reusing a stale manifest after changing a script or input.

## Acceptance checklist

- [ ] Contract, claim matrix, and open gates are included.
- [ ] Artifact rows are sorted and content-addressed where possible.
- [ ] Environment and commands are recorded with versions.
- [ ] Private material is excluded or explicitly redacted.
- [ ] A reviewer can distinguish replayable steps from review-only steps.
