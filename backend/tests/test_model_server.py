import httpx
import pytest

from studio.inference.model_server import ModelServerError, post_json


def _client(handler) -> httpx.Client:
    return httpx.Client(base_url="http://embedder", transport=httpx.MockTransport(handler))


def test_a_refusal_carries_llama_cpp_s_own_message():
    def refuse(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"message": "input is too large to process"}})

    with pytest.raises(ModelServerError, match=r"embedder refused the request \(400\): input is too large to process"):
        post_json(_client(refuse), "/v1/embeddings", {}, "embedder")


def test_a_server_that_is_not_answering_says_to_start_it_again():
    def unreachable(request):
        raise httpx.ConnectError("Name or service not known")

    with pytest.raises(ModelServerError, match="reranker is not answering: start it again"):
        post_json(_client(unreachable), "/v1/rerank", {}, "reranker")


def test_a_success_returns_the_json_body():
    assert post_json(_client(lambda request: httpx.Response(200, json={"ok": 1})), "/x", {}, "generator") == {"ok": 1}
