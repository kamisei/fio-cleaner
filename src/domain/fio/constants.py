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
