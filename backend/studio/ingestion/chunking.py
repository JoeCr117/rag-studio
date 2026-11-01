"""Splits files into chunks measured in the embedding model's own tokens: Markdown along its headings, everything else
along paragraphs and lines."""

from functools import cache

from semantic_text_splitter import MarkdownSplitter, TextSplitter
from tokenizers import Tokenizer

MARKDOWN_SUFFIXES = (".md", ".markdown")


@cache
def _tokenizer(name: str) -> Tokenizer:
    return Tokenizer.from_pretrained(name)


@cache
def splitter_for(
    tokenizer: str, min_tokens: int, max_tokens: int, overlap: int, markdown: bool
) -> MarkdownSplitter | TextSplitter:
    splitter_type = MarkdownSplitter if markdown else TextSplitter
    return splitter_type.from_huggingface_tokenizer(
        _tokenizer(tokenizer), capacity=(min_tokens, max_tokens), overlap=overlap
    )


def file_header(source_name: str, path: str) -> str:
    """Prepended before embedding so a chunk from the middle of a file still says which file it is from."""
    return f"File: {path}\nSource: {source_name}"


def is_markdown(path: str) -> bool:
    return path.lower().endswith(MARKDOWN_SUFFIXES)
