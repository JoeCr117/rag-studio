import json

import httpx
import pytest

from studio.databases.engines.base import SearchHit
from studio.inference.clients import GeneratorClient
from studio.search.answering import passages_within
from studio.search.context_budget import ContextBudget, QuestionTooLong, output_allowance, passages_that_fit


def test_the_output_allowance_grows_with_thinking_but_never_takes_over_half_the_window():
    assert output_allowance(think=False, window=8192) == 1024
    assert output_allowance(think=True, window=8192) == 4096
    assert output_allowance(think=True, window=4096) == 2048


def test_passages_are_kept_best_first_until_the_next_would_overflow():
    assert passages_that_fit([300, 300, 300], base_tokens=100, prompt_budget=700) == 2
    assert passages_that_fit([300, 300], base_tokens=100, prompt_budget=1000) == 2
    assert passages_that_fit([900, 10], base_tokens=100, prompt_budget=700) == 0


def test_the_budget_reports_what_was_left_out():
    assert (
        ContextBudget(window=8192, output_allowance=1024, passages_found=50, passages_used=31).passages_left_out == 19
    )


def _hit(content: str) -> SearchHit:
    return SearchHit(
        document_id=1,
        source_id=1,
        path="a.md",
        chunk_index=0,
        content=content,
        score=0.5,
        similarity=0.5,
        semantic_rank=1,
        keyword_rank=None,
    )


def _generator_counting_words(template_overhead: int) -> GeneratorClient:
    """A fake llama.cpp: one token per word, plus `template_overhead` tokens for the chat template."""

    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if request.url.path == "/apply-template":
            text = " ".join(message["content"] for message in body["messages"])
            return httpx.Response(200, json={"prompt": text + " x" * template_overhead})
        return httpx.Response(200, json={"tokens": body["content"].split()})

    return GeneratorClient("http://generator", transport=httpx.MockTransport(respond))


def test_passages_within_counts_with_the_generators_own_template_and_tokenizer():
    hits = [_hit("word " * 100), _hit("word " * 100), _hit("word " * 100)]
    with _generator_counting_words(template_overhead=20) as generator:
        assert passages_within(generator, "Who?", hits, {1: "notes"}, think=False, prompt_budget=280) == 2
        assert passages_within(generator, "Who?", hits, {1: "notes"}, think=False, prompt_budget=260) == 1


def test_a_question_that_fills_the_budget_alone_is_refused():
    with _generator_counting_words(template_overhead=500) as generator, pytest.raises(QuestionTooLong):
        passages_within(generator, "Who?", [_hit("text")], {}, think=False, prompt_budget=100)
