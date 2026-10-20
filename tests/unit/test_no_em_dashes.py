"""Repo-wide guard against em dashes.

Em dashes are disallowed: the package's rendered output is ASCII only apart
from the intentional evidence markers (checkmark / warning / cross), and
library output is frequently piped, diffed, or pasted into terminals where
non-ASCII punctuation renders inconsistently.

En dashes are allowed in prose for numeric ranges. Only U+2014 is rejected.

Renaming or moving this file is fine; keep the guard.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# No em dash is permitted anywhere in tracked text files.
EM_DASH = "\u2014"

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".cfg",
    ".ini",
    ".yml",
    ".yaml",
    ".json",
    ".rst",
}


def _tracked_text_files() -> list[Path]:
    """Return tracked files, excluding binaries and build artefacts."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git checkout (e.g. an installed sdist): fall back to the
        # package source tree so the guard still runs where it matters.
        root = Path(__file__).resolve().parent.parent
        return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]

    files: list[Path] = []
    for name in out.split("\0"):
        if not name:
            continue
        path = Path(name)
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if "__pycache__" in path.parts or ".egg-info" in str(path):
            continue
        files.append(path)
    return files


def test_no_em_dashes_in_tracked_files() -> None:
    offenders: list[str] = []
    for path in _tracked_text_files():
        try:
            contents = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(contents.splitlines(), start=1):
            if EM_DASH in line:
                offenders.append(f"{path}:{lineno}: {line.strip()}")

    assert not offenders, (
        "Em dash (U+2014) found; use a plain ASCII hyphen instead:\n"
        + "\n".join(offenders)
    )
