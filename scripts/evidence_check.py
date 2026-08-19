#!/usr/bin/env python3
"""Validate a small, source-backed engineering evidence contract.

The checker is intentionally dependency-free. It is a gate for structure and
provenance, not a substitute for a solver, a physical review, or an engineer's
judgement.
"""

from __future__ import annotations

import argparse
import json
import math
import re
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
CONDITIONAL_REVIEW_STATES = {"required", "not_started", "not_run", "pending"}
BLOCKED_REVIEW_STATES = {"failed", "rejected", "blocked"}
SUPPORTED_CONTRACT_VERSIONS = {"0.1", "0.2"}
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
PASS_REVIEW_STATES = PASS_REVIEW_STATES | {"pass", "success"}
KNOWN_LIFECYCLE_STATES = (
    PASS_REVIEW_STATES | CONDITIONAL_REVIEW_STATES | BLOCKED_REVIEW_STATES
)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_frame(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_time(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


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
    elif contract["contract_version"] not in SUPPORTED_CONTRACT_VERSIONS:
        errors.append(
            "contract_version must be one of: "
            + ", ".join(sorted(SUPPORTED_CONTRACT_VERSIONS))
        )
    if not _is_nonempty_string(contract["artifact_id"]):
        errors.append("artifact_id must be a non-empty string")
    if not isinstance(contract["scope"], dict) or not contract["scope"]:
        errors.append("scope must be a non-empty object")

    inputs = contract["inputs"]
    contract_version = contract.get("contract_version")
    input_source_ids: set[str] = set()
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
            source_id = item.get("source_id")
            if _is_nonempty_string(source_id):
                if contract_version == "0.2" and source_id in input_source_ids:
                    errors.append(f"duplicate input source id: {source_id}")
                input_source_ids.add(source_id)
            digest = item.get("sha256")
            if _is_nonempty_string(digest) and not SHA256_PATTERN.fullmatch(digest):
                errors.append(
                    f"inputs[{index}].sha256 must be a 64-character hexadecimal SHA-256 digest"
                )

    statuses = contract["solver_status"]
    if not isinstance(statuses, dict):
        errors.append("solver_status must be an object")
        statuses = {}
    for key in ("datacheck", "analysis", "physics_review"):
        if not _is_nonempty_string(statuses.get(key)):
            errors.append(f"solver_status missing non-empty {key}")
        elif statuses[key] not in KNOWN_LIFECYCLE_STATES:
            errors.append(
                f"solver_status.{key} has unsupported lifecycle status: {statuses[key]}"
            )

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
                if item["id"] in evidence_ids:
                    errors.append(f"duplicate evidence id: {item['id']}")
                evidence_ids.add(item["id"])
            if item.get("kind") in {"field", "history"}:
                if "frame" in item and not _valid_frame(item["frame"]):
                    errors.append(
                        f"evidence[{index}] frame/time must use a non-negative integer frame"
                    )
                if "time" in item and not _valid_time(item["time"]):
                    errors.append(
                        f"evidence[{index}] frame/time must use a finite non-negative numeric time"
                    )
                if not _valid_frame(item.get("frame")) and not _valid_time(item.get("time")):
                    errors.append(
                        f"evidence[{index}] must identify a valid frame or time"
                    )
            if "sha256" in item and (
                not isinstance(item["sha256"], str)
                or not SHA256_PATTERN.fullmatch(item["sha256"])
            ):
                errors.append(
                    f"evidence[{index}].sha256 must be a 64-character hexadecimal SHA-256 digest"
                )
            source_id = item.get("source_id")
            if (
                contract_version == "0.2"
                and _is_nonempty_string(source_id)
                and source_id not in input_source_ids
            ):
                errors.append(
                    f"evidence[{index}] references unknown input source id: {source_id}"
                )

    claims = contract["claims"]
    claim_ids: set[str] = set()
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
            elif item["id"] in claim_ids:
                errors.append(f"duplicate claim id: {item['id']}")
            if _is_nonempty_string(item.get("id")):
                claim_ids.add(item["id"])
            if not _is_nonempty_string(item.get("text")):
                errors.append(f"claims[{index}].text must be a non-empty string")
            refs = item.get("evidence_ids")
            if not isinstance(refs, list) or not refs:
                errors.append(f"claims[{index}].evidence_ids must be a non-empty list")
            else:
                for ref in refs:
                    if not _is_nonempty_string(ref):
                        errors.append(
                            f"claims[{index}].evidence_ids must contain non-empty strings"
                        )
                    elif ref not in evidence_ids:
                        errors.append(f"claims[{index}] references unknown evidence id: {ref}")

    if errors:
        return "BLOCKED", errors
    statuses_by_key = {
        key: statuses[key] for key in ("datacheck", "analysis", "physics_review")
    }
    blocked = [
        f"{key} state is {state}"
        for key, state in statuses_by_key.items()
        if state in BLOCKED_REVIEW_STATES
    ]
    if blocked:
        return "BLOCKED", blocked
    conditional = [
        f"{key} state is {state}; publication claim is gated"
        for key, state in statuses_by_key.items()
        if state in CONDITIONAL_REVIEW_STATES
    ]
    if conditional:
        return "CONDITIONAL", conditional
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
