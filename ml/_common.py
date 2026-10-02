"""Shared helpers for the offline ML scripts (run from anywhere)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "backend", ROOT / "database"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import pandas as pd  # noqa: E402

DATASETS = ROOT / "ml" / "datasets"


def destinations_frame() -> pd.DataFrame:
    df = pd.read_csv(DATASETS / "destinations.csv")
    df["tags"] = df["tags"].str.split("|")
    return df


def destination_texts(df: pd.DataFrame) -> list[str]:
    from app.ml.semantic import destination_text

    return [destination_text(r.name, r.category, r.tags, r.description) for r in df.itertuples()]
