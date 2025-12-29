from django.contrib import admin
from .models import Run, Suggestion


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "source_csv_path",
    )
    ordering = ("-id",)
    readonly_fields = (
        "created_at",
    )


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "run",
        "row_id",
        "field_name",
        "before_value",
        "suggested_value",
        "confidence",
        "suggestion_code",
    )
    list_filter = (
        "confidence",
        "suggestion_code",
    )
    search_fields = (
        "before_value",
        "suggested_value",
    )
    readonly_fields = (
        "created_at",
        "generator",
        "generator_version",
        "dictionary_hash",
    )
