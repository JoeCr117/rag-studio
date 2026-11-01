"""Hover explanations for the UI, read from the RAGStudioVault Obsidian vault: a note is found by its unique name in any
folder, and its first paragraph is the explanation."""

import glob
import re
from dataclasses import dataclass
from pathlib import Path

WIKILINK = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]")
"""`[[Note]]` -> Note and `[[Note|shown text]]` -> shown text."""
FORMATTING = re.compile(r"\*\*|`")


@dataclass(frozen=True)
class GlossaryNote:
    name: str
    summary: str
    path: str
    """Relative to the vault, without `.md`: what an `obsidian://open` link needs."""


def find_note(vault_dir: Path, name: str) -> Path | None:
    """Rejects names that could reach outside the vault or match more than a file name."""
    if not name or name.startswith(".") or any(character in name for character in "/\\"):
        return None
    return next(vault_dir.rglob(glob.escape(f"{name}.md")), None)


def first_paragraph(markdown: str) -> str:
    """The paragraph after the title, as plain text."""
    body = re.sub(r"^#[^\n]*\n", "", markdown.lstrip(), count=1).strip()
    paragraph = re.split(r"\n\s*\n", body, maxsplit=1)[0]
    return FORMATTING.sub("", WIKILINK.sub(r"\1", paragraph)).replace("\n", " ").strip()


def glossary_note(vault_dir: Path, name: str) -> GlossaryNote | None:
    note = find_note(vault_dir, name)
    if note is None:
        return None
    path = note.relative_to(vault_dir).with_suffix("").as_posix()
    return GlossaryNote(name=name, summary=first_paragraph(note.read_text(encoding="utf-8")), path=path)
