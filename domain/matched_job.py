"""Domain entity for a job matched against a user's profile.

Pure-Python dataclass — no ORM, no Flask, no I/O. Identity is the `id` field;
two MatchedJobs with the same id are the same entity even if their other fields
differ. `score` is a fit percentage 0–100 (None when the matcher was skipped,
e.g. a profile-less user whose scraped jobs were sent unfiltered).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class MatchedJob:
    id: int
    user_id: str
    title: str
    company: str
    location: str
    job_url: str
    date_posted: Optional[str]
    score: Optional[int]
    created_at: datetime

    def __post_init__(self) -> None:
        if self.score is not None and not (0 <= self.score <= 100):
            raise ValueError(
                f"score must be a fit percentage 0–100 or None, got {self.score}"
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MatchedJob):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)