
from django.db import models


class Run(models.Model):
    """
    A single processing run for a CSV file.
    Stores context required for reproducibility.
    """

    created_at = models.DateTimeField(auto_now_add=True)

    source_csv_path = models.CharField(
        max_length=500,
        help_text="Path to the source CSV file in storage",
    )

    selection = models.JSONField(
        help_text="Selected FIO columns and mode (single/split)",
    )

    encoding = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Detected CSV encoding",
    )

    delimiter = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        help_text="Detected CSV delimiter",
    )

    def __str__(self):
        return f"Run #{self.id} ({self.created_at:%Y-%m-%d %H:%M:%S})"


class Suggestion(models.Model):
    """
    A proposed correction for a single field in a single row within a Run.
    No automatic changes are applied.
    """

    CONFIDENCE_HIGH = "high"
    CONFIDENCE_MEDIUM = "medium"
    CONFIDENCE_CHOICES = [
        (CONFIDENCE_HIGH, "high"),
        (CONFIDENCE_MEDIUM, "medium"),
    ]

    DECISION_PROPOSED = "proposed"
    DECISION_ACCEPTED = "accepted"
    DECISION_REJECTED = "rejected"
    DECISION_EDITED = "edited"
    DECISION_CHOICES = [
        (DECISION_PROPOSED, "proposed"),
        (DECISION_ACCEPTED, "accepted"),
        (DECISION_REJECTED, "rejected"),
        (DECISION_EDITED, "edited"),
    ]

    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE,
        related_name="suggestions",
    )

    row_id = models.PositiveIntegerField(
        help_text="1-based row number in the source CSV",
    )

    field_name = models.CharField(
        max_length=50,
        help_text="Target field name (fio, first_name, last_name, etc.)",
    )

    before_value = models.TextField(
        blank=True,
        help_text="Original value before suggestion",
    )

    suggested_value = models.TextField(
        help_text="Proposed corrected value",
    )

    suggestion_code = models.CharField(
        max_length=100,
        help_text="Machine-readable suggestion reason code",
    )

    confidence = models.CharField(
        max_length=10,
        choices=CONFIDENCE_CHOICES,
    )

    message = models.TextField(
        help_text="Human-readable explanation of the suggestion",
    )

    evidence = models.JSONField(
        null=True,
        blank=True,
        help_text="Structured evidence supporting the suggestion",
    )

    generator = models.CharField(
        max_length=100,
        help_text="Suggestion generator identifier",
    )

    generator_version = models.CharField(
        max_length=50,
        help_text="Version of the suggestion generator",
    )

    dictionary_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Hash of the dictionary version used, if applicable",
    )

    decision_status = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        default=DECISION_PROPOSED,
    )

    decision_value = models.TextField(
        null=True,
        blank=True,
        help_text="Final value chosen by the user, if edited",
    )

    decided_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "run",
                    "row_id",
                    "field_name",
                    "suggestion_code",
                    "suggested_value",
                ],
                name="uniq_suggestion_per_run_row_field_reason_value",
            )
        ]

    def __str__(self):
        return (
            f"Suggestion(run={self.run_id}, row={self.row_id}, "
            f"field={self.field_name}, value={self.suggested_value})"
        )
