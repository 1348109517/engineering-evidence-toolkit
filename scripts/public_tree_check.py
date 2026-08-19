#!/usr/bin/env python3
"""Scan the public repository tree without following ignored build material."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable


EXCLUDED_DIRECTORY_NAMES = {".git", ".worktrees", "worktrees", "build", "dist", "__pycache__"}
FORBIDDEN_NAMES = {".env", ".env.local", "credentials.json", "token.json"}
BINARY_SUFFIXES = {".odb", ".cae", ".sim", ".db", ".zip", ".7z", ".png", ".jpg", ".pyc"}
PRIVATE_MARKERS = ("Paper" + "Writing", "D" + ":\\", "1348109517" + "@" + "qq.com")
MAX_PUBLIC_FILE_SIZE = 250_000


def _is_excluded(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRECTORY_NAMES for part in relative.parts)


def _tracked_files(root: Path) -> Iterable[Path] | None:
    if not (root / ".git").exists():
        return None
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    paths = []
    for raw_path in completed.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = Path(raw_path.decode("utf-8", errors="surrogateescape"))
        path = root / relative
        if not _is_excluded(path, root) and (path.is_file() or path.is_symlink()):
            paths.append(path)
    return paths


def iter_public_files(root: Path) -> Iterable[Path]:
    """Yield public files, preferring git-tracked paths when a git root exists."""

    root = Path(root).resolve()
    tracked = _tracked_files(root)
    if tracked is not None:
        yield from sorted(tracked)
        return
    for path in sorted(root.rglob("*")):
        if _is_excluded(path, root) or (not path.is_file() and not path.is_symlink()):
            continue
        yield path


def scan_public_tree(root: Path) -> list[str]:
    """Return deterministic privacy and binary-material findings for ``root``."""

    root = Path(root).resolve()
    errors: list[str] = []
    for path in iter_public_files(root):
        relative = path.relative_to(root)
        label = str(relative)
        if path.is_symlink():
            errors.append(f"symlink is not allowed in public tree: {label}")
            continue
        if path.name.lower() in FORBIDDEN_NAMES:
            errors.append(f"forbidden public filename: {label}")
        if path.suffix.lower() in BINARY_SUFFIXES:
            errors.append(f"binary/private suffix is not allowed: {label}")
        if path.stat().st_size > MAX_PUBLIC_FILE_SIZE:
            errors.append(f"unexpectedly large public file: {label}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"public file is not UTF-8 text: {label}")
            continue
        for marker in PRIVATE_MARKERS:
            if marker in text:
                errors.append(f"private marker {marker!r} found in: {label}")
    return sorted(errors)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = scan_public_tree(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Public tree privacy scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
