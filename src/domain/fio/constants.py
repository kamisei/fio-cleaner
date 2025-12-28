# Domain constants for Step 2.2 (safe normalization of FIO values)

TECH_STATUS_OK = "ok"
TECH_STATUS_FIXED = "fixed"

TECH_STATUSES = {
    "ok": TECH_STATUS_OK,
    "fixed": TECH_STATUS_FIXED,
}

UI_STATUS_LABELS_RU = {
    "ok": "ок",
    "fixed": "нормализовано",
    "needs_review": "требует проверки",
}

RULE_TO_STR_OR_EMPTY = "to_str_or_empty"
RULE_STRIP_INVISIBLE = "strip_invisible"
RULE_NORMALIZE_PUNCTUATION = "normalize_punctuation"
RULE_NORMALIZE_SPACES = "normalize_spaces"
RULE_NORMALIZE_DASH = "normalize_dash"
RULE_TITLE_CASE = "title_case"

RULES_REGISTRY_RU = {
    RULE_TO_STR_OR_EMPTY: "приведение к строке или пусто",
    RULE_STRIP_INVISIBLE: "удаление невидимых/мусорных символов",
    RULE_NORMALIZE_PUNCTUATION: "нормализация пунктуации (кроме круглых скобок)",
    RULE_NORMALIZE_SPACES: "нормализация пробелов",
    RULE_NORMALIZE_DASH: "нормализация тире",
    RULE_TITLE_CASE: "приведение регистра (Title Case)",
}


# Quality checks (warnings) - Step 2.3.x
ATTENTION_LABEL_RU = "❗️требует внимания"

WARN_HAS_DIGITS = "has_digits"
WARN_HAS_LATIN = "has_latin"
WARN_SPLIT_WORD_SUSPECTED = "split_word_suspected"
WARN_TOO_SHORT = "too_short"
WARN_SINGLE_LETTER_TOKEN = "single_letter_token"

WARNING_LABELS_RU = {
    WARN_HAS_DIGITS: "цифры",
    WARN_HAS_LATIN: "латиница",
    WARN_SPLIT_WORD_SUSPECTED: "разрыв внутри слова",
    WARN_TOO_SHORT: "слишком коротко",
    WARN_SINGLE_LETTER_TOKEN: "однобуквенный фрагмент",
}
