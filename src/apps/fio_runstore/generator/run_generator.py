"""
Suggestion generator entry point.

Responsibilities:
- create Run records;
- iterate through CSV rows;
- generate Suggestion objects (no auto-fixes).
"""

from typing import Optional
import csv
import io

from django.core.files.storage import default_storage

from apps.fio_runstore.models import Run, Suggestion
from apps.fio_runstore.generator.name_dictionary import load_names_variant_map


GENERATOR_ID = "apps.fio_runstore.generator"
GENERATOR_VERSION = "0.2"


def _extract_first_name_from_fio(value: str) -> Optional[str]:
    """
    Very simple heuristic for single-field FIO:
    assume 'Last First Middle' and take the second token.
    """
    if not value:
        return None
    parts = [p for p in value.strip().split() if p]
    if len(parts) < 2:
        return None
    return parts[1]


def generate_suggestions_for_csv(
    *,
    source_csv_path: str,
    selection: dict,
    encoding: Optional[str] = None,
    delimiter: Optional[str] = None,
) -> Run:
    """
    Create a Run and generate name-based suggestions using dictionary.
    """

    run = Run.objects.create(
        source_csv_path=source_csv_path,
        selection=selection,
        encoding=encoding,
        delimiter=delimiter,
    )

    name_map, name_meta = load_names_variant_map()

    with default_storage.open(source_csv_path, "rb") as raw:
        text = io.TextIOWrapper(raw, encoding=encoding or "utf-8", newline="")
        reader = csv.reader(text, delimiter=delimiter or ",")

        header = next(reader, None)
        if header is None:
            return run

        col_index = {name: i for i, name in enumerate(header)}

        mode = selection.get("mode")

        for row_id, row in enumerate(reader, start=1):
            if mode == "split":
                first_col = selection.get("first_name_column")
                if not first_col:
                    continue
                idx = col_index.get(first_col)
                if idx is None or idx >= len(row):
                    continue
                before = (row[idx] or "").strip()
                field_name = "first_name"

            else:  # single
                fio_col = selection.get("fio_column")
                if not fio_col:
                    continue
                idx = col_index.get(fio_col)
                if idx is None or idx >= len(row):
                    continue
                fio_val = (row[idx] or "").strip()
                before = _extract_first_name_from_fio(fio_val)
                field_name = "fio.first_name"

            if not before:
                continue

            canonical = name_map.get(before)
            if not canonical or canonical == before:
                continue

            Suggestion.objects.create(
                run=run,
                row_id=row_id,
                field_name=field_name,
                before_value=before,
                suggested_value=canonical,
                suggestion_code="DICT_NAME_VARIANT",
                confidence=Suggestion.CONFIDENCE_HIGH,
                message=f"В словаре имён вариант «{before}» сопоставлен с канонической формой «{canonical}».",
                evidence={
                    "variant": before,
                    "canonical": canonical,
                    "dictionary": name_meta.path,
                },
                generator=GENERATOR_ID,
                generator_version=GENERATOR_VERSION,
                dictionary_hash=name_meta.sha256,
            )

    return run
