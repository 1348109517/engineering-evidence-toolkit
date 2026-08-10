import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = [
    "evidence-contract",
    "provenance-ledger",
    "solver-status-gate",
    "result-audit",
    "claim-readiness-audit",
    "reproducible-reporting",
]
REQUIRED_HEADINGS = [
    "When to use",
    "Inputs",
    "Outputs",
    "Safety gates",
    "Example prompts",
    "Common failures",
    "Acceptance checklist",
]


class RepositoryStructureTests(unittest.TestCase):
    def test_expected_skills_have_valid_frontmatter_and_sections(self):
        for skill_name in SKILLS:
            skill_path = ROOT / "skills" / skill_name / "SKILL.md"
            self.assertTrue(skill_path.is_file(), skill_path)
            text = skill_path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), skill_path)
            frontmatter, body = text.split("---\n", 2)[1:]
            self.assertRegex(frontmatter, rf"(?m)^name: {re.escape(skill_name)}$")
            description = re.search(r"(?m)^description: (.+)$", frontmatter)
            self.assertIsNotNone(description, skill_path)
            self.assertTrue(description.group(1).startswith("Use when "), skill_path)
            for heading in REQUIRED_HEADINGS:
                self.assertIn(f"## {heading}", body, (skill_path, heading))

    def test_repository_docs_and_ci_are_present(self):
        required = [
            "README.md",
            "README.zh-CN.md",
            "LICENSE",
            "NOTICE",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CODE_OF_CONDUCT.md",
            "CHANGELOG.md",
            "ROADMAP.md",
            "docs/architecture.md",
            "docs/quickstart.md",
            "docs/claim-lifecycle.md",
            ".github/workflows/validate.yml",
            "scripts/evidence_check.py",
            "examples/synthetic/README.md",
            "examples/synthetic/contract.json",
        ]
        for relative_path in required:
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

    def test_readme_links_to_every_skill(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for skill_name in SKILLS:
            self.assertIn(f"skills/{skill_name}/SKILL.md", readme)

    def test_public_tree_excludes_private_or_binary_material(self):
        forbidden_names = {".env", ".env.local", "credentials.json", "token.json"}
        binary_suffixes = {".odb", ".cae", ".sim", ".db", ".zip", ".7z", ".png", ".jpg"}
        private_markers = ["Paper" + "Writing", "D" + ":\\", "1348109517" + "@" + "qq.com"]
        for path in ROOT.rglob("*"):
            if ".git" in path.parts or "tests" in path.parts or not path.is_file():
                continue
            self.assertNotIn(path.name.lower(), forbidden_names, path)
            self.assertNotIn(path.suffix.lower(), binary_suffixes, path)
            if path.stat().st_size > 250_000:
                self.fail(f"unexpectedly large public file: {path}")
            text = path.read_text(encoding="utf-8")
            for marker in private_markers:
                self.assertNotIn(marker, text, path)


if __name__ == "__main__":
    unittest.main()
