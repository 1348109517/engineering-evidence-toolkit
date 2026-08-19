# Synthetic cross-repository audit

This public fixture mirrors the static `report.json` shape emitted by the
companion Abaqus workflow repository. It contains synthetic finding codes,
generalized locations, and skill names only; it does not contain an ODB, CAE,
solver output, private path, or timestamp.

From the repository root, convert the report and check the resulting contract:

```powershell
python scripts/from_abaqus_audit.py examples/cross-repo/abaqus-agent-report.json contract.json
python scripts/evidence_check.py contract.json
```

The first command is deterministic. Re-running it against the same `contract.json`
prints `UNCHANGED` and leaves the bytes identical. The checker returns exit code
`2` with `CONDITIONAL`: the static report is structurally traceable, while the
solver and physical-review lifecycle states remain required. A static audit is
not an Abaqus run and does not establish physical correctness.
