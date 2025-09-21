from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class PipelineConfig:
    horizon_weeks: int = int(os.getenv("PIPELINE_HORIZON_WEEKS", "4"))
    min_score: float = float(os.getenv("PIPELINE_MIN_SCORE", "0.7"))
    group_max_items: int = int(os.getenv("PIPELINE_GROUP_MAX_ITEMS", "4"))
    default_assignees_csv: str = os.getenv("PIPELINE_DEFAULT_ASSIGNEES", "")

    @property
    def default_assignees(self) -> list[str]:
        return [a.strip() for a in self.default_assignees_csv.split(",") if a.strip()]
