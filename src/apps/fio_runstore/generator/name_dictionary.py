import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple


DEFAULT_NAMES_CSV_PATH = Path("src/data/dictionaries/names.csv")


@dataclass(frozen=True)
class NameDictMeta:
    path: str
    sha256: str
    total_rows: int
    enabled_rows: int


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_names_variant_map(
    *,
    csv_path: Path = DEFAULT_NAMES_CSV_PATH,
) -> Tuple[Dict[str, str], NameDictMeta]:
    """
    Load names dictionary as mapping: variant -> canonical.

    Rules:
    - Only enabled=1 rows are included.
    - If the same variant appears multiple times, the first occurrence wins.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Names dictionary not found: {csv_path}")

    sha256 = _sha256_of_file(csv_path)

    variant_to_canonical: Dict[str, str] = {}
    total_rows = 0
    enabled_rows = 0

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"canonical", "variant", "enabled", "note", "source"}
        if not reader.fieldnames or set(reader.fieldnames) < required:
            raise ValueError(
                f"Invalid names.csv header. Expected columns: {sorted(required)}; got: {reader.fieldnames}"
            )

        for row in reader:
            total_rows += 1
            canonical = (row.get("canonical") or "").strip()
            variant = (row.get("variant") or "").strip()
            enabled = (row.get("enabled") or "").strip()

            if not canonical or not variant:
                continue

            if enabled != "1":
                continue

            enabled_rows += 1
            if variant not in variant_to_canonical:
                variant_to_canonical[variant] = canonical

    meta = NameDictMeta(
        path=str(csv_path),
        sha256=sha256,
        total_rows=total_rows,
        enabled_rows=enabled_rows,
    )
    return variant_to_canonical, meta
