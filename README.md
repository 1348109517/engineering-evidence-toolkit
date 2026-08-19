# Engineering Evidence Toolkit

Small, inspectable building blocks for turning engineering and simulation outputs into source-backed, reproducible evidence. The v0.2 contract accepts the v0.1 example while validating lifecycle precedence, hexadecimal SHA-256 digests, unique IDs, resolvable claims, and typed frame/time markers. The toolkit is designed for human-reviewed workflows: it records scope, provenance, solver state, units, coordinates, frames, and claim readiness without pretending that a green solver exit code proves physical correctness.

This is a clean-room, Apache-2.0 repository. The examples are synthetic and contain no ODB, CAE, manuscript, credential, or private project data.

## What is included

| Skill | Purpose |
| --- | --- |
| [evidence-contract](skills/evidence-contract/SKILL.md) | Define the smallest testable contract before collecting results. |
| [provenance-ledger](skills/provenance-ledger/SKILL.md) | Bind every input and observation to an identifier, digest, unit system, and transform history. |
| [solver-status-gate](skills/solver-status-gate/SKILL.md) | Separate datacheck, solver completion, physical review, and publication readiness. |
| [result-audit](skills/result-audit/SKILL.md) | Audit signs, units, coordinates, frames, regions, baselines, and simple bounds. |
| [claim-readiness-audit](skills/claim-readiness-audit/SKILL.md) | Map each prose claim to evidence and expose blocked or conditional links. |
| [reproducible-reporting](skills/reproducible-reporting/SKILL.md) | Assemble a deterministic manifest, environment record, command log, and handoff report. |

The standard-library checker at [`scripts/evidence_check.py`](scripts/evidence_check.py) validates a compact JSON contract. It is a structural gate, not a replacement for an Abaqus run, an ODB review, or an engineering sign-off.

## Quick start

```powershell
python -B scripts/evidence_check.py examples/synthetic/contract.json
python -B -m unittest discover -s tests -v
```

The synthetic contract should print `PASS`. Changing `solver_status.physics_review` to `not_started` demonstrates the `CONDITIONAL` exit code (`2`). Missing source records or unbound evidence returns `BLOCKED`.

## Contract shape

Every contract records:

1. an `artifact_id` and explicit `scope` (model, step, region, and other boundaries);
2. non-empty `inputs` with `source_id`, SHA-256, and units;
3. separate `solver_status` values for `datacheck`, `analysis`, and `physics_review`;
4. field/history observations with source IDs, field names, units, coordinate system, and valid non-negative frame or finite non-negative time; static-audit/document rows are exempt from frame/time;
5. claims whose `evidence_ids` resolve to observations.

The contract intentionally keeps the final decision visible. A failed status in any of `datacheck`, `analysis`, or `physics_review` blocks the contract; otherwise any pending/required/not-run state is conditional; only complete/passed/reviewed states across all three can pass. A calculation can be complete while a claim remains conditional or blocked until physical review, baseline comparison, or source reconciliation is complete.

## Abaqus report adapter

The deterministic [`from_abaqus_audit.py`](scripts/from_abaqus_audit.py) adapter accepts the companion Abaqus report shape (`input_digest` plus `findings`) and emits a static-only 0.2 contract. It can also hash a model input file with `--model-input`:

```powershell
python -B scripts/from_abaqus_audit.py examples/cross-repo/abaqus-agent-report.json contract.json
python -B scripts/evidence_check.py contract.json
```

The public [cross-repository example](examples/cross-repo/README.md) is synthetic. Repeating the conversion produces byte-identical output and the checker returns `CONDITIONAL` because no solver or physical-review gate is being asserted.

## Documentation

- [Architecture](docs/architecture.md)
- [Quickstart and extension guide](docs/quickstart.md)
- [Claim lifecycle](docs/claim-lifecycle.md)
- [Contributing](CONTRIBUTING.md)
- [Security and data boundary](SECURITY.md)
- [Roadmap](ROADMAP.md)
- [Citation metadata](CITATION.cff)

## Relationship to Abaqus skills

The companion [abaqus-agent-skills](https://github.com/1348109517/abaqus-agent-skills) repository focuses on model construction and review. This repository is deliberately solver-agnostic so that the same evidence contract can wrap Abaqus, other finite-element solvers, laboratory measurements, or analytical baselines.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
