import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.dont_write_bytecode = True

from scripts import from_abaqus_audit as adapter


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "from_abaqus_audit.py"
CHECKER = ROOT / "scripts" / "evidence_check.py"


class AbaqusAuditAdapterTests(unittest.TestCase):
    def write_inputs(self, folder):
        model = folder / "model.inp"
        model.write_text("*HEADING\nSynthetic public fixture\n", encoding="utf-8")
        report = folder / "report.json"
        report.write_text(
            json.dumps(
                {
                    "artifact_id": "synthetic-abaqus-audit",
                    "scope": {"model": "synthetic", "step": "static-audit"},
                    "solver_status": {
                        "datacheck": "complete",
                        "analysis": "complete",
                        "physics_review": "required",
                    },
                    "checks": [
                        {
                            "id": "AUDIT-001",
                            "name": "boundary-condition-inventory",
                            "status": "passed",
                            "note": "All synthetic supports are named.",
                        }
                    ],
                    "claims": [
                        {
                            "id": "CLAIM-001",
                            "text": "The static audit inventory is complete.",
                        }
                    ],
                    "redacted_path": "REDACTED_PATH",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return model, report

    def run_adapter(self, report, output, model):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(report),
                str(output),
                "--model-input",
                str(model),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_writes_deterministic_static_only_v020_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            output = folder / "contract.json"
            completed = self.run_adapter(report, output, model)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["contract_version"], "0.2")
            self.assertEqual(
                {row["kind"] for row in payload["evidence"]}, {"static-audit"}
            )
            self.assertEqual(
                payload["inputs"][0]["sha256"],
                hashlib.sha256(model.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                payload["inputs"][1]["sha256"],
                hashlib.sha256(report.read_bytes()).hexdigest(),
            )
            output_text = output.read_text(encoding="utf-8")
            self.assertNotIn("REDACTED_PATH", output_text)
            self.assertNotIn("timestamp", output_text.lower())
            checked = subprocess.run(
                [sys.executable, str(CHECKER), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 2, checked.stderr)
            self.assertIn("CONDITIONAL", checked.stdout)

            first = output.read_bytes()
            repeated = self.run_adapter(report, output, model)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(output.read_bytes(), first)

    def test_static_adapter_downgrades_solver_pass_states_to_required(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            payload = json.loads(report.read_text(encoding="utf-8"))
            payload["solver_status"] = {
                "datacheck": "complete",
                "analysis": "passed",
                "physics_review": "reviewed",
            }
            report.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            output = folder / "contract.json"
            completed = self.run_adapter(report, output, model)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            generated = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                generated["solver_status"],
                {
                    "datacheck": "required",
                    "analysis": "required",
                    "physics_review": "required",
                },
            )
            checked = subprocess.run(
                [sys.executable, str(CHECKER), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 2, checked.stderr)
            self.assertIn("CONDITIONAL", checked.stdout)

    def test_rejects_unsafe_finding_id_without_writing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            payload = json.loads(report.read_text(encoding="utf-8"))
            payload["checks"][0]["id"] = "../private-finding"
            report.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            output = folder / "contract.json"
            completed = self.run_adapter(report, output, model)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("public-safe", completed.stderr.lower())
            self.assertFalse(output.exists())

    def test_rejects_unsafe_claim_id_without_writing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            payload = json.loads(report.read_text(encoding="utf-8"))
            payload["claims"][0]["id"] = "claim/operator.txt"
            report.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            output = folder / "contract.json"
            completed = self.run_adapter(report, output, model)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("public-safe", completed.stderr.lower())
            self.assertFalse(output.exists())

    def test_scope_keeps_only_public_allowlisted_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            payload = json.loads(report.read_text(encoding="utf-8"))
            payload["scope"] = {
                "model": "synthetic",
                "step": "static-audit",
                "region": "crown",
                "path": "C:" + "\\private\\model.inp",
                "timestamp": "2026-08-20T00:00:00Z",
                "owner": "private-owner",
                "operator": "private-operator",
            }
            report.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            output = folder / "contract.json"
            completed = self.run_adapter(report, output, model)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            generated = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                generated["scope"],
                {"model": "synthetic", "region": "crown", "step": "static-audit"},
            )
            output_text = output.read_text(encoding="utf-8")
            self.assertNotIn("private-owner", output_text)
            self.assertNotIn("private-operator", output_text)
            self.assertNotIn("timestamp", output_text.lower())
            self.assertNotIn("C:" + "\\\\private", output_text)

    def test_embedded_paths_and_uris_are_removed_from_emitted_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            payload = json.loads(report.read_text(encoding="utf-8"))
            payload["scope"] = {
                "model": "report at " + "C:" + "/Users/private/model.inp",
                "step": "static-audit",
            }
            payload["checks"][0]["location"] = "source file:///tmp/private/audit.json"
            payload["claims"][0]["text"] = "Review /home/private/audit.json before release."
            report.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            output = folder / "contract.json"
            completed = self.run_adapter(report, output, model)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output_text = output.read_text(encoding="utf-8")
            for marker in ("C:" + "/Users/", "/home/", "file://"):
                self.assertNotIn(marker, output_text)

    def test_model_input_digest_mismatch_is_rejected_without_writing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            payload = json.loads(report.read_text(encoding="utf-8"))
            payload["input_digest"] = "d" * 64
            report.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            output = folder / "contract.json"
            completed = self.run_adapter(report, output, model)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("digest mismatch", completed.stderr.lower())
            self.assertFalse(output.exists())

    def test_refuses_to_overwrite_different_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            output = folder / "contract.json"
            output.write_text('{"artifact_id":"different"}\n', encoding="utf-8")
            before = output.read_bytes()
            completed = self.run_adapter(report, output, model)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("refusing", completed.stderr.lower())
            self.assertEqual(output.read_bytes(), before)

    def test_public_synthetic_fixtures_convert(self):
        model = ROOT / "tests" / "fixtures" / "synthetic_model.inp"
        report = ROOT / "tests" / "fixtures" / "abaqus_report.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "contract.json"
            completed = self.run_adapter(report, output, model)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["scope"]["model"], "synthetic")
            self.assertEqual(payload["evidence"][0]["kind"], "static-audit")

    def test_actual_abaqus_agent_report_shape_uses_input_digest_and_findings(self):
        report = ROOT / "tests" / "fixtures" / "abaqus_agent_report.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "contract.json"
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(report), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["inputs"][0]["sha256"], "c" * 64)
            self.assertEqual(
                len(payload["evidence"]),
                2,
            )
            first, second = payload["evidence"]
            self.assertEqual(first["code"], "BC-001")
            self.assertEqual(first["location"], "model.boundary_conditions")
            self.assertEqual(first["skill"], "abaqus-bc")
            self.assertEqual(second["code"], "LOAD-002")
            self.assertEqual(second["location"], "loads.mapping")
            self.assertEqual(second["skill"], "abaqus-load")
            self.assertNotIn("next_action", output.read_text(encoding="utf-8"))

    def test_unknown_explicit_claim_reference_rejects_without_writing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            payload = json.loads(report.read_text(encoding="utf-8"))
            payload["claims"][0]["evidence_ids"] = ["E-NOT-PRESENT"]
            report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            output = folder / "contract.json"
            completed = self.run_adapter(report, output, model)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("unknown evidence id", completed.stderr.lower())
            self.assertFalse(output.exists())

    def test_invalid_explicit_lifecycle_state_is_preserved_for_checker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            payload = json.loads(report.read_text(encoding="utf-8"))
            payload["solver_status"]["analysis"] = "mystery-state"
            report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            output = folder / "contract.json"
            completed = self.run_adapter(report, output, model)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            generated = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(generated["solver_status"]["analysis"], "mystery-state")
            checked = subprocess.run(
                [sys.executable, str(CHECKER), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 1)
            self.assertIn("unsupported lifecycle", checked.stderr)

    def _make_symlink_or_skip(self, link, target):
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink unavailable on this platform: {exc}")

    def test_existing_symlink_and_dangling_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            target = folder / "target.json"
            target.write_text("unchanged\n", encoding="utf-8")
            link = folder / "contract.json"
            self._make_symlink_or_skip(link, target)
            completed = self.run_adapter(report, link, model)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("symlink", completed.stderr.lower())
            self.assertEqual(target.read_text(encoding="utf-8"), "unchanged\n")

            link.unlink()
            dangling_target = folder / "does-not-exist.json"
            self._make_symlink_or_skip(link, dangling_target)
            completed = self.run_adapter(report, link, model)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("symlink", completed.stderr.lower())
            self.assertTrue(link.is_symlink())

    def test_existing_non_file_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            output = folder / "contract.json"
            output.mkdir()
            completed = self.run_adapter(report, output, model)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("non-file", completed.stderr.lower())

    def test_exclusive_creation_rejects_race_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            model, report = self.write_inputs(folder)
            output = folder / "contract.json"
            real_open = os.open

            def create_collision(path, flags, mode=0o666):
                Path(path).write_text("race\n", encoding="utf-8")
                return real_open(path, flags, mode)

            with patch.object(adapter.os, "open", side_effect=create_collision):
                with self.assertRaises(FileExistsError):
                    adapter.convert(report, output, model)
            self.assertEqual(output.read_text(encoding="utf-8"), "race\n")


if __name__ == "__main__":
    unittest.main()
