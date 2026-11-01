"""Lists a source's ingestible files from metadata alone (path, size, modified time), cheap enough to run every second.

Skipped: the default folders below, anything a `.gitignore` inside the source ignores, the source's own exclude
patterns, files over MAX_FILE_BYTES, and files not matching the include patterns (Markdown, text and code by default).
Patterns use .gitignore syntax.
"""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from pathspec import GitIgnoreSpec

DEFAULT_EXCLUDES = [
    ".git/",
    "node_modules/",
    ".venv/",
    "venv/",
    "__pycache__/",
    ".obsidian/",
    ".trash/",
    "dist/",
    "build/",
    ".next/",
    "target/",
    ".idea/",
    ".vscode/",
]
DEFAULT_INCLUDES = [
    "*.md",
    "*.markdown",
    "*.txt",
    "*.rst",
    "*.py",
    "*.ts",
    "*.tsx",
    "*.js",
    "*.jsx",
    "*.json",
    "*.yaml",
    "*.yml",
    "*.toml",
    "*.sql",
    "*.sh",
    "*.ps1",
    "*.cs",
    "*.java",
    "*.go",
    "*.rs",
    "*.c",
    "*.h",
    "*.cpp",
    "*.hpp",
    "*.css",
    "*.html",
]
MAX_FILE_BYTES = 2_000_000


@dataclass(frozen=True)
class ScannedFile:
    path: str
    """Relative to the source root, with forward slashes."""
    size: int
    modified_ns: int


@dataclass(frozen=True)
class ScanResult:
    files: tuple[ScannedFile, ...]
    fingerprint: str


@dataclass(frozen=True)
class FileChanges:
    added: int
    removed: int
    modified: int


def pattern_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def fingerprint(files: tuple[ScannedFile, ...]) -> str:
    listing = "\n".join(f"{file.path}\t{file.size}\t{file.modified_ns}" for file in files)
    return hashlib.sha256(listing.encode()).hexdigest()


def file_changes(before: tuple[ScannedFile, ...], after: tuple[ScannedFile, ...]) -> FileChanges:
    old = {file.path: file for file in before}
    new = {file.path: file for file in after}
    return FileChanges(
        added=len(new.keys() - old.keys()),
        removed=len(old.keys() - new.keys()),
        modified=sum(old[path] != new[path] for path in old.keys() & new.keys()),
    )


class IgnoreRules:
    """Default and source-level excludes plus every `.gitignore` found while walking, each relative to its folder."""

    def __init__(self, excludes: list[str]) -> None:
        self._excludes = GitIgnoreSpec.from_lines(DEFAULT_EXCLUDES + excludes)
        self._gitignores: list[tuple[PurePosixPath, GitIgnoreSpec]] = []

    def add_gitignore(self, folder: PurePosixPath, text: str) -> None:
        self._gitignores.append((folder, GitIgnoreSpec.from_lines(text.splitlines())))

    def ignores(self, path: PurePosixPath, is_dir: bool) -> bool:
        suffix = "/" if is_dir else ""
        if self._excludes.match_file(f"{path}{suffix}"):
            return True
        return any(
            spec.match_file(f"{path.relative_to(folder)}{suffix}")
            for folder, spec in self._gitignores
            if path.is_relative_to(folder) and path != folder
        )


def _relative(root: Path, directory: str) -> PurePosixPath:
    relative = Path(directory).relative_to(root).as_posix()
    return PurePosixPath("" if relative == "." else relative)


def scan_source(root: Path, include_patterns: list[str], exclude_patterns: list[str]) -> ScanResult:
    includes = GitIgnoreSpec.from_lines(include_patterns or DEFAULT_INCLUDES)
    rules = IgnoreRules(exclude_patterns)
    files = []
    for directory, folders, names in os.walk(root):
        folder = _relative(root, directory)
        if ".gitignore" in names:
            rules.add_gitignore(folder, (Path(directory) / ".gitignore").read_text(encoding="utf-8", errors="replace"))
        folders[:] = sorted(name for name in folders if not rules.ignores(folder / name, is_dir=True))
        for name in sorted(names):
            path = folder / name
            if rules.ignores(path, is_dir=False) or not includes.match_file(str(path)):
                continue
            status = (Path(directory) / name).stat()
            if status.st_size <= MAX_FILE_BYTES:
                files.append(ScannedFile(path=str(path), size=status.st_size, modified_ns=status.st_mtime_ns))
    ordered = tuple(sorted(files, key=lambda file: file.path))
    return ScanResult(files=ordered, fingerprint=fingerprint(ordered))
