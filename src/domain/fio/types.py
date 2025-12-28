from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NormalizationResult:
    """
    Result of a single-value normalization.

    before: original input value as received (may be None, number, string, etc.)
    after: normalized string (may be empty string)
    status: technical status ("ok" or "fixed")
    applied_rules: list of rule codes that actually changed the value (in order)
    """

    before: Any
    after: str
    status: str
    applied_rules: list[str]
