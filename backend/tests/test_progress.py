from types import SimpleNamespace

from django.test import override_settings
from huggingface_hub.utils._xet_progress_reporting import XetDownloadProgressReporter

from studio import model_downloads
from studio.databases.catalog import EMBEDDING_MODELS
from studio.jobs.progress import Progress, ThrottledProgress, byte_counting_tqdm
from studio.model_downloads import ensure_downloaded

MODEL = EMBEDDING_MODELS["nomic-embed-text-v1.5-q8"]


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_throttle_passes_the_first_report_then_at_most_one_per_interval():
    sent, clock = [], FakeClock()
    throttled = ThrottledProgress(sent.append, interval=0.5, clock=clock)
    for done, at in enumerate([0.0, 0.1, 0.4, 0.6, 0.7, 1.2]):
        clock.now = at
        throttled.report(Progress(done=done, total=10, unit="files"))
    assert [progress.done for progress in sent] == [0, 3, 5]


def test_byte_counting_bar_hands_on_bytes_and_prints_nothing(capsys):
    seen = []
    bar_class = byte_counting_tqdm(lambda written, total: seen.append((written, total)))
    with bar_class(total=100, initial=10, unit="B", desc="model.gguf") as bar:
        bar.update(5)
        bar.update_transfer(50)
        bar.update(85)
    assert seen == [(15, 100), (100, 100)]
    assert capsys.readouterr() == ("", "")


def test_xet_downloads_report_bytes_written_through_one_bar():
    """Xet calls the aggregated-bar methods from its own thread, where a missing one fails silently."""
    seen = []
    reporter = XetDownloadProgressReporter(
        reconstruction_desc="model.gguf",
        total=1000,
        log_level=0,
        tqdm_class=byte_counting_tqdm(lambda *args: seen.append(args)),
    )
    for written, received in [(0, 300), (250, 700), (1000, 1000)]:
        reporter.update_progress(
            SimpleNamespace(
                total_bytes_completed=written,
                total_transfer_bytes_completed=received,
                total_bytes=1000,
                total_bytes_completion_rate=1.0,
                total_transfer_bytes_completion_rate=1.0,
            )
        )
    reporter.close()
    assert seen == [(250, 1000), (1000, 1000)]


def test_download_reports_bytes_through_huggingface_progress_hook(tmp_path, monkeypatch):
    def fake_hf_hub_download(repo, file, local_dir, tqdm_class):
        with tqdm_class(total=None) as bar:
            bar.update(40)
        (local_dir / file).write_bytes(b"x" * 40)

    monkeypatch.setattr(model_downloads, "hf_hub_download", fake_hf_hub_download)
    reports = []
    with override_settings(MODELS_DIR=tmp_path):
        ensure_downloaded(MODEL, reports.append)
    assert reports == [
        Progress(done=40, total=int(MODEL.size_gb * 1e9), unit="bytes", detail=f"Downloading {MODEL.label}")
    ]


def test_an_existing_model_reports_nothing(tmp_path):
    (tmp_path / MODEL.file).write_bytes(b"x")
    reports = []
    with override_settings(MODELS_DIR=tmp_path):
        ensure_downloaded(MODEL, reports.append)
    assert reports == []
