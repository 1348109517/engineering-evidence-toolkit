#!/usr/bin/env python3
"""Dependency-free CI validation for the repository's skill frontmatter."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    skill_file = path / "SKILL.md"
    if not skill_file.is_file():
        return [f"{path}: SKILL.md not found"]
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return [f"{skill_file}: invalid frontmatter"]
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    if set(fields) != {"name", "description"}:
        errors.append(f"{skill_file}: frontmatter must contain only name and description")
    name = fields.get("name", "")
    if name != path.name or not re.fullmatch(r"[a-z0-9-]+", name):
        errors.append(f"{skill_file}: name must match its hyphen-case directory")
    if not fields.get("description", "").startswith("Use when "):
        errors.append(f"{skill_file}: description must start with 'Use when '")

    metadata_file = path / "agents" / "openai.yaml"
    if not metadata_file.is_file():
        errors.append(f"{metadata_file}: metadata file not found")
    else:
        metadata_fields = {}
        for line in metadata_file.read_text(encoding="utf-8").splitlines():
            match = re.match(r'^\s{2}([a-z_]+):\s*"(.*)"$', line)
            if match:
                metadata_fields[match.group(1)] = match.group(2)
        expected_fields = {"display_name", "short_description", "default_prompt"}
        if set(metadata_fields) != expected_fields:
            errors.append(
                f"{metadata_file}: interface must contain exactly "
                "display_name, short_description, and default_prompt"
            )
        if not metadata_fields.get("display_name", "").strip():
            errors.append(f"{metadata_file}: display_name must be non-empty")
        if len(metadata_fields.get("short_description", "")) not in range(25, 65):
            errors.append(f"{metadata_file}: short_description must be 25-64 characters")
        if f"${name}" not in metadata_fields.get("default_prompt", ""):
            errors.append(f"{metadata_file}: default_prompt must mention ${name}")
        if re.search(r"openai|chatgpt|codex", metadata_file.read_text(encoding="utf-8"), re.I):
            errors.append(f"{metadata_file}: branding is not allowed")

    routing = re.search(
        r"## Routing cases\n\n### Positive routing cases\n(?P<positive>.*?)(?=\n### Negative routing cases)",
        text,
        re.DOTALL,
    )
    negative = re.search(
        r"### Negative routing cases\n(?P<negative>.*?)(?=\n## |\Z)",
        text,
        re.DOTALL,
    )
    if routing is None or negative is None:
        errors.append(f"{skill_file}: routing corpus headings are required")
    else:
        positive_count = len(re.findall(r"(?m)^\d+\. ", routing.group("positive")))
        negative_count = len(re.findall(r"(?m)^\d+\. ", negative.group("negative")))
        if positive_count != 3 or negative_count != 2:
            errors.append(
                f"{skill_file}: routing corpus must contain 3 positive and 2 negative cases"
            )
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = []
    for path in sorted((root / "skills").iterdir()):
        if path.is_dir():
            errors.extend(validate(path))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("All skill frontmatter checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
