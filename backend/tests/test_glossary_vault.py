"""The glossary vault's shape (Vault Metadata.md): Home → area → group → note at any depth, every note listed by its
folder's hub and found by name, and every note the UI explains present."""

import re
from collections import Counter
from pathlib import Path

from studio.glossary import find_note, first_paragraph, glossary_note
from studio.model_locations import BUILT_IN_MODELS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VAULT_DIR = PROJECT_ROOT / "RAGStudioVault"
WEB_SOURCES = [*(PROJECT_ROOT / "web" / "components").glob("*.tsx"), *(PROJECT_ROOT / "web" / "app").glob("*.tsx")]
HOME = "Home"
WIKILINK = re.compile(r"\[\[([^\]|#\\]+)")
CODE = re.compile(r"(`{3,}).*?\1|`[^`\n]+`", re.DOTALL)
UI_NOTE_PROP = re.compile(r'\bnote(?:=|: )("[^"]+"|\{[^}]*\})')
QUOTED = re.compile(r'"([^"]+)"')
"""Note names written in the UI source: `note="A"`, both sides of `note={cond ? "A" : "B"}`, and `note: "A"` in objects.
Names read from data (such as built-in model notes) are checked where that data is defined."""

NOTE_FILES = sorted(VAULT_DIR.rglob("*.md"))
LINKS = {note.stem: WIKILINK.findall(CODE.sub("", note.read_text(encoding="utf-8"))) for note in NOTE_FILES}


def is_hub(note: Path) -> bool:
    return note.stem == HOME or note.stem == note.parent.name


def hub_of(note: Path) -> str:
    """The hub that must list this note: its folder's hub, or for a hub, the hub of the folder above."""
    folder = note.parent.parent if is_hub(note) else note.parent
    return HOME if folder == VAULT_DIR else folder.name


def test_note_names_are_unique():
    repeated = [name for name, count in Counter(note.stem for note in NOTE_FILES).items() if count > 1]
    assert repeated == []


def test_no_path_outside_an_area_contains_that_area_name():
    """Graph colour groups and path searches match an area by text anywhere in the path, not by folder."""
    areas = [folder.name for folder in VAULT_DIR.iterdir() if folder.is_dir() and not folder.name.startswith(".")]
    paths = [note.relative_to(VAULT_DIR).as_posix() for note in NOTE_FILES]
    clashes = [
        (area, path)
        for area in areas
        for path in paths
        if area.lower() in path.lower() and not path.startswith(f"{area}/")
    ]
    assert clashes == []


def test_every_link_points_at_a_note():
    broken = {(name, target) for name, targets in LINKS.items() for target in targets if target not in LINKS}
    assert broken == set()


def test_every_note_is_listed_by_its_own_hub():
    unlisted = [note.stem for note in NOTE_FILES if note.stem != HOME and note.stem not in LINKS[hub_of(note)]]
    assert unlisted == []


def test_every_note_opens_with_a_title_and_a_summary_paragraph():
    for note in NOTE_FILES:
        title, blank, summary, *_ = note.read_text(encoding="utf-8").splitlines()
        assert title == f"# {note.stem}"
        assert blank == "" and summary and not summary.startswith(("-", "#"))


def test_every_note_the_ui_explains_exists():
    referenced = {
        name
        for source in WEB_SOURCES
        for prop in UI_NOTE_PROP.findall(source.read_text(encoding="utf-8"))
        for name in QUOTED.findall(prop)
    }
    assert referenced, "the reference pattern no longer matches the web source"
    assert {name for name in referenced if find_note(VAULT_DIR, name) is None} == set()


def test_every_built_in_model_note_exists():
    assert [model.note for model in BUILT_IN_MODELS if find_note(VAULT_DIR, model.note) is None] == []


def test_find_note_searches_every_folder_and_stays_inside_the_vault(tmp_path):
    filed = tmp_path / "Runtime" / "Inference Servers" / "llama.cpp.md"
    filed.parent.mkdir(parents=True)
    filed.touch()
    assert find_note(tmp_path, "llama.cpp") == filed
    assert find_note(tmp_path, "Missing") is None
    assert find_note(tmp_path, "../secrets") is None
    assert find_note(tmp_path, "Runtime/Inference Servers/llama.cpp") is None


def test_first_paragraph_is_plain_text_without_links_or_formatting():
    markdown = (
        "# Chunk\n\nOne **piece** of a [[Document|file]], measured in [[Tokens]] and `code`.\n\n- **Detail:** more."
    )
    assert first_paragraph(markdown) == "One piece of a file, measured in Tokens and code."


def test_glossary_note_gives_the_path_obsidian_opens():
    note = glossary_note(VAULT_DIR, "Hybrid search")
    assert note.path == "Search/Search Methods/Hybrid search"
    assert note.summary.startswith("Running a vector search and a keyword search")
