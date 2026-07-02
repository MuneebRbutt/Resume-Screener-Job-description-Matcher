import re

import nltk
from nltk.corpus import words as nltk_words

nltk.download("words", quiet=True)

_ENGLISH_WORDS = {w.lower() for w in nltk_words.words()}

MIN_WORD_COUNT = 25
MIN_UNIQUE_RATIO = 0.3
MIN_VALID_WORD_RATIO = 0.45


def is_probably_job_description(text: str) -> tuple[bool, str]:
    """Heuristically check whether text looks like a real job description."""
    tokens = re.findall(r"[a-zA-Z]{2,}", text.lower())
    word_count = len(tokens)

    if word_count < MIN_WORD_COUNT:
        return False, "it's too short to be a real job description"

    unique_tokens = set(tokens)
    unique_ratio = len(unique_tokens) / word_count
    if unique_ratio < MIN_UNIQUE_RATIO:
        return False, "it looks too repetitive to be a real job description"

    valid_word_count = sum(1 for token in unique_tokens if token in _ENGLISH_WORDS)
    valid_ratio = valid_word_count / len(unique_tokens)
    if valid_ratio < MIN_VALID_WORD_RATIO:
        return False, "it doesn't contain enough recognizable English words"

    return True, ""
