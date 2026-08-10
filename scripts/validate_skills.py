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
