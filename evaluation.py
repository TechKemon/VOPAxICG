from __future__ import annotations

import csv
import logging
from pathlib import Path

import pandas as pd

from myca_recsys.models import RecommendationRequest, UserProfile
from myca_recsys.service import RecommendationEngine

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT_FOLDER = Path(__file__).resolve().parent
INPUT_CSV = PROJECT_FOLDER / "myca_eval_dataset.csv"
OUTPUT_CSV = PROJECT_FOLDER / "myca_eval_results.csv"

TITLE_TO_ID = {
    "emotional first aid": "C001",
    "understanding emotions": "C002",
    "understanding your emotions": "C002",
    "addiction awareness": "C003",
    "sexuality education": "C004",
    "exploring the mind": "C005",
    "suicide prevention": "C006",
    "suicide prevention (gkt program)": "C006",
    "teachers' mental health": "C007",
    "youth mental health": "C008",
}


def run_evaluation() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing evaluation dataset: {INPUT_CSV}")

    engine = RecommendationEngine()
    df = pd.read_csv(INPUT_CSV)
    rows = []
    top1_hits = 0
    top3_hits = 0

    for _, row in df.iterrows():
        text = _combined_text(row)
        expected_id = _expected_course_id(str(row.get("recommendation (8 courses)", "")))
        response = engine.recommend(RecommendationRequest(profile=_profile_from_row(row), chat_history=text, top_n=3))
        predicted_ids = [item.id for item in response.recommendations]
        top1_hits += int(bool(predicted_ids) and predicted_ids[0] == expected_id)
        top3_hits += int(expected_id in predicted_ids)
        rows.append(
            {
                "id": row.get("id"),
                "expected_course_id": expected_id,
                "predicted_course_ids": ",".join(predicted_ids),
                "top1_hit": bool(predicted_ids) and predicted_ids[0] == expected_id,
                "top3_hit": expected_id in predicted_ids,
                "safety_is_crisis": response.safety.is_crisis,
                "message": response.model_dump_json(),
            }
        )

    _write_results(rows)
    total = max(len(rows), 1)
    logger.info("Wrote %s", OUTPUT_CSV)
    logger.info("Top-1 accuracy: %.2f", top1_hits / total)
    logger.info("Top-3 accuracy: %.2f", top3_hits / total)


def _combined_text(row) -> str:
    return f"{row.get('context', '')}\n{row.get('conversation', '')}".strip()


def _profile_from_row(row) -> UserProfile:
    modules = str(row.get("modules (opt)", ""))
    return UserProfile(challenges=[item.strip() for item in modules.split(",") if item.strip()])


def _expected_course_id(label: str) -> str:
    normalized = label.split("(")[0].strip().lower()
    return TITLE_TO_ID.get(normalized, "")


def _write_results(rows: list[dict]) -> None:
    if not rows:
        return
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    run_evaluation()
