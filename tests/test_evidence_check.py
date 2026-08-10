import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "evidence_check.py"
EXAMPLE = ROOT / "examples" / "synthetic" / "contract.json"


class EvidenceCheckerTests(unittest.TestCase):
    def run_checker(self, payload):
        with tempfile.TemporaryDirectory() as temp_dir:
            contract_path = Path(temp_dir) / "contract.json"
            contract_path.write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(CHECKER), str(contract_path)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_synthetic_example_passes(self):
        completed = subprocess.run(
            [sys.executable, str(CHECKER), str(EXAMPLE)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS", completed.stdout)

    def test_missing_provenance_is_rejected(self):
        payload = {
            "contract_version": "0.1",
            "artifact_id": "bad-example",
            "scope": {"model": "synthetic", "step": "Step-1"},
            "inputs": [],
            "solver_status": {
                "datacheck": "pass",
                "analysis": "complete",
                "physics_review": "required",
            },
            "evidence": [],
            "claims": [],
        }
        completed = self.run_checker(payload)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("inputs", completed.stderr)

    def test_solver_completion_without_physics_review_is_conditional(self):
        payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        payload["solver_status"]["physics_review"] = "not_started"
        completed = self.run_checker(payload)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("CONDITIONAL", completed.stdout)


if __name__ == "__main__":
    unittest.main()
