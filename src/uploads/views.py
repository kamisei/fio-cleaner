import csv
import io
import os

from django.core.files.storage import default_storage
from django.shortcuts import render
from django.utils import timezone

PREVIEW_ROWS = 20
SNIFF_BYTES = 8192

# Practical set for real-world Russian CSV:
# - UTF-8 with/without BOM
# - Windows-1251 (very common in exports)
ENCODINGS_TO_TRY = ["utf-8-sig", "cp1251"]


def _decode_sample(sample_bytes: bytes):
    for enc in ENCODINGS_TO_TRY:
        try:
            return sample_bytes.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError(
        "Не удалось прочитать файл. Поддерживаются UTF-8 и Windows-1251 (cp1251)."
    )


def _read_csv_preview(storage_path: str):
    """
    Returns:
      columns: list[str]
      rows: list[list[str]]
      encoding_used: str
      delimiter_used: str
    Raises ValueError with a user-friendly message on failure.
    """
    with default_storage.open(storage_path, "rb") as f:
        sample_bytes = f.read(SNIFF_BYTES)

    if not sample_bytes:
        raise ValueError("Файл пустой: нет данных для предпросмотра.")

    sample_text, encoding_used = _decode_sample(sample_bytes)

    # Delimiter: sniff, else comma.
    delimiter_used = ","
    dialect = csv.get_dialect("excel")
    try:
        sniffed = csv.Sniffer().sniff(sample_text)
        if sniffed.delimiter in [",", ";", "\t", "|"]:
            dialect = sniffed
            delimiter_used = sniffed.delimiter
    except Exception:
        dialect = csv.get_dialect("excel")
        delimiter_used = ","

    # Read the file for real using the selected encoding.
    with default_storage.open(storage_path, "rb") as raw:
        text = io.TextIOWrapper(raw, encoding=encoding_used, newline="")
        reader = csv.reader(text, dialect=dialect)

        header = next(reader, None)
        if header is None:
            raise ValueError("Файл пустой: нет данных для предпросмотра.")

        columns = [str(c).strip() for c in header]
        if not any(columns):
            raise ValueError("Не удалось прочитать заголовки столбцов.")

        rows = []
        for _ in range(PREVIEW_ROWS):
            row = next(reader, None)
            if row is None:
                break
            rows.append([str(c).strip() for c in row])

    return columns, rows, encoding_used, delimiter_used


def upload_csv(request):
    context = {"preview_rows_limit": PREVIEW_ROWS}

    if request.method == "POST":
        uploaded = request.FILES.get("csv_file")

        if not uploaded:
            context["error"] = "Файл не выбран."
            return render(request, "uploads/upload.html", context)

        name_lower = uploaded.name.lower()
        if not name_lower.endswith(".csv"):
            context["error"] = "Пожалуйста, загрузите файл в формате .csv."
            return render(request, "uploads/upload.html", context)

        base, ext = os.path.splitext(os.path.basename(uploaded.name))
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"{base}_{timestamp}{ext}"

        saved_path = default_storage.save(f"uploads/{safe_name}", uploaded)

        context["success"] = True
        context["original_name"] = uploaded.name
        context["saved_path"] = saved_path
        context["file_url"] = default_storage.url(saved_path)

        try:
            columns, rows, encoding_used, delimiter_used = _read_csv_preview(saved_path)
            context["preview_columns"] = columns
            context["preview_rows"] = rows
            context["preview_encoding"] = encoding_used
            context["preview_delimiter"] = delimiter_used
        except ValueError as e:
            context["preview_error"] = str(e)
        except Exception:
            context["preview_error"] = "Не удалось построить предпросмотр файла."

    return render(request, "uploads/upload.html", context)
