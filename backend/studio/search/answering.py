"""Retrieval-augmented generation: search the database, put the best chunks that fit the context window in a numbered
context, and have the generator answer from that context alone, citing chunk numbers."""

from dataclasses import dataclass, replace

from studio.databases.engines.base import SearchHit
from studio.inference.clients import Completion, GeneratorClient
from studio.models import VectorDatabase
from studio.search.context_budget import ContextBudget, QuestionTooLong, output_allowance, passages_that_fit
from studio.search.querying import SearchResult, search_database

SYSTEM_PROMPT = (
    "You answer questions using only the numbered context passages. Cite the passages you used as [1], [2] and so on. "
    "If the passages do not contain the answer, say that you do not know. Be concise."
)


@dataclass(frozen=True)
class Answer:
    text: str
    search: SearchResult
    """Only the passages the generator received, numbered as in its context."""
    completion: Completion
    budget: ContextBudget


def passage_block(number: int, hit: SearchHit, source_names: dict[int, str]) -> str:
    return f"[{number}] {source_names.get(hit.source_id, f'source {hit.source_id}')} / {hit.path}\n{hit.content}"


def context_block(hits: list[SearchHit], source_names: dict[int, str]) -> str:
    return "\n\n".join(passage_block(number, hit, source_names) for number, hit in enumerate(hits, start=1))


def ask_messages(question: str, hits: list[SearchHit], source_names: dict[int, str]) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n\n{context_block(hits, source_names)}\n\nQuestion: {question}"},
    ]


def passages_within(
    generator: GeneratorClient,
    question: str,
    hits: list[SearchHit],
    source_names: dict[int, str],
    think: bool,
    prompt_budget: int,
) -> int:
    """How many of `hits`, best first, fit in `prompt_budget` tokens once the chat template has built the prompt."""
    base = generator.prompt_tokens(ask_messages(question, [], source_names), think)
    if base > prompt_budget:
        raise QuestionTooLong(
            f"The question alone needs {base:,} tokens; only {prompt_budget:,} are left for the prompt"
        )
    passage_tokens = [
        generator.token_count(passage_block(n, hit, source_names) + "\n\n") for n, hit in enumerate(hits, 1)
    ]
    kept = passages_that_fit(passage_tokens, base, prompt_budget)
    while kept and generator.prompt_tokens(ask_messages(question, hits[:kept], source_names), think) > prompt_budget:
        kept -= 1
    return kept


def answer_question(
    database: VectorDatabase,
    question: str,
    limit: int,
    mode: str,
    rerank_pool: int | None,
    source_names: dict[int, str],
    window: int,
    think: bool = False,
) -> Answer:
    """`window`: the running generator's context window in tokens, shared by the prompt and the answer."""
    search = search_database(database, question, limit, mode, rerank_pool)
    allowance = output_allowance(think, window)
    with GeneratorClient() as generator:
        kept = passages_within(generator, question, search.hits, source_names, think, window - allowance)
        used = search.hits[:kept]
        completion = generator.chat(ask_messages(question, used, source_names), allowance, think)
    budget = ContextBudget(
        window=window, output_allowance=allowance, passages_found=len(search.hits), passages_used=kept
    )
    return Answer(text=completion.text, search=replace(search, hits=used), completion=completion, budget=budget)
