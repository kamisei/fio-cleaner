from __future__ import annotations

from typing import Any

from .constants import (
    WARN_HAS_DIGITS,
    WARN_HAS_LATIN,
    WARN_SINGLE_LETTER_TOKEN,
    WARN_SPLIT_WORD_SUSPECTED,
    WARN_TOO_SHORT,
)


def _to_str(value: Any) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def _has_latin(s: str) -> bool:
    return any(("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in s)


def _tokenize(s: str) -> list[str]:
    # We do not normalize here; checks are based on the raw value.
    # Split by whitespace runs.
    return [tok for tok in s.strip().split() if tok]


def _split_word_suspected(tokens: list[str]) -> bool:
    # split_word_suspected:
    # 1) single-letter token followed by token starting with lowercase letter: "Г еоргиевна"
    # 2) token ending with lowercase letter followed by token starting with lowercase: "серге евич"
    for a, b in zip(tokens, tokens[1:]):
        if not a or not b:
            continue
        b0 = b[0]
        if b0.isalpha() and b0 == b0.lower():
            if len(a) == 1 and a.isalpha() and a == a.upper():
                return True
            a_last = a[-1]
            if a_last.isalpha() and a_last == a_last.lower():
                return True
    return False


def detect_warnings(before: Any) -> list[str]:
    """
    W1 (optimal) warning set. Returns stable-ordered list of warning codes.

    Warnings do NOT change the value and do NOT affect ok/fixed normalization status.
    """
    s = _to_str(before)

    # Empty value is not a problem at this stage
    if not s.strip():
        return []

    tokens = _tokenize(s)

    warnings: list[str] = []

    # 1) digits
    if any(ch.isdigit() for ch in s):
        warnings.append(WARN_HAS_DIGITS)

    # 2) latin
    if _has_latin(s):
        warnings.append(WARN_HAS_LATIN)

    # 3) split word suspected
    if _split_word_suspected(tokens):
        warnings.append(WARN_SPLIT_WORD_SUSPECTED)

    # 4) too short
    # Rule: too_short only if the whole string is extremely short OR single 1-letter token.
    if len(s.strip()) < 2:
        warnings.append(WARN_TOO_SHORT)
    elif len(tokens) == 1 and len(tokens[0]) == 1 and tokens[0].isalpha():
        warnings.append(WARN_TOO_SHORT)

    # 5) single-letter token
    if any(len(tok) == 1 and tok.isalpha() for tok in tokens):
        warnings.append(WARN_SINGLE_LETTER_TOKEN)

    return warnings
