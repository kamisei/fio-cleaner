import csv
import io
import os

from django.core.files.storage import default_storage
from django.shortcuts import render
from django.utils import timezone


# Domain (Step 2.2)
from domain.fio.normalize_value import normalize_fio_value
from domain.fio.quality_checks import detect_warnings
from domain.fio.quality_checks import detect_flags
from domain.fio.constants import ATTENTION_LABEL_RU, WARNING_LABELS_RU, FLAG_LABELS_RU
PREVIEW_ROWS = 20
SNIFF_BYTES = 8192

# Practical set for real-world Russian CSV
ENCODINGS_TO_TRY = ["utf-8-sig", "cp1251"]

# Session keys
S_ACTIVE_FILE = "active_csv_path"
S_SELECTION = "fio_selection"


def _decode_sample(sample_bytes: bytes):
    for enc in ENCODINGS_TO_TRY:
        try:
            return sample_bytes.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError("Не удалось прочитать файл. Поддерживаются UTF-8 и Windows-1251 (cp1251).")


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


def _compute_column_stats(columns, rows, selected_column_names, examples_limit=5):
    """
    For each selected column name computes:
      - filled_count
      - fill_rate (%)
      - examples (up to examples_limit non-empty values)
    Returns (rows_checked, stats_dict, warnings_list).
    """
    col_index = {name: i for i, name in enumerate(columns)}
    rows_checked = len(rows)
    warnings = []
    stats = {}

    for name in selected_column_names:
        if name not in col_index:
            warnings.append(f"Столбец «{name}» не найден в заголовках.")
            continue

        idx = col_index[name]
        filled = 0
        examples = []

        for r in rows:
            val = r[idx] if idx < len(r) else ""
            val = (val or "").strip()
            if val:
                filled += 1
                if len(examples) < examples_limit and val not in examples:
                    examples.append(val)

        fill_rate = (filled / rows_checked * 100.0) if rows_checked > 0 else 0.0
        stats[name] = {
            "filled_count": filled,
            "fill_rate": round(fill_rate, 1),
            "examples": examples,
        }

    return rows_checked, stats, warnings


def _load_active_file_from_session(request):
    return request.session.get(S_ACTIVE_FILE)


def _save_selection_to_session(request, selection: dict):
    request.session[S_SELECTION] = selection
    request.session.modified = True


def _get_selection_from_session(request):
    return request.session.get(S_SELECTION)


def upload_csv(request):
    context = {
        "preview_rows_limit": PREVIEW_ROWS,
        "selection_modes": [
            ("single", "Одно поле (ФИО целиком)"),
            ("split", "Отдельные поля (Ф/И/О)"),
        ],
    }

    # If we already have an active file in session, try to show its preview on GET
    active_path = _load_active_file_from_session(request)
    selection = _get_selection_from_session(request)
    context["saved_selection"] = selection

    def hydrate_preview_for_active_file():
        nonlocal active_path
        if not active_path:
            return
        try:
            columns, rows, encoding_used, delimiter_used = _read_csv_preview(active_path)
            context["has_active_file"] = True
            context["preview_columns"] = columns
            context["preview_rows"] = rows
            context["preview_encoding"] = encoding_used
            context["preview_delimiter"] = delimiter_used
            context["rows_checked"] = len(rows)
        except ValueError as e:
            context["has_active_file"] = True
            context["preview_error"] = str(e)
        except Exception:
            context["has_active_file"] = True
            context["preview_error"] = "Не удалось построить предпросмотр файла."

    if request.method == "POST":
        action = request.POST.get("action", "upload")

        # 1) Upload action: handle file upload, save, preview, reset selection
        if action == "upload":
            uploaded = request.FILES.get("csv_file")

            if not uploaded:
                context["error"] = "Файл не выбран."
                hydrate_preview_for_active_file()
                return render(request, "uploads/upload.html", context)

            name_lower = uploaded.name.lower()
            if not name_lower.endswith(".csv"):
                context["error"] = "Пожалуйста, загрузите файл в формате .csv."
                hydrate_preview_for_active_file()
                return render(request, "uploads/upload.html", context)

            base, ext = os.path.splitext(os.path.basename(uploaded.name))
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            safe_name = f"{base}_{timestamp}{ext}"

            saved_path = default_storage.save(f"uploads/{safe_name}", uploaded)

            # Save active file in session and reset selection for new file
            request.session[S_ACTIVE_FILE] = saved_path
            request.session.pop(S_SELECTION, None)
            request.session.modified = True

            context["success"] = True
            context["original_name"] = uploaded.name
            context["saved_path"] = saved_path
            context["file_url"] = default_storage.url(saved_path)
            context["has_active_file"] = True

            try:
                columns, rows, encoding_used, delimiter_used = _read_csv_preview(saved_path)
                context["preview_columns"] = columns
                context["preview_rows"] = rows
                context["preview_encoding"] = encoding_used
                context["preview_delimiter"] = delimiter_used
                context["rows_checked"] = len(rows)
            except ValueError as e:
                context["preview_error"] = str(e)
            except Exception:
                context["preview_error"] = "Не удалось построить предпросмотр файла."

            return render(request, "uploads/upload.html", context)

        # 2) Select action: save selection in session and compute metrics
        if action == "select":
            active_path = _load_active_file_from_session(request)
            if not active_path:
                context["selection_error"] = "Сначала загрузите CSV-файл."
                return render(request, "uploads/upload.html", context)

            # Read preview data to compute metrics
            try:
                columns, rows, encoding_used, delimiter_used = _read_csv_preview(active_path)
                context["has_active_file"] = True
                context["preview_columns"] = columns
                context["preview_rows"] = rows
                context["preview_encoding"] = encoding_used
                context["preview_delimiter"] = delimiter_used
                context["rows_checked"] = len(rows)
            except ValueError as e:
                context["has_active_file"] = True
                context["preview_error"] = str(e)
                context["selection_error"] = "Невозможно сохранить выбор, потому что предпросмотр не построен."
                return render(request, "uploads/upload.html", context)
            except Exception:
                context["has_active_file"] = True
                context["preview_error"] = "Не удалось построить предпросмотр файла."
                context["selection_error"] = "Невозможно сохранить выбор, потому что предпросмотр не построен."
                return render(request, "uploads/upload.html", context)

            mode = request.POST.get("fio_mode", "").strip()
            if mode not in ("single", "split"):
                context["selection_error"] = "Выберите режим: одно поле или отдельные поля."
                return render(request, "uploads/upload.html", context)

            selection_payload = {"mode": mode}

            selected_columns_for_metrics = []
            human_labels = []

            if mode == "single":
                fio_col = request.POST.get("fio_column", "").strip()
                if not fio_col:
                    context["selection_error"] = "Выберите столбец с ФИО (одно поле)."
                    return render(request, "uploads/upload.html", context)

                selection_payload["fio_column"] = fio_col
                selected_columns_for_metrics = [fio_col]
                human_labels = [("ФИО", fio_col)]

            else:  # split
                last_col = request.POST.get("last_name_column", "").strip()
                first_col = request.POST.get("first_name_column", "").strip()
                middle_col = request.POST.get("middle_name_column", "").strip()

                # Empty string means "not used"
                selection_payload["last_name_column"] = last_col or None
                selection_payload["first_name_column"] = first_col or None
                selection_payload["middle_name_column"] = middle_col or None

                chosen = [c for c in [last_col, first_col, middle_col] if c]
                if not chosen:
                    context["selection_error"] = "Выберите хотя бы одно поле: фамилия / имя / отчество."
                    return render(request, "uploads/upload.html", context)

                if last_col:
                    human_labels.append(("Фамилия", last_col))
                    selected_columns_for_metrics.append(last_col)
                if first_col:
                    human_labels.append(("Имя", first_col))
                    selected_columns_for_metrics.append(first_col)
                if middle_col:
                    human_labels.append(("Отчество", middle_col))
                    selected_columns_for_metrics.append(middle_col)

            _save_selection_to_session(request, selection_payload)
            context["saved_selection"] = selection_payload
            context["selection_saved"] = True

            rows_checked, stats, warnings = _compute_column_stats(
                columns=columns,
                rows=rows,
                selected_column_names=selected_columns_for_metrics,
                examples_limit=5,
            )

            context["selection_human"] = human_labels
            context["metrics_rows_checked"] = rows_checked
            context["metrics_stats"] = stats
            context["metrics_warnings"] = warnings

            # Non-blocking warnings (optional UX)
            if rows_checked == 0:
                context["metrics_general_warning"] = (
                    "В файле нет строк данных для предпросмотра (возможно, только заголовок). "
                    "Выбор сохранён, но метрики заполненности не информативны."
                )

            return render(request, "uploads/upload.html", context)

    # GET path: show preview for active file if any
    hydrate_preview_for_active_file()
    return render(request, "uploads/upload.html", context)

def normalize_preview(request):
    """
    Step 2.3: normalization preview page (no persistence).
    Shows how Step 2.2 safe normalization changes values for selected FIO columns.
    """
    active_path = _load_active_file_from_session(request)
    selection = _get_selection_from_session(request)

    context = {
        "active_path": active_path,
        "selection": selection,
        "preview_rows_limit": PREVIEW_ROWS,
        "items": [],
        "error": None,
    }

    if not active_path:
        context["error"] = "Сначала загрузите CSV-файл."
        return render(request, "uploads/normalize_preview.html", context)

    if not selection or not isinstance(selection, dict) or selection.get("mode") not in ("single", "split"):
        context["error"] = "Сначала выберите поле(я) ФИО на странице загрузки."
        return render(request, "uploads/normalize_preview.html", context)

    try:
        columns, rows, encoding_used, delimiter_used = _read_csv_preview(active_path)
        context["preview_encoding"] = encoding_used
        context["preview_delimiter"] = delimiter_used
    except ValueError as e:
        context["error"] = str(e)
        return render(request, "uploads/normalize_preview.html", context)
    except Exception:
        context["error"] = "Не удалось построить предпросмотр файла."
        return render(request, "uploads/normalize_preview.html", context)

    col_index = {name: i for i, name in enumerate(columns)}

    # Build list of (label, column_name)
    selected_fields = []
    if selection["mode"] == "single":
        col = selection.get("fio_column")
        if col:
            selected_fields.append(("фио", col))
    else:
        mapping = [
            ("фамилия", selection.get("last_name_column")),
            ("имя", selection.get("first_name_column")),
            ("отчество", selection.get("middle_name_column")),
        ]
        for label, col in mapping:
            if col:
                selected_fields.append((label, col))

    if not selected_fields:
        context["error"] = "Выбор полей ФИО пустой. Вернитесь назад и выберите хотя бы одно поле."
        return render(request, "uploads/normalize_preview.html", context)

    # Prepare preview items
    items = []
    for row_i, r in enumerate(rows, start=1):
        for field_label, col_name in selected_fields:
            idx = col_index.get(col_name)
            before_val = r[idx] if idx is not None and idx < len(r) else ""
            result = normalize_fio_value(before_val)

            items.append(
                {
                    "row_num": row_i,
                    "field_label": field_label,
                    "column_name": col_name,
                    "before": before_val,
                    "after": result.after,
                    "status": None,  # computed below
                    "applied_rules": ", ".join(result.applied_rules) if result.applied_rules else "",
                    "warnings": detect_warnings(before_val),
                    "attention": ATTENTION_LABEL_RU if detect_warnings(before_val) else "",
                    "attention_reasons": ", ".join(WARNING_LABELS_RU[w] for w in detect_warnings(before_val)) if detect_warnings(before_val) else "",
                    "flags": "",
                    "comment": "",
                }
            )
            flags = detect_flags(before_val)

            if flags:
                status = "needs_review"
                flags_str = ", ".join(flags)
                comment = ", ".join(FLAG_LABELS_RU[f] for f in flags)
            else:
                status = result.status
                flags_str = ""
                comment = ""

            items[-1]["status"] = status
            items[-1]["flags"] = flags_str
            items[-1]["comment"] = comment


    total = len(items)
    ok_count = sum(1 for it in items if it.get("status") == "ok")
    fixed_count = sum(1 for it in items if it.get("status") == "fixed")
    attention_count = sum(1 for it in items if it.get("attention"))
    needs_review_count = sum(1 for it in items if it.get("status") == "needs_review")
    context["stats"] = {
        "total": total,
        "ok": ok_count,
        "fixed": fixed_count,
        "attention": attention_count,
        "needs_review": needs_review_count,
        "ok_pct": round((ok_count / total * 100.0), 1) if total else 0.0,
        "fixed_pct": round((fixed_count / total * 100.0), 1) if total else 0.0,
        "attention_pct": round((attention_count / total * 100.0), 1) if total else 0.0,
        "needs_review_pct": round((needs_review_count / total * 100.0), 1) if total else 0.0,
    }

    context["items"] = items
    return render(request, "uploads/normalize_preview.html", context)

