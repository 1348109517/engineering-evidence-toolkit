import hashlib
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.public_tree_check import scan_public_tree, iter_public_files


ROOT = Path(__file__).resolve().parents[1]
SKILLS = [
    "evidence-contract",
    "provenance-ledger",
    "solver-status-gate",
    "result-audit",
    "claim-readiness-audit",
    "reproducible-reporting",
]


class RepositoryV020Tests(unittest.TestCase):
    def test_license_is_the_recognized_canonical_apache_text(self):
        digest = hashlib.sha256((ROOT / "LICENSE").read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "0a28dc2bc51bba69be636ef35f3dfcbb98aab20b05957809f257a85c32466a25",
        )

    def test_citation_identifies_mid_mountain_v020(self):
        citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
        self.assertEqual(citation["cff-version"], "1.2.0")
        self.assertEqual(citation["title"], "Engineering Evidence Toolkit")
        self.assertEqual(citation["version"], "0.2.0")
        self.assertEqual(citation["license"], "Apache-2.0")
        self.assertTrue(any(author.get("name") == "Mid-Mountain" for author in citation["authors"]))

    def test_ci_has_ubuntu_windows_python_310_312_matrix(self):
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )
        self.assertRegex(workflow, r"os:\s*\[ubuntu-latest,\s*windows-latest\]")
        self.assertRegex(workflow, r'python-version:\s*\["3\.10",\s*"3\.12"\]')
        self.assertIn("${{ matrix.os }}", workflow)
        self.assertIn("${{ matrix.python-version }}", workflow)

    def test_all_skills_have_unbranded_metadata_with_exact_skill_prompt(self):
        for skill_name in SKILLS:
            metadata_path = ROOT / "skills" / skill_name / "agents" / "openai.yaml"
            self.assertTrue(metadata_path.is_file(), metadata_path)
            raw = metadata_path.read_text(encoding="utf-8")
            metadata = yaml.safe_load(raw)
            interface = metadata.get("interface", {})
            self.assertEqual(
                set(interface), {"display_name", "short_description", "default_prompt"}
            )
            self.assertTrue(interface["display_name"].strip())
            self.assertTrue(25 <= len(interface["short_description"]) <= 64)
            self.assertIn(f"${skill_name}", interface["default_prompt"])
            self.assertNotRegex(raw, re.compile(r"openai|chatgpt|codex", re.IGNORECASE))

    def test_each_skill_has_exactly_three_positive_and_two_negative_routes(self):
        for skill_name in SKILLS:
            text = (ROOT / "skills" / skill_name / "SKILL.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("## Routing cases", text, skill_name)
            positive = re.search(
                r"### Positive routing cases\n(?P<body>.*?)(?=\n### Negative routing cases)",
                text,
                re.DOTALL,
            )
            negative = re.search(
                r"### Negative routing cases\n(?P<body>.*?)(?=\n## |\Z)",
                text,
                re.DOTALL,
            )
            self.assertIsNotNone(positive, skill_name)
            self.assertIsNotNone(negative, skill_name)
            self.assertEqual(
                len(re.findall(r"(?m)^\d+\. ", positive.group("body"))), 3
            )
            self.assertEqual(
                len(re.findall(r"(?m)^\d+\. ", negative.group("body"))), 2
            )

    def test_git_tracked_scan_includes_tests_and_notice_but_excludes_ignored_trees(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
            notice = root / "NOTICE"
            notice.write_text("Paper" + "Writing marker", encoding="utf-8")
            test_file = root / "tests" / "tracked_sensitive.txt"
            test_file.parent.mkdir()
            test_file.write_text("1348109517" + "@" + "qq.com marker", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "NOTICE", "tests/tracked_sensitive.txt"],
                check=True,
                capture_output=True,
            )
            for relative in (
                ".worktrees/ignored.txt",
                "worktrees/ignored.txt",
                "build/ignored.txt",
                "dist/ignored.txt",
                "__pycache__/ignored.pyc",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("D" + ":\\private marker", encoding="utf-8")

            files = set(iter_public_files(root))
            self.assertIn(notice, files)
            self.assertIn(test_file, files)
            self.assertNotIn(root / ".worktrees" / "ignored.txt", files)
            self.assertNotIn(root / "build" / "ignored.txt", files)
            errors = scan_public_tree(root)
            self.assertTrue(any("NOTICE" in error for error in errors), errors)
            self.assertTrue(any("tracked_sensitive" in error for error in errors), errors)
            self.assertFalse(any("ignored" in error for error in errors), errors)

    def test_public_tree_reports_fallback_symlink(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target.txt"
            target.write_text("public target", encoding="utf-8")
            link = root / "link.txt"
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink unavailable on this platform: {exc}")
            errors = scan_public_tree(root)
            self.assertTrue(any("symlink" in error.lower() for error in errors), errors)

    def test_public_tree_reports_tracked_symlink(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
            target = root / "target.txt"
            target.write_text("public target", encoding="utf-8")
            link = root / "link.txt"
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink unavailable on this platform: {exc}")
            subprocess.run(
                ["git", "-C", str(root), "add", "target.txt", "link.txt"],
                check=True,
                capture_output=True,
            )
            errors = scan_public_tree(root)
            self.assertTrue(any("symlink" in error.lower() for error in errors), errors)

    def test_public_tree_falls_back_when_git_invocation_raises_oserror(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()
            notice = root / "NOTICE"
            notice.write_text("public notice", encoding="utf-8")
            with patch(
                "scripts.public_tree_check.subprocess.run",
                side_effect=OSError("git unavailable"),
            ):
                files = set(iter_public_files(root))
            self.assertIn(notice, files)

    def test_public_cross_repo_example_is_deterministic_and_conditional(self):
        report = ROOT / "examples" / "cross-repo" / "abaqus-agent-report.json"
        self.assertTrue(report.is_file(), report)
        adapter = ROOT / "scripts" / "from_abaqus_audit.py"
        checker = ROOT / "scripts" / "evidence_check.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "contract.json"
            first = subprocess.run(
                [sys.executable, str(adapter), str(report), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            first_bytes = output.read_bytes()
            second = subprocess.run(
                [sys.executable, str(adapter), str(report), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(output.read_bytes(), first_bytes)
            checked = subprocess.run(
                [sys.executable, str(checker), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 2, checked.stderr)
            self.assertIn("CONDITIONAL", checked.stdout)
            generated = output.read_text(encoding="utf-8")
            self.assertNotIn("timestamp", generated.lower())
            self.assertNotIn("date-released", generated.lower())
            self.assertNotIn("C:" + "\\", generated)


if __name__ == "__main__":
    unittest.main()
