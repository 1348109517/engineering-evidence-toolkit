#!/usr/bin/env python3
"""Create a deterministic, static-only evidence contract from an Abaqus audit report."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
PUBLIC_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
EMBEDDED_PATH_OR_URI_PATTERN = re.compile(
    r"(?i)(?:[A-Z]:[\\/]|(?:^|[\s\"'(])/(?!/)\S+|[A-Z][A-Z0-9+.-]*://)"
)
PUBLIC_SCOPE_KEYS = ("model", "step", "region", "load_case", "scenario")
STATIC_PASS_STATES = {"pass", "passed", "complete", "reviewed", "success"}


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_scalar(value: Any) -> bool:
    if not isinstance(value, (str, int, float, bool)):
        return False
    if isinstance(value, str) and (
        "\\" in value or EMBEDDED_PATH_OR_URI_PATTERN.search(value)
    ):
        return False
    return True


def _safe_text(value: Any, fallback: str) -> str:
    if not isinstance(value, str) or not value.strip() or not _safe_scalar(value):
        return fallback
    return value.strip()


def _safe_scope(raw_scope: Any) -> dict[str, Any]:
    scope: dict[str, Any] = {}
    if isinstance(raw_scope, dict):
        for key in PUBLIC_SCOPE_KEYS:
            value = raw_scope.get(key)
            if isinstance(value, str) and value.strip() and _safe_scalar(value):
                scope[key] = value.strip()
    return scope or {"model": "abaqus-audit", "step": "static-audit"}


def _digest_from_report(report: dict[str, Any]) -> str | None:
    candidates: list[tuple[str, Any]] = [
        ("input_digest", report.get("input_digest")),
        ("model_input_sha256", report.get("model_input_sha256")),
        ("model_input_digest", report.get("model_input_digest")),
    ]
    model_input = report.get("model_input")
    if isinstance(model_input, dict):
        candidates.extend(
            [
                ("model_input.sha256", model_input.get("sha256")),
                ("model_input.digest", model_input.get("digest")),
            ]
        )
    digests = []
    for key, candidate in candidates:
        if candidate is None:
            continue
        if not isinstance(candidate, str) or not SHA256_PATTERN.fullmatch(candidate):
            raise ValueError(f"report {key} must be a 64-character hexadecimal digest")
        digests.append(candidate.lower())
    if not digests:
        return None
    if len(set(digests)) != 1:
        raise ValueError("report contains conflicting model input digests")
    return digests[0]


def _resolve_model_input(report_path: Path, report: dict[str, Any], supplied: Path | None) -> str:
    reported_digest = _digest_from_report(report)
    if supplied is not None:
        supplied_digest = digest_file(supplied)
        if reported_digest is not None and supplied_digest != reported_digest:
            raise ValueError("model input digest mismatch between report and --model-input")
        return supplied_digest
    if reported_digest:
        return reported_digest
    raw_path: Any = report.get("model_input_path")
    if raw_path is None and isinstance(report.get("model_input"), str):
        raw_path = report["model_input"]
    if isinstance(raw_path, str) and raw_path.strip():
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = report_path.parent / candidate
        return digest_file(candidate)
    raise ValueError("a model input file or model_input_sha256 is required")


def _public_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not PUBLIC_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"{label} must be a public-safe ID matching "
            "[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}"
        )
    return value


def _static_status(value: Any) -> Any:
    if value is None or (isinstance(value, str) and not value.strip()):
        return "required"
    if isinstance(value, str) and value.strip().lower() in STATIC_PASS_STATES:
        return "required"
    return value


def _checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    checks = report.get("checks")
    if not isinstance(checks, list) or not checks:
        checks = report.get("findings")
    if not isinstance(checks, list) or not checks:
        return [{"id": "AUDIT-001", "field": "static-audit-report", "status": "reviewed"}]
    return [item for item in checks if isinstance(item, dict)] or [
        {"id": "AUDIT-001", "field": "static-audit-report", "status": "reviewed"}
    ]


def build_contract(report: dict[str, Any], report_digest: str, model_digest: str) -> dict[str, Any]:
    audit_source = "ABAQUS-AUDIT-REPORT"
    evidence: list[dict[str, Any]] = []
    used_evidence_ids: set[str] = set()
    for index, check in enumerate(_checks(report), start=1):
        check_id = None
        if "id" in check:
            check_id = _public_id(check["id"], f"finding[{index}].id")
        evidence_id = check_id or f"AUDIT-{index:03d}"
        if evidence_id in used_evidence_ids:
            evidence_id = f"AUDIT-{index:03d}"
        while evidence_id in used_evidence_ids:
            evidence_id = f"AUDIT-{index:03d}-{len(used_evidence_ids):02d}"
        used_evidence_ids.add(evidence_id)
        code = _safe_text(check.get("code"), evidence_id)
        location = _safe_text(check.get("location"), "static-audit")
        skill = _safe_text(check.get("skill"), "static-audit")
        evidence.append(
            {
                "id": evidence_id,
                "kind": "static-audit",
                "source_id": audit_source,
                "code": code,
                "location": location,
                "skill": skill,
                "field": _safe_text(
                    check.get("field") or check.get("name"),
                    code,
                ),
                "units": _safe_text(check.get("units"), "n/a"),
                "coordinate_system": _safe_text(
                    check.get("coordinate_system"), "not_applicable"
                ),
                "status": _safe_text(check.get("status"), "reviewed"),
            }
        )
    evidence_ids = [item["id"] for item in evidence]

    raw_claims = report.get("claims")
    claims: list[dict[str, Any]] = []
    used_claim_ids: set[str] = set()
    if isinstance(raw_claims, list):
        for index, claim in enumerate(raw_claims, start=1):
            if not isinstance(claim, dict):
                continue
            claim_id = None
            if "id" in claim:
                claim_id = _public_id(claim["id"], f"claim[{index}].id")
            text = _safe_text(claim.get("text"), "")
            if not text:
                continue
            candidate_id = claim_id or f"CLAIM-{index:03d}"
            if candidate_id in used_claim_ids:
                candidate_id = f"CLAIM-{index:03d}"
            while candidate_id in used_claim_ids:
                candidate_id = f"CLAIM-{index:03d}-{len(used_claim_ids):02d}"
            used_claim_ids.add(candidate_id)
            if "evidence_ids" not in claim:
                refs = evidence_ids
            else:
                refs = claim["evidence_ids"]
                if not isinstance(refs, list) or not refs:
                    raise ValueError(
                        f"claim {candidate_id} has an empty or invalid evidence_ids list"
                    )
                invalid_refs = [
                    ref
                    for ref in refs
                    if not isinstance(ref, str) or ref not in evidence_ids
                ]
                if invalid_refs:
                    raise ValueError(
                        f"claim {candidate_id} references unknown evidence id: {invalid_refs[0]}"
                    )
            claims.append(
                {
                    "id": candidate_id,
                    "text": text,
                    "evidence_ids": list(refs),
                }
            )
    if not claims:
        claims = [
            {
                "id": "CLAIM-001",
                "text": "The static Abaqus audit report is structurally traceable.",
                "evidence_ids": evidence_ids,
            }
        ]
    for claim in claims:
        if not claim["evidence_ids"]:
            claim["evidence_ids"] = evidence_ids

    statuses = report.get("solver_status")
    if not isinstance(statuses, dict):
        statuses = {}
    solver_status = {
        key: _static_status(statuses.get(key))
        for key in ("datacheck", "analysis", "physics_review")
    }
    return {
        "contract_version": "0.2",
        "artifact_id": f"abaqus-static-audit-{report_digest[:16]}",
        "scope": _safe_scope(report.get("scope")),
        "inputs": [
            {
                "name": "model-input",
                "source_id": "ABAQUS-MODEL-INPUT",
                "sha256": model_digest,
                "units": "n/a",
            },
            {
                "name": "audit-report",
                "source_id": audit_source,
                "sha256": report_digest,
                "units": "n/a",
            },
        ],
        "solver_status": solver_status,
        "evidence": evidence,
        "claims": claims,
    }


def convert(report_path: Path, output_path: Path, model_input: Path | None = None) -> bool:
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes.decode("utf-8"))
    if not isinstance(report, dict):
        raise ValueError("report.json must contain a JSON object")
    report_digest = hashlib.sha256(report_bytes).hexdigest()
    model_digest = _resolve_model_input(report_path, report, model_input)
    payload = build_contract(report, report_digest, model_digest)
    rendered = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if os.path.lexists(output_path):
        if output_path.is_symlink():
            raise FileExistsError(f"refusing to overwrite symlink output: {output_path}")
        if not output_path.is_file():
            raise FileExistsError(f"refusing to overwrite non-file output: {output_path}")
        if output_path.read_bytes() == rendered:
            return False
        raise FileExistsError(f"refusing to overwrite different output: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        file_descriptor = os.open(str(output_path), flags, 0o666)
    except FileExistsError as exc:
        raise FileExistsError(
            f"refusing to overwrite colliding output: {output_path}"
        ) from exc
    with os.fdopen(file_descriptor, "wb") as handle:
        handle.write(rendered)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--report", dest="report_option", type=Path)
    parser.add_argument("--output", dest="output_option", type=Path)
    parser.add_argument("--model-input", type=Path)
    args = parser.parse_args(argv)
    report = args.report or args.report_option
    output = args.output or args.output_option
    if report is None or output is None:
        parser.error("report and output paths are required")
    try:
        changed = convert(report, output, args.model_input)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("WROTE" if changed else "UNCHANGED", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
