"""HTTP clients for the shared generator and reranker containers (llama.cpp server, OpenAI-compatible routes)."""

from dataclasses import dataclass

import httpx

from studio.inference.model_server import ModelServerClient

GENERATOR_URL = "http://generator:8080"
RERANKER_URL = "http://reranker:8080"


def is_healthy(base_url: str) -> bool:
    """llama.cpp answers /health with 200 only once the model is loaded."""
    try:
        return httpx.get(f"{base_url}/health", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


@dataclass(frozen=True)
class Completion:
    text: str
    prompt_tokens: int
    completion_tokens: int
    prompt_ms: float
    """Prefill: reading the whole prompt (question plus retrieved chunks) before the first answer token."""
    generation_ms: float
    tokens_per_second: float
    """Generation speed, the figure the project's 25-100 tok/s band is about."""
    reasoning: str = ""
    """The model's thinking, which llama.cpp returns apart from the answer; empty when thinking was off or the model's
    chat template has no thinking mode. Its tokens are counted in `completion_tokens`."""
    finish_reason: str = "stop"
    """"length" when the output allowance ran out, so the answer is cut off."""


def chat_request(messages: list[dict], max_tokens: int, think: bool) -> dict:
    """`enable_thinking` is the chat-template switch thinking models read; templates without it ignore it. Sending it
    on every request overrides the server's own default, so one running generator answers either way."""
    return {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "cache_prompt": False,
        "chat_template_kwargs": {"enable_thinking": think},
    }


def completion_from_response(body: dict) -> Completion:
    usage, timings = body.get("usage", {}), body.get("timings", {})
    choice = body["choices"][0]
    message = choice["message"]
    return Completion(
        reasoning=message.get("reasoning_content") or "",
        text=message["content"] or "",
        prompt_tokens=timings.get("prompt_n", usage.get("prompt_tokens", 0)),
        completion_tokens=timings.get("predicted_n", usage.get("completion_tokens", 0)),
        prompt_ms=round(timings.get("prompt_ms", 0.0), 1),
        generation_ms=round(timings.get("predicted_ms", 0.0), 1),
        tokens_per_second=round(timings.get("predicted_per_second", 0.0), 1),
        finish_reason=choice.get("finish_reason") or "stop",
    )


class GeneratorClient(ModelServerClient):
    def __init__(self, base_url: str = GENERATOR_URL, transport: httpx.BaseTransport | None = None) -> None:
        super().__init__(base_url, "generator", timeout=280, transport=transport)

    def chat(self, messages: list[dict], max_tokens: int, think: bool = False) -> Completion:
        return completion_from_response(self._post("/v1/chat/completions", chat_request(messages, max_tokens, think)))

    def prompt_tokens(self, messages: list[dict], think: bool) -> int:
        """The exact prompt the chat template builds from `messages`, counted in the generator's own tokens."""
        prompt = self._post(
            "/apply-template", {"messages": messages, "chat_template_kwargs": {"enable_thinking": think}}
        )
        return self.token_count(prompt["prompt"])

    def token_count(self, text: str) -> int:
        body = self._post("/tokenize", {"content": text, "add_special": False, "parse_special": True})
        return len(body["tokens"])


class RerankerClient(ModelServerClient):
    """A cross-encoder scores (query, document) pairs read together: slower than comparing vectors, but sharper, so it
    only re-orders a candidate pool that search already found."""

    def __init__(self, base_url: str = RERANKER_URL) -> None:
        super().__init__(base_url, "reranker", timeout=120)

    def scores(self, query: str, documents: list[str]) -> list[float]:
        """Relevance score per document, in the order given."""
        if not documents:
            return []
        body = self._post("/v1/rerank", {"query": query, "documents": documents, "top_n": len(documents)})
        by_index = {result["index"]: result["relevance_score"] for result in body["results"]}
        return [by_index[index] for index in range(len(documents))]
