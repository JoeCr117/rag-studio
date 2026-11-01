"""Turns text into vectors through an embedder container's OpenAI-compatible /v1/embeddings endpoint."""

from itertools import batched

from studio.databases.catalog import EmbeddingModel
from studio.inference.model_server import ModelServerClient


class EmbeddingClient(ModelServerClient):
    def __init__(self, base_url: str, model: EmbeddingModel, batch_size: int = 8) -> None:
        super().__init__(base_url, f"embedder for {model.label}", timeout=300)
        self._model = model
        self._batch_size = batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prefixed = [f"{self._model.document_prefix}{text}" for text in texts]
        return [
            vector for batch in batched(prefixed, self._batch_size, strict=False) for vector in self._embed(list(batch))
        ]

    def embed_query(self, query: str) -> list[float]:
        return self._embed([f"{self._model.query_prefix}{query}"])[0]

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        body = self._post("/v1/embeddings", {"input": inputs})
        return [item["embedding"] for item in sorted(body["data"], key=lambda item: item["index"])]
