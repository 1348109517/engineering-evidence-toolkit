# Synthetic example

`contract.json` is a deliberately small, fictional tunnel-response record. All IDs and SHA-256 values are placeholders. It exists to exercise the checker and the documentation, not to support an engineering conclusion.

Try changing `solver_status.physics_review` from `passed` to `not_started` and run the checker again. The result becomes `CONDITIONAL`, which demonstrates the distinction between structural completeness and an open physical gate.
