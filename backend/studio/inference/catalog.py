"""Generator and reranker models the Ask tab can start. GGUF files from public Hugging Face repos (no login).

VRAM figures are rough estimates for the warning before a start; the worker logs the measured use after each start.
"""

from dataclasses import asdict, dataclass

GENERATOR_CONTEXTS = (4096, 8192, 16384, 32768)
DEFAULT_GENERATOR_CONTEXT = 8192


@dataclass(frozen=True)
class GeneratorModel:
    key: str
    label: str
    repo: str
    file: str
    size_gb: float
    vram_gb: float
    """Weights and compute buffers held on the GPU, without the KV cache."""
    kv_gb_per_8k: float
    """q8_0 KV cache per 8,192 tokens of context."""
    cpu_moe_layers: int = 0
    """Mixture-of-experts layers whose expert weights stay in system RAM (`-ncmoe`)."""
    notes: str = ""

    def vram_estimate_gb(self, context: int) -> float:
        return round(self.vram_gb + self.kv_gb_per_8k * context / 8192, 1)


@dataclass(frozen=True)
class RerankerModel:
    key: str
    label: str
    repo: str
    file: str
    size_gb: float
    vram_gb: float
    notes: str = ""


GENERATOR_MODELS = {
    model.key: model
    for model in (
        GeneratorModel(
            key="qwen3.5-9b-q4km",
            label="Qwen3.5 9B (Q4_K_M)",
            repo="unsloth/Qwen3.5-9B-GGUF",
            file="Qwen3.5-9B-Q4_K_M.gguf",
            size_gb=5.29,
            vram_gb=5.1,
            kv_gb_per_8k=0.3,
            notes="Thinking model, run with reasoning off. The main project's default generator.",
        ),
        GeneratorModel(
            key="granite-4.2-8b-q5km",
            label="Granite 4.2 8B (Q5_K_M)",
            repo="ibm-granite/granite-4.2-8b-GGUF",
            file="granite-4.2-8b-Q5_K_M.gguf",
            size_gb=5.82,
            vram_gb=6.4,
            kv_gb_per_8k=0.6,
            notes="Tuned by IBM for grounded answers with citations.",
        ),
        GeneratorModel(
            key="gemma-4-12b-q4km",
            label="Gemma 4 12B (Q4_K_M)",
            repo="unsloth/gemma-4-12b-it-GGUF",
            file="gemma-4-12b-it-Q4_K_M.gguf",
            size_gb=6.63,
            vram_gb=7.3,
            kv_gb_per_8k=0.8,
            notes="Largest dense model that fits fully in 12 GB.",
        ),
        GeneratorModel(
            key="lfm2.5-8b-a1b-q4km",
            label="LFM2.5 8B-A1B (Q4_K_M)",
            repo="LiquidAI/LFM2.5-8B-A1B-GGUF",
            file="LFM2.5-8B-A1B-Q4_K_M.gguf",
            size_gb=4.8,
            vram_gb=5.3,
            kv_gb_per_8k=0.2,
            notes="Mixture of experts with 1B active parameters per token: very fast, less accurate.",
        ),
        GeneratorModel(
            key="gemma-4-26b-a4b-q4km",
            label="Gemma 4 26B-A4B (UD-Q4_K_M)",
            repo="unsloth/gemma-4-26B-A4B-it-GGUF",
            file="gemma-4-26B-A4B-it-UD-Q4_K_M.gguf",
            size_gb=15.78,
            vram_gb=8.5,
            kv_gb_per_8k=0.5,
            cpu_moe_layers=18,
            notes="Mixture of experts larger than VRAM: 18 layers' experts stay in system RAM, so it is slower.",
        ),
    )
}

RERANKER_MODELS = {
    model.key: model
    for model in (
        RerankerModel(
            key="qwen3-reranker-0.6b-q8",
            label="Qwen3-Reranker 0.6B (Q8)",
            repo="ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF",
            file="qwen3-reranker-0.6b-q8_0.gguf",
            size_gb=0.6,
            vram_gb=1.0,
            notes="Cross-encoder: reads the query and each candidate chunk together and scores the pair.",
        ),
    )
}


def inference_options(model_status: dict[str, str]) -> dict:
    """`model_status`: model key -> "downloaded", "downloading" or "missing"."""

    def with_status(model) -> dict:
        return asdict(model) | {"download_status": model_status.get(model.key, "missing")}

    return {
        "generator_models": [
            with_status(model) | {"vram_estimate_gb": model.vram_estimate_gb(DEFAULT_GENERATOR_CONTEXT)}
            for model in GENERATOR_MODELS.values()
        ],
        "reranker_models": [with_status(model) for model in RERANKER_MODELS.values()],
        "generator_contexts": list(GENERATOR_CONTEXTS),
    }
