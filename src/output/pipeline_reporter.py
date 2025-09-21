from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PipelineReport:
    articles_processed: int
    issues_created: int
    groups_considered: int
    duplicates_skipped: int
    errors: int = 0

    def to_markdown(self) -> str:
        return (
            "### Pipeline Summary\n\n"
            f"- Articles processed: {self.articles_processed}\n"
            f"- Groups considered: {self.groups_considered}\n"
            f"- Issues created: {self.issues_created}\n"
            f"- Duplicates skipped: {self.duplicates_skipped}\n"
            f"- Errors: {self.errors}\n"
        )
