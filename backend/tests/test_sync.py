from studio.ingestion.sync import content_hash, sync_source
from studio.jobs.progress import Progress
from studio.sources.scanning import scan_source


class InMemoryEngine:
    def __init__(self):
        self.documents: dict[tuple[int, str], tuple[str, list]] = {}

    def document_hashes(self, database_id, source_id):
        return {path: digest for (source, path), (digest, _) in self.documents.items() if source == source_id}

    def replace_document(self, database_id, source_id, path, digest, chunks):
        self.documents[(source_id, path)] = (digest, list(chunks))

    def remove_documents(self, database_id, source_id, paths):
        for path in paths:
            self.documents.pop((source_id, path))


class CountingEmbedder:
    def __init__(self):
        self.embedded: list[str] = []

    def embed_documents(self, texts):
        self.embedded.extend(texts)
        return [[float(len(text))] for text in texts]


def paragraphs(_path):
    return lambda text: [part for part in text.split("\n\n") if part.strip()]


def run(root, engine, embedder):
    return sync_source(1, 7, "Notes", root, scan_source(root, [], []), engine, embedder, paragraphs)


def test_first_sync_adds_every_file_with_its_header(tmp_path):
    (tmp_path / "a.md").write_bytes(b"one\n\ntwo")
    engine, embedder = InMemoryEngine(), CountingEmbedder()
    summary = run(tmp_path, engine, embedder)
    assert (summary.added, summary.chunks) == (1, 2)
    digest, chunks = engine.documents[(7, "a.md")]
    assert digest == content_hash(b"one\n\ntwo")
    assert chunks[0].content == "one" and chunks[0].embedding_text == "File: a.md\nSource: Notes\n\none"


def test_sync_reports_each_file_before_working_on_it(tmp_path):
    (tmp_path / "a.md").write_text("one", encoding="utf-8")
    (tmp_path / "b.md").write_text("two", encoding="utf-8")
    reports = []
    sync_source(
        1,
        7,
        "Notes",
        tmp_path,
        scan_source(tmp_path, [], []),
        InMemoryEngine(),
        CountingEmbedder(),
        paragraphs,
        reports.append,
    )
    assert reports == [
        Progress(done=0, total=2, unit="files", detail="a.md"),
        Progress(done=1, total=2, unit="files", detail="b.md"),
    ]


def test_resync_embeds_only_changed_files_and_removes_missing_ones(tmp_path):
    (tmp_path / "keep.md").write_text("same", encoding="utf-8")
    (tmp_path / "edit.md").write_text("old", encoding="utf-8")
    (tmp_path / "gone.md").write_text("bye", encoding="utf-8")
    engine = InMemoryEngine()
    run(tmp_path, engine, CountingEmbedder())
    (tmp_path / "edit.md").write_text("new text", encoding="utf-8")
    (tmp_path / "gone.md").unlink()
    embedder = CountingEmbedder()
    summary = run(tmp_path, engine, embedder)
    assert (summary.added, summary.updated, summary.unchanged, summary.removed) == (0, 1, 1, 1)
    assert embedder.embedded == ["File: edit.md\nSource: Notes\n\nnew text"]
    assert sorted(path for _, path in engine.documents) == ["edit.md", "keep.md"]
