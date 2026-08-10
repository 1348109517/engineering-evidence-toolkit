#!/usr/bin/env python3
"""Validate a small, source-backed engineering evidence contract.

The checker is intentionally dependency-free. It is a gate for structure and
provenance, not a substitute for a solver, a physical review, or an engineer's
judgement.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = (
    "contract_version",
    "artifact_id",
    "scope",
    "inputs",
    "solver_status",
    "evidence",
    "claims",
)
PASS_REVIEW_STATES = {"passed", "complete", "reviewed"}
CONDITIONAL_REVIEW_STATES = {"required", "not_started", "pending"}
BLOCKED_REVIEW_STATES = {"failed", "rejected", "blocked"}


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_contract(contract: Any) -> tuple[str, list[str]]:
    """Return ``(verdict, errors)`` where verdict is PASS/CONDITIONAL/BLOCKED."""

    errors: list[str] = []
    if not isinstance(contract, dict):
        return "BLOCKED", ["contract must be a JSON object"]

    for key in REQUIRED_TOP_LEVEL:
        if key not in contract:
            errors.append(f"missing top-level field: {key}")

    if errors:
        return "BLOCKED", errors

    if not _is_nonempty_string(contract["contract_version"]):
        errors.append("contract_version must be a non-empty string")
    if not _is_nonempty_string(contract["artifact_id"]):
        errors.append("artifact_id must be a non-empty string")
    if not isinstance(contract["scope"], dict) or not contract["scope"]:
        errors.append("scope must be a non-empty object")

    inputs = contract["inputs"]
    if not isinstance(inputs, list) or not inputs:
        errors.append("inputs must be a non-empty list with source provenance")
    else:
        for index, item in enumerate(inputs):
            if not isinstance(item, dict):
                errors.append(f"inputs[{index}] must be an object")
                continue
            for key in ("name", "source_id", "sha256", "units"):
                if not _is_nonempty_string(item.get(key)):
                    errors.append(f"inputs[{index}] missing non-empty {key}")
            digest = item.get("sha256")
            if _is_nonempty_string(digest) and len(digest) != 64:
                errors.append(f"inputs[{index}].sha256 must be a 64-character digest")

    statuses = contract["solver_status"]
    if not isinstance(statuses, dict):
        errors.append("solver_status must be an object")
        statuses = {}
    for key in ("datacheck", "analysis", "physics_review"):
        if not _is_nonempty_string(statuses.get(key)):
            errors.append(f"solver_status missing non-empty {key}")
    if statuses.get("datacheck") not in {"pass", "passed", "complete"}:
        errors.append("solver_status.datacheck must be pass/passed/complete")
    if statuses.get("analysis") not in {"complete", "passed", "success"}:
        errors.append("solver_status.analysis must be complete/passed/success")

    evidence = contract["evidence"]
    evidence_ids: set[str] = set()
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must be a non-empty list")
    else:
        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                errors.append(f"evidence[{index}] must be an object")
                continue
            for key in ("id", "kind", "source_id", "field", "units", "coordinate_system"):
                if not _is_nonempty_string(item.get(key)):
                    errors.append(f"evidence[{index}] missing non-empty {key}")
            if _is_nonempty_string(item.get("id")):
                evidence_ids.add(item["id"])
            if "frame" not in item and "time" not in item:
                errors.append(f"evidence[{index}] must identify a frame or time")

    claims = contract["claims"]
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list")
    else:
        for index, item in enumerate(claims):
            if not isinstance(item, dict):
                errors.append(f"claims[{index}] must be an object")
                continue
            for key in ("id", "text", "evidence_ids"):
                if key not in item:
                    errors.append(f"claims[{index}] missing {key}")
            if not _is_nonempty_string(item.get("id")):
                errors.append(f"claims[{index}].id must be a non-empty string")
            if not _is_nonempty_string(item.get("text")):
                errors.append(f"claims[{index}].text must be a non-empty string")
            refs = item.get("evidence_ids")
            if not isinstance(refs, list) or not refs:
                errors.append(f"claims[{index}].evidence_ids must be a non-empty list")
            else:
                for ref in refs:
                    if ref not in evidence_ids:
                        errors.append(f"claims[{index}] references unknown evidence id: {ref}")

    review_state = statuses.get("physics_review")
    if errors:
        return "BLOCKED", errors
    if review_state in BLOCKED_REVIEW_STATES:
        return "BLOCKED", [f"physics review state is {review_state}"]
    if review_state in CONDITIONAL_REVIEW_STATES:
        return "CONDITIONAL", [f"physics review state is {review_state}; publication claim is gated"]
    if review_state not in PASS_REVIEW_STATES:
        return "CONDITIONAL", [f"unrecognized physics review state: {review_state}"]
    return "PASS", []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="path to a JSON evidence contract")
    args = parser.parse_args(argv)
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: contract file not found: {args.contract}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 1

    verdict, messages = validate_contract(contract)
    if verdict == "PASS":
        print(f"PASS: {contract.get('artifact_id', args.contract.name)} satisfies the evidence contract")
        return 0
    if verdict == "CONDITIONAL":
        print(f"CONDITIONAL: {contract.get('artifact_id', args.contract.name)} is structurally valid but gated")
        for message in messages:
            print(f"- {message}")
        return 2
    print("BLOCKED: evidence contract is not publishable", file=sys.stderr)
    for message in messages:
        print(f"- {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
