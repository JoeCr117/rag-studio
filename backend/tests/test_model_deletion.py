import pytest
from django.test import override_settings

from studio.databases.catalog import EMBEDDING_MODELS
from studio.inference.catalog import GENERATOR_MODELS
from studio.model_downloads import DOWNLOAD_RECORDS, delete_download, remove_partial_downloads, tokenizer_folder

EMBEDDER = EMBEDDING_MODELS["qwen3-embedding-0.6b-q8"]
GENERATOR = GENERATOR_MODELS["qwen3.5-9b-q4km"]


def _write(path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def test_partial_downloads_are_removed_and_finished_files_kept(tmp_path):
    _write(tmp_path / DOWNLOAD_RECORDS / "PAoLHK4_6VEiea1O3_A93Q840Ng=.f2c2.a4037f38.incomplete", 900)
    _write(tmp_path / "hf" / "hub" / "models--BAAI--bge-m3" / "blobs" / "3f2a.incomplete", 100)
    _write(tmp_path / GENERATOR.file, 50)
    _write(tmp_path / DOWNLOAD_RECORDS / f"{GENERATOR.file}.metadata", 5)
    assert remove_partial_downloads(tmp_path) == 1000
    assert list(tmp_path.rglob("*.incomplete")) == []
    assert (tmp_path / GENERATOR.file).exists() and (
        tmp_path / DOWNLOAD_RECORDS / f"{GENERATOR.file}.metadata"
    ).exists()


def test_nothing_partial_frees_nothing(tmp_path):
    assert remove_partial_downloads(tmp_path) == 0


def test_deleting_an_embedder_removes_its_file_records_and_tokenizer_but_nothing_else(tmp_path):
    _write(tmp_path / EMBEDDER.file, 100)
    _write(tmp_path / DOWNLOAD_RECORDS / f"{EMBEDDER.file}.metadata", 10)
    _write(tmp_path / tokenizer_folder(EMBEDDER.tokenizer) / "snapshots" / "tokenizer.json", 5)
    _write(tmp_path / GENERATOR.file, 1)
    _write(tmp_path / DOWNLOAD_RECORDS / f"{GENERATOR.file}.metadata", 1)
    with override_settings(MODELS_DIR=tmp_path):
        freed = delete_download(EMBEDDER)
    assert freed == 115
    assert not (tmp_path / EMBEDDER.file).exists()
    assert not (tmp_path / DOWNLOAD_RECORDS / f"{EMBEDDER.file}.metadata").exists()
    assert not (tmp_path / tokenizer_folder(EMBEDDER.tokenizer)).exists()
    assert (tmp_path / GENERATOR.file).exists() and (
        tmp_path / DOWNLOAD_RECORDS / f"{GENERATOR.file}.metadata"
    ).exists()


def _link(link, target) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("creating symlinks needs Developer Mode on Windows; runs in the backend container")


def test_deleting_a_tokenizer_removes_its_shared_blobs_unless_another_repo_still_links_them(tmp_path):
    blobs = tmp_path / "hf" / "hub" / "blobs"
    _write(blobs / "aa" / "only-mine", 7)
    _write(blobs / "bb" / "shared", 3)
    mine = tmp_path / tokenizer_folder(EMBEDDER.tokenizer)
    other = tmp_path / tokenizer_folder("Qwen/Qwen3-Embedding-4B")
    _link(mine / "snapshots" / "rev" / "tokenizer.json", blobs / "aa" / "only-mine")
    _link(mine / "snapshots" / "rev" / "config.json", blobs / "bb" / "shared")
    _link(other / "snapshots" / "rev" / "config.json", blobs / "bb" / "shared")
    with override_settings(MODELS_DIR=tmp_path):
        freed = delete_download(EMBEDDER)
    assert freed == 7
    assert not (blobs / "aa" / "only-mine").exists() and not mine.exists()
    assert (blobs / "bb" / "shared").exists() and other.exists()


def test_deleting_a_model_that_is_not_downloaded_frees_nothing(tmp_path):
    with override_settings(MODELS_DIR=tmp_path):
        assert delete_download(GENERATOR) == 0
