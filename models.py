from dataclasses import dataclass


@dataclass(frozen=True)
class ResumeResult:
    filename: str
    score: float
    matched_skills: set[str]
    missing_skills: set[str]
    section_scores: dict[str, float]
    boosters: list[tuple[str, float]]
    draggers: list[tuple[str, float]]

    @property
    def score_pct(self) -> float:
        return self.score * 100

    @property
    def skill_match_pct(self) -> float:
        total = len(self.matched_skills) + len(self.missing_skills)
        return (len(self.matched_skills) / total * 100) if total else 0.0

    @property
    def display_name(self) -> str:
        return self.filename.replace(".pdf", "")
