"""Where a model server can run. The GPU is offered only when compose.gpu.yaml gave the containers an NVIDIA GPU."""

RUNTIMES = ("cpu", "gpu")
NO_GPU_MESSAGE = (
    "No NVIDIA GPU was found when RAG Studio started, so models run on the CPU only. "
    "With an NVIDIA GPU and driver installed, start RAG Studio again with start.ps1."
)


def available_runtimes(gpu_available: bool) -> tuple[str, ...]:
    return RUNTIMES if gpu_available else ("cpu",)
