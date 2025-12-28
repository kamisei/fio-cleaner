from __future__ import annotations

import unicodedata
from typing import Any

from .constants import (
    TECH_STATUS_FIXED,
    TECH_STATUS_OK,
    RULE_NORMALIZE_DASH,
    RULE_NORMALIZE_PUNCTUATION,
    RULE_NORMALIZE_SPACES,
    RULE_STRIP_INVISIBLE,
    RULE_TITLE_CASE,
)
from .types import NormalizationResult


_INVISIBLE_CHARS = {
    "\ufeff",  # BOM
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\u2060",  # WORD JOINER
}

_DASH_CHARS = {
    "\u2010",  # hyphen
    "\u2011",  # non-breaking hyphen
    "\u2012",  # figure dash
    "\u2013",  # en dash
    "\u2014",  # em dash
    "\u2212",  # minus sign
}

_QUOTES = {
    '"',
    "'",
    "«",
    "»",
    "“",
    "”",
    "„",
    "‟",
    "‹",
    "›",
}

_PUNCT_TO_SPACE = {
    ",",
    ".",
    ";",
    "/",
    "\\",
}


def _strip_invisible(s: str) -> str:
    out = []
    for ch in s:
        if ch in _INVISIBLE_CHARS:
            continue
        cat = unicodedata.category(ch)
        # Remove most control/format chars; keep common whitespace for later normalization.
        if cat in {"Cc", "Cf"} and ch not in {"\t", "\n", "\r"}:
            continue
        out.append(ch)
    return "".join(out)


def _normalize_punctuation(s: str) -> str:
    # Keep parentheses as-is. Other punctuation: defined mapping only.
    out = []
    for ch in s:
        if ch in _QUOTES:
            continue
        if ch in _PUNCT_TO_SPACE:
            out.append(" ")
            continue
        out.append(ch)
    return "".join(out)


def _normalize_spaces(s: str) -> str:
    # Convert any whitespace to a space, then collapse runs of spaces, trim.
    chars = [" " if ch.isspace() else ch for ch in s]
    s2 = "".join(chars)
    parts = s2.strip().split()
    return " ".join(parts)


def _normalize_dash(s: str) -> str:
    return "".join("-" if ch in _DASH_CHARS else ch for ch in s)


def _title_case_token_part(part: str) -> str:
    if not part:
        return part
    return part[:1].upper() + part[1:].lower()


def _split_word_suspected_for_title_case(s: str) -> bool:
    # Same heuristic as quality checks, but local to normalizer.
    tokens = [tok for tok in s.strip().split() if tok]
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


def _title_case_outside_parentheses(s: str) -> str:
    """
    Title-case only outside of круглых скобок.

    Content inside (...) is preserved exactly as-is to avoid changing meaning
    (e.g., maiden name, comments).

    Important: spaces are preserved exactly (spaces were already normalized earlier).
    """
    if s == "":
        return s

    out: list[str] = []
    i = 0
    n = len(s)

    def flush_word(buf: list[str]) -> None:
        if not buf:
            return
        word = "".join(buf)
        parts = word.split("-")
        parts = [_title_case_token_part(part) for part in parts]
        out.append("-".join(parts))
        buf.clear()

    word_buf: list[str] = []

    while i < n:
        ch = s[i]

        if ch == "(":
            # Finish any pending word, then copy protected segment verbatim.
            flush_word(word_buf)
            j = i + 1
            depth = 1
            while j < n and depth > 0:
                if s[j] == "(":
                    depth += 1
                elif s[j] == ")":
                    depth -= 1
                j += 1
            out.append(s[i:j])
            i = j
            continue

        if ch == " ":
            flush_word(word_buf)
            out.append(" ")
            i += 1
            continue

        # build word (letters/digits/other symbols) until space or '('
        word_buf.append(ch)
        i += 1

    flush_word(word_buf)
    return "".join(out)



def normalize_fio_value(value: Any) -> NormalizationResult:
    """
    Step 2.2: safe (non-semantic) normalization of a single FIO value.

    Allowed (safe changes):
    - trim outer spaces
    - collapse inner spaces
    - remove invisible/garbage chars
    - normalize unicode dashes to '-'
    - normalize punctuation EXCEPT parentheses:
        commas/dots/semicolons/slashes -> space; quotes removed
    - title case outside parentheses (Cyrillic-friendly), hyphen-aware

    Forbidden:
    - guessing, typo fixing, transliteration
    - reordering or semantic restructuring
    - changing content inside parentheses

    Variant 1B decision:
    - None -> "" is treated as OK (equivalent to empty), not as FIXED.
    """
    before = value

    if value is None:
        return NormalizationResult(before=before, after="", status=TECH_STATUS_OK, applied_rules=[])

    baseline = value if isinstance(value, str) else str(value)
    current = baseline
    applied_rules: list[str] = []

    new = _strip_invisible(current)
    if new != current:
        applied_rules.append(RULE_STRIP_INVISIBLE)
        current = new

    new = _normalize_punctuation(current)
    if new != current:
        applied_rules.append(RULE_NORMALIZE_PUNCTUATION)
        current = new

    new = _normalize_spaces(current)
    if new != current:
        applied_rules.append(RULE_NORMALIZE_SPACES)
        current = new

    new = _normalize_dash(current)
    if new != current:
        applied_rules.append(RULE_NORMALIZE_DASH)
        current = new

    new = current
    if current != "" and not _split_word_suspected_for_title_case(current):
        new = _title_case_outside_parentheses(current)
    if new != current:
        applied_rules.append(RULE_TITLE_CASE)
        current = new

    status = TECH_STATUS_OK if current == baseline else TECH_STATUS_FIXED
    return NormalizationResult(before=before, after=current, status=status, applied_rules=applied_rules)
