"""A running job's progress, written to its row so the page's once-a-second poll can draw a progress bar."""

import time
from collections.abc import Callable
from dataclasses import dataclass

from tqdm import tqdm

from studio.models import Job

REPORT_INTERVAL_SECONDS = 0.5


@dataclass(frozen=True)
class Progress:
    done: int
    total: int | None
    """None when the amount of work is not known yet; the bar then shows activity without a percentage."""
    unit: str
    """"files" or "bytes"."""
    detail: str = ""
    """What is being worked on now, such as the file being synced."""


ProgressReport = Callable[[Progress], None]


def ignore_progress(progress: Progress) -> None:
    """For callers with no job to report to."""


class ThrottledProgress:
    """Passes progress on at most once per interval, so a fast loop does not write a database row per file."""

    def __init__(
        self,
        report: ProgressReport,
        interval: float = REPORT_INTERVAL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._report, self._interval, self._clock = report, interval, clock
        self._last_sent: float | None = None

    def report(self, progress: Progress) -> None:
        now = self._clock()
        if self._last_sent is None or now - self._last_sent >= self._interval:
            self._last_sent = now
            self._report(progress)


def job_progress_report(job_id: int) -> ProgressReport:
    def write(progress: Progress) -> None:
        Job.objects.filter(pk=job_id).update(
            progress_done=progress.done,
            progress_total=progress.total,
            progress_unit=progress.unit,
            progress_detail=progress.detail[: Job.PROGRESS_DETAIL_LENGTH],
        )

    return write


def throttled_job_progress(job: Job) -> ProgressReport:
    return ThrottledProgress(job_progress_report(job.id)).report


def byte_counting_tqdm(on_bytes: Callable[[int, int | None], None]) -> type[tqdm]:
    """A progress-bar class for huggingface_hub's `tqdm_class` that prints nothing and hands on (bytes so far, total).

    Defining `update_transfer` and `set_transfer_postfix_str` (huggingface_hub's aggregated-bar interface) makes Xet
    downloads report through this one bar, counting bytes written to disk.
    """

    class ByteCountingTqdm(tqdm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs | {"disable": True})
            self.bytes_written = kwargs.get("initial", 0)

        def update(self, n: float | None = 1) -> None:
            self.bytes_written += int(n or 0)
            on_bytes(self.bytes_written, self.total)

        def update_transfer(self, n: int) -> None:
            """Bytes received from the network; the bar follows bytes written instead."""

        def set_transfer_postfix_str(self, s: str = "", refresh: bool = True) -> None:
            """The network speed text; nothing is printed."""

    return ByteCountingTqdm
