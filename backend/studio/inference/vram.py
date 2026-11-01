"""GPU memory: what is in use right now and whether a model about to start would fit.

When VRAM runs out, the NVIDIA driver on Windows silently spills into system RAM and generation slows to a crawl, so
the app warns before a GPU start instead of letting it happen.
"""

import subprocess
import time
from dataclasses import dataclass

HEADROOM_GB = 1.0
"""Kept free for the desktop, other apps and allocation spikes."""
CACHE_SECONDS = 1.0
NVIDIA_SMI = ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"]


@dataclass(frozen=True)
class VramUsage:
    used_mib: int
    total_mib: int

    @property
    def free_gb(self) -> float:
        return (self.total_mib - self.used_mib) / 1024


def parse_nvidia_smi(output: str) -> VramUsage:
    """First GPU of `nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits`."""
    used, total = (int(value.strip()) for value in output.strip().splitlines()[0].split(","))
    return VramUsage(used_mib=used, total_mib=total)


def vram_shortfall(need_gb: float, freed_gb: float, usage: VramUsage | None) -> str | None:
    """A warning when starting something needing `need_gb` (after stopping something holding `freed_gb`) would leave
    less than the headroom free; None when it fits or VRAM cannot be read."""
    if usage is None:
        return None
    free_after = usage.free_gb + freed_gb - need_gb
    if free_after >= HEADROOM_GB:
        return None
    return (
        f"Needs about {need_gb:.1f} GB of VRAM but only {usage.free_gb + freed_gb:.1f} GB is free "
        f"({usage.used_mib / 1024:.1f} of {usage.total_mib / 1024:.1f} GB in use). Past the limit the driver spills "
        "into system RAM and everything on the GPU slows down. Stop something first, or start anyway."
    )


_cached: tuple[float, VramUsage | None] = (0.0, None)


def current_vram() -> VramUsage | None:
    """Live usage of the whole card (every process, not only this app's containers); None without a GPU."""
    global _cached
    read_at, usage = _cached
    if time.monotonic() - read_at < CACHE_SECONDS:
        return usage
    try:
        completed = subprocess.run(NVIDIA_SMI, capture_output=True, text=True, timeout=5)
        usage = parse_nvidia_smi(completed.stdout) if completed.returncode == 0 else None
    except OSError, subprocess.TimeoutExpired, ValueError:
        usage = None
    _cached = (time.monotonic(), usage)
    return usage
