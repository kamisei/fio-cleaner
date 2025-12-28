import os
from django.core.files.storage import default_storage
from django.shortcuts import render
from django.utils import timezone


def upload_csv(request):
    context = {}

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

    return render(request, "uploads/upload.html", context)
