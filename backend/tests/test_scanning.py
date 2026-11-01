import os

from studio.sources.scanning import MAX_FILE_BYTES, file_changes, pattern_lines, scan_source


def write(path, text="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def paths(result):
    return [file.path for file in result.files]


def test_default_rules_keep_text_and_code_and_skip_tool_folders(tmp_path):
    for name in [
        "notes/a.md",
        "src/app.py",
        "image.png",
        "node_modules/lib/index.js",
        ".git/config.txt",
        ".obsidian/x.md",
    ]:
        write(tmp_path / name)
    assert paths(scan_source(tmp_path, [], [])) == ["notes/a.md", "src/app.py"]


def test_gitignore_files_apply_to_their_own_folder(tmp_path):
    write(tmp_path / ".gitignore", "secret.md\n")
    write(tmp_path / "secret.md")
    write(tmp_path / "pkg" / ".gitignore", "generated/\n")
    write(tmp_path / "pkg" / "generated" / "out.py")
    write(tmp_path / "pkg" / "keep.py")
    write(tmp_path / "other" / "generated" / "kept.py")
    assert paths(scan_source(tmp_path, [], [])) == ["other/generated/kept.py", "pkg/keep.py"]


def test_source_patterns_narrow_the_files(tmp_path):
    for name in ["a.md", "b.py", "drafts/c.md"]:
        write(tmp_path / name)
    assert paths(scan_source(tmp_path, ["*.md"], ["drafts/"])) == ["a.md"]


def test_large_files_are_skipped(tmp_path):
    write(tmp_path / "big.txt", "x" * (MAX_FILE_BYTES + 1))
    assert paths(scan_source(tmp_path, [], [])) == []


def test_fingerprint_changes_with_content_metadata(tmp_path):
    write(tmp_path / "a.md", "one")
    before = scan_source(tmp_path, [], [])
    assert scan_source(tmp_path, [], []).fingerprint == before.fingerprint
    write(tmp_path / "a.md", "two words")
    os.utime(tmp_path / "a.md", ns=(1, 1))
    write(tmp_path / "b.md")
    after = scan_source(tmp_path, [], [])
    assert after.fingerprint != before.fingerprint
    assert file_changes(before.files, after.files).__dict__ == {"added": 1, "removed": 0, "modified": 1}


def test_pattern_lines_drop_blanks_and_comments():
    assert pattern_lines("*.md\n\n# note\n  drafts/  \n") == ["*.md", "drafts/"]
