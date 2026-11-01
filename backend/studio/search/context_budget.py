"""How much of the generator's context window the retrieved passages may fill.

The window holds the prompt and the answer together. Without a budget, too many passages leave no room for the answer:
llama.cpp stops at the window's end and the answer is cut off mid-sentence.
"""

from dataclasses import dataclass
from itertools import accumulate

ANSWER_TOKENS = 1024
THINKING_TOKENS = 3072
"""Added to the output allowance when thinking: thinking and answer share one limit, so without it a long trace would
leave no room for the answer."""
MAX_OUTPUT_SHARE = 2
"""The output allowance never takes more than 1/2 of the window, so a small window still has room for passages."""


@dataclass(frozen=True)
class ContextBudget:
    window: int
    output_allowance: int
    passages_found: int
    passages_used: int

    @property
    def passages_left_out(self) -> int:
        return self.passages_found - self.passages_used


def output_allowance(think: bool, window: int) -> int:
    return min(ANSWER_TOKENS + (THINKING_TOKENS if think else 0), window // MAX_OUTPUT_SHARE)


def passages_that_fit(passage_tokens: list[int], base_tokens: int, prompt_budget: int) -> int:
    """How many passages, best first, fit in `prompt_budget` after the `base_tokens` of instructions and question."""
    return sum(1 for total in accumulate(passage_tokens) if base_tokens + total <= prompt_budget)


class QuestionTooLong(ValueError):
    """The instructions and question alone do not fit, before any passage."""
