import json
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

from scripts.evidence_check import validate_contract


ROOT = Path(__file__).resolve().parents[1]


def make_contract(version="0.2", statuses=None, evidence=None, claims=None):
    statuses = statuses or {
        "datacheck": "complete",
        "analysis": "passed",
        "physics_review": "reviewed",
    }
    evidence = evidence or [
        {
            "id": "E-FIELD-001",
            "kind": "field",
            "source_id": "SYN-IN-001",
            "field": "U2",
            "frame": 4,
            "units": "m",
            "coordinate_system": "global",
        },
        {
            "id": "E-STATIC-001",
            "kind": "static-audit",
            "source_id": "SYN-IN-001",
            "field": "boundary-condition-check",
            "units": "n/a",
            "coordinate_system": "not_applicable",
        },
    ]
    claims = claims or [
        {
            "id": "C-001",
            "text": "The synthetic audit is structurally traceable.",
            "evidence_ids": ["E-FIELD-001", "E-STATIC-001"],
        }
    ]
    return {
        "contract_version": version,
        "artifact_id": "synthetic-v020",
        "scope": {"model": "synthetic", "step": "Step-1"},
        "inputs": [
            {
                "name": "synthetic-input",
                "source_id": "SYN-IN-001",
                "sha256": "a" * 64,
                "units": "SI",
            }
        ],
        "solver_status": statuses,
        "evidence": evidence,
        "claims": claims,
    }


class EvidenceContractV020Tests(unittest.TestCase):
    def assert_verdict(self, payload, expected, fragment=None):
        verdict, messages = validate_contract(payload)
        self.assertEqual(verdict, expected, messages)
        if fragment:
            self.assertTrue(
                any(fragment in message for message in messages),
                messages,
            )

    def test_accepts_v020_static_audit_without_frame_or_time(self):
        self.assert_verdict(make_contract(), "PASS")

    def test_accepts_existing_v010_example(self):
        payload = json.loads(
            (ROOT / "examples" / "synthetic" / "contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assert_verdict(payload, "PASS")

    def test_rejects_non_hex_sha256(self):
        payload = make_contract()
        payload["inputs"][0]["sha256"] = "g" * 64
        self.assert_verdict(payload, "BLOCKED", "64-character hexadecimal")

    def test_rejects_duplicate_evidence_ids(self):
        payload = make_contract()
        payload["evidence"][1]["id"] = payload["evidence"][0]["id"]
        self.assert_verdict(payload, "BLOCKED", "duplicate evidence id")

    def test_rejects_duplicate_claim_ids(self):
        payload = make_contract()
        payload["claims"].append(
            {
                "id": payload["claims"][0]["id"],
                "text": "A second claim.",
                "evidence_ids": ["E-FIELD-001"],
            }
        )
        self.assert_verdict(payload, "BLOCKED", "duplicate claim id")

    def test_rejects_duplicate_input_source_ids_in_v020(self):
        payload = make_contract()
        payload["inputs"].append(
            {
                **payload["inputs"][0],
                "name": "duplicate-source",
            }
        )
        self.assert_verdict(payload, "BLOCKED", "duplicate input source id")

    def test_rejects_unresolved_evidence_source_id_in_v020(self):
        payload = make_contract()
        payload["evidence"][0]["source_id"] = "SYN-MISSING-001"
        self.assert_verdict(payload, "BLOCKED", "unknown input source id")

    def test_rejects_unresolvable_claim_reference(self):
        payload = make_contract()
        payload["claims"][0]["evidence_ids"] = ["E-MISSING"]
        self.assert_verdict(payload, "BLOCKED", "unknown evidence id")

    def test_field_and_history_need_frame_or_time(self):
        for kind in ("field", "history"):
            payload = make_contract(
                evidence=[
                    {
                        "id": "E-001",
                        "kind": kind,
                        "source_id": "SYN-IN-001",
                        "field": "U2",
                        "units": "m",
                        "coordinate_system": "global",
                    }
                ],
                claims=[
                    {
                        "id": "C-001",
                        "text": "A scoped observation.",
                        "evidence_ids": ["E-001"],
                    }
                ],
            )
            self.assert_verdict(payload, "BLOCKED", "frame or time")

    def test_field_and_history_temporal_markers_are_valid_scalars(self):
        invalid_markers = (
            {"frame": -1},
            {"frame": True},
            {"frame": 1.0},
            {"frame": []},
            {"time": -0.1},
            {"time": True},
            {"time": float("nan")},
            {"time": []},
        )
        for marker in invalid_markers:
            for kind in ("field", "history"):
                evidence = [
                    {
                        "id": "E-001",
                        "kind": kind,
                        "source_id": "SYN-IN-001",
                        "field": "U2",
                        **marker,
                        "units": "m",
                        "coordinate_system": "global",
                    }
                ]
                claims = [
                    {
                        "id": "C-001",
                        "text": "A scoped observation.",
                        "evidence_ids": ["E-001"],
                    }
                ]
                self.assert_verdict(
                    make_contract(evidence=evidence, claims=claims),
                    "BLOCKED",
                    "frame/time",
                )

    def test_field_and_history_accept_valid_temporal_scalars(self):
        valid_markers = ({"frame": 0}, {"frame": 4}, {"time": 0}, {"time": 1.25})
        for marker in valid_markers:
            evidence = [
                {
                    "id": "E-001",
                    "kind": "field",
                    "source_id": "SYN-IN-001",
                    "field": "U2",
                    **marker,
                    "units": "m",
                    "coordinate_system": "global",
                }
            ]
            claims = [
                {
                    "id": "C-001",
                    "text": "A scoped observation.",
                    "evidence_ids": ["E-001"],
                }
            ]
            self.assert_verdict(
                make_contract(evidence=evidence, claims=claims), "PASS"
            )

    def test_static_audit_and_document_do_not_need_frame_or_time(self):
        for kind in ("static-audit", "document"):
            evidence = [
                {
                    "id": "E-001",
                    "kind": kind,
                    "source_id": "SYN-IN-001",
                    "field": "audit",
                    "units": "n/a",
                    "coordinate_system": "not_applicable",
                }
            ]
            claims = [
                {
                    "id": "C-001",
                    "text": "A static observation.",
                    "evidence_ids": ["E-001"],
                }
            ]
            self.assert_verdict(
                make_contract(evidence=evidence, claims=claims), "PASS"
            )

    def test_lifecycle_states_are_conditional(self):
        for state in ("not_run", "pending", "required"):
            statuses = {
                "datacheck": "complete",
                "analysis": "complete",
                "physics_review": state,
            }
            self.assert_verdict(make_contract(statuses=statuses), "CONDITIONAL")

    def test_lifecycle_states_are_blocked(self):
        for state in ("failed", "rejected", "blocked"):
            statuses = {
                "datacheck": "complete",
                "analysis": "complete",
                "physics_review": state,
            }
            self.assert_verdict(make_contract(statuses=statuses), "BLOCKED")

    def test_unknown_lifecycle_state_is_structural_block(self):
        statuses = {
            "datacheck": "complete",
            "analysis": "complete",
            "physics_review": "maybe",
        }
        self.assert_verdict(make_contract(statuses=statuses), "BLOCKED", "status")

    def test_failed_datacheck_blocks_even_when_physics_review_passes(self):
        statuses = {
            "datacheck": "failed",
            "analysis": "complete",
            "physics_review": "passed",
        }
        self.assert_verdict(make_contract(statuses=statuses), "BLOCKED")

    def test_pending_analysis_is_conditional_even_when_physics_review_passes(self):
        statuses = {
            "datacheck": "complete",
            "analysis": "pending",
            "physics_review": "passed",
        }
        self.assert_verdict(make_contract(statuses=statuses), "CONDITIONAL")

    def test_solver_status_precedence_checks_all_three_statuses(self):
        cases = [
            (
                {"datacheck": "failed", "analysis": "pending", "physics_review": "passed"},
                "BLOCKED",
            ),
            (
                {"datacheck": "complete", "analysis": "pending", "physics_review": "reviewed"},
                "CONDITIONAL",
            ),
            (
                {"datacheck": "complete", "analysis": "complete", "physics_review": "reviewed"},
                "PASS",
            ),
        ]
        for statuses, expected in cases:
            self.assert_verdict(make_contract(statuses=statuses), expected)


if __name__ == "__main__":
    unittest.main()
