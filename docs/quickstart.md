# Quickstart and extension guide

## 1. Validate the synthetic example

From the repository root:

```powershell
python -B scripts/evidence_check.py examples/synthetic/contract.json
```

The checker reads UTF-8 JSON and exits with `0` for `PASS`, `2` for `CONDITIONAL`, and `1` for malformed or blocked evidence. Use the exit code in CI; use the text output when handing a result to a reviewer.

## 2. Start a project-local contract

Copy the synthetic file outside this repository and replace its IDs with project-local IDs. Keep source files in their controlled project location. Record only a digest and a stable source reference in the public contract.

At minimum, fill in:

- the model, step, region, load case, and time/frame scope;
- input source IDs, SHA-256 digests, and units;
- datacheck, analysis, and physics-review states;
- field or history observations with coordinates, frames/times, and units;
- claim IDs and the evidence IDs that support them.

For field/history rows, provide a non-negative integer `frame` or a finite,
non-negative numeric `time`. Static-audit and document rows do not need either
marker. Every SHA-256 value must be exactly 64 hexadecimal characters.

## 3. Convert a synthetic Abaqus report

The public cross-repository fixture uses the report shape emitted by the
companion Abaqus skills. It is static-only and intentionally remains conditional:

```powershell
python -B scripts/from_abaqus_audit.py examples/cross-repo/abaqus-agent-report.json contract.json
python -B scripts/evidence_check.py contract.json
```

Run the conversion twice to confirm that the second run reports `UNCHANGED` and
that the contract bytes are identical. A different existing output, symlink,
directory, or dangling link is rejected rather than overwritten.

## 4. Use the skills in order

Read [evidence-contract](../skills/evidence-contract/SKILL.md) before extracting values. Use [provenance-ledger](../skills/provenance-ledger/SKILL.md) while copying or transforming them. Apply [solver-status-gate](../skills/solver-status-gate/SKILL.md) before calling a run complete, then [result-audit](../skills/result-audit/SKILL.md) and [claim-readiness-audit](../skills/claim-readiness-audit/SKILL.md). Finish with [reproducible-reporting](../skills/reproducible-reporting/SKILL.md).

## 5. Add a stricter check

Prefer a small, deterministic Python module with unit tests. Return a distinct exit code for a new gate, document whether it is structural or physical, and include a synthetic fixture. Do not make a validator infer missing coordinates, units, frames, or baselines.
