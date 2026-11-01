from qdrant_client import models

from studio.databases.engines.base import SearchHit, StoredChunk
from studio.databases.engines.qdrant_engine import DOCUMENT_POINT, chunk_points, cosine, document_id, matching, point_id
from studio.inference.catalog import GENERATOR_MODELS, inference_options
from studio.inference.clients import chat_request, completion_from_response
from studio.inference.servers import running_vram_gb
from studio.inference.vram import VramUsage, parse_nvidia_smi, vram_shortfall
from studio.model_downloads import DOWNLOADABLE_MODELS
from studio.models import InferenceServer
from studio.search.answering import ask_messages
from studio.search.querying import reranked


def hit(path: str, score: float = 0.0) -> SearchHit:
    return SearchHit(
        document_id=1,
        source_id=2,
        path=path,
        chunk_index=0,
        content=f"text of {path}",
        score=score,
        similarity=0.5,
        semantic_rank=1,
        keyword_rank=None,
    )


def test_nvidia_smi_output_parses_to_mib():
    assert parse_nvidia_smi("1260, 12288\n") == VramUsage(used_mib=1260, total_mib=12288)


def test_vram_warning_keeps_a_gigabyte_of_headroom():
    usage = VramUsage(used_mib=4 * 1024, total_mib=12 * 1024)
    assert vram_shortfall(6.5, 0.0, usage) is None
    assert "Needs about 7.5 GB" in vram_shortfall(7.5, 0.0, usage)
    assert vram_shortfall(7.5, 6.0, usage) is None
    assert vram_shortfall(99.0, 0.0, None) is None


def test_generator_estimate_grows_with_context():
    model = GENERATOR_MODELS["qwen3.5-9b-q4km"]
    assert model.vram_estimate_gb(16384) > model.vram_estimate_gb(8192)


def test_running_vram_counts_only_running_gpu_servers():
    generator = InferenceServer(
        role="generator", model_key="qwen3.5-9b-q4km", runtime="gpu", context=8192, running=True
    )
    assert running_vram_gb(generator) == GENERATOR_MODELS["qwen3.5-9b-q4km"].vram_estimate_gb(8192)
    assert (
        running_vram_gb(
            InferenceServer(role="reranker", model_key="qwen3-reranker-0.6b-q8", runtime="cpu", running=True)
        )
        == 0.0
    )
    assert running_vram_gb(None) == 0.0


def test_every_catalog_is_downloadable_and_reports_status():
    options = inference_options({"qwen3.5-9b-q4km": "downloaded"})
    assert {model["key"] for model in options["generator_models"]} <= set(DOWNLOADABLE_MODELS)
    assert (
        next(m for m in options["generator_models"] if m["key"] == "qwen3.5-9b-q4km")["download_status"] == "downloaded"
    )
    assert all(model["download_status"] == "missing" for model in options["reranker_models"])


def test_reranking_reorders_by_cross_encoder_score_and_truncates():
    result = reranked([hit("a.md"), hit("b.md"), hit("c.md")], [0.1, 0.9, 0.5], limit=2)
    assert [(item.path, item.rerank_score) for item in result] == [("b.md", 0.9), ("c.md", 0.5)]


def test_ask_prompt_numbers_each_passage_with_its_source():
    messages = ask_messages("Who?", [hit("a.md"), hit("b.md")], {2: "notes"})
    assert "[1]" in messages[0]["content"]
    assert "[1] notes / a.md\ntext of a.md" in messages[1]["content"]
    assert "[2] notes / b.md" in messages[1]["content"]
    assert messages[1]["content"].endswith("Question: Who?")


def test_llama_cpp_timings_become_the_completion_figures():
    completion = completion_from_response(
        {
            "choices": [{"message": {"content": "Helen [1]."}}],
            "timings": {
                "prompt_n": 900,
                "prompt_ms": 210.44,
                "predicted_n": 12,
                "predicted_ms": 150.0,
                "predicted_per_second": 80.04,
            },
        }
    )
    assert (completion.text, completion.prompt_tokens, completion.tokens_per_second) == ("Helen [1].", 900, 80.0)
    assert completion.finish_reason == "stop"


def test_an_answer_cut_off_by_the_output_allowance_says_so():
    completion = completion_from_response(
        {"choices": [{"message": {"content": "Helen went"}, "finish_reason": "length"}]}
    )
    assert completion.finish_reason == "length"


def test_thinking_is_returned_apart_from_the_answer():
    completion = completion_from_response(
        {
            "choices": [
                {"message": {"content": "Twelve pens cost $8.", "reasoning_content": "3 pens = $2, so 12 = 4 x $2."}}
            ],
            "timings": {"predicted_n": 198},
        }
    )
    assert (completion.text, completion.reasoning, completion.completion_tokens) == (
        "Twelve pens cost $8.",
        "3 pens = $2, so 12 = 4 x $2.",
        198,
    )


def test_every_request_says_whether_to_think_and_thinking_gets_room_to_answer():
    assert chat_request([], 1024, think=True)["chat_template_kwargs"] == {"enable_thinking": True}
    assert chat_request([], 1024, think=False)["chat_template_kwargs"] == {"enable_thinking": False}


def test_qdrant_ids_are_stable_and_distinct():
    assert document_id(1, "a.md") == document_id(1, "a.md") != document_id(2, "a.md")
    assert 0 <= document_id(1, "a.md") < 2**60
    assert point_id(1, "a.md", 0) != point_id(1, "a.md", 1)


def test_qdrant_filter_matches_lists_with_any():
    conditions = matching(source_id=3, path=["a.md", "b.md"]).must
    assert isinstance(conditions[0].match, models.MatchValue) and isinstance(conditions[1].match, models.MatchAny)


def test_each_document_gets_a_vectorless_marker_point_before_its_chunks():
    points = chunk_points(
        3, "a.md", "hash", [StoredChunk(index=0, content="c", embedding_text="File: a.md\n\nc", vector=[0.6, 0.8])]
    )
    marker, chunk = points
    assert marker.payload["chunk_index"] == DOCUMENT_POINT and marker.vector == {}
    assert marker.payload["chunk_count"] == 1 and marker.payload["content_hash"] == "hash"
    assert chunk.vector["dense"] == [0.6, 0.8] and chunk.vector["bm25"].text == "File: a.md\n\nc"


def test_cosine_ignores_vector_length():
    assert round(cosine([1.0, 0.0], [5.0, 0.0]), 6) == 1.0
    assert round(cosine([1.0, 0.0], [0.0, 2.0]), 6) == 0.0
