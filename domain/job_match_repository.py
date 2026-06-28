"""Repository port for MatchedJob persistence.

Domain owns the interface; infrastructure provides the implementation
(SqlAlchemyJobMatchRepository). Tests inject an in-memory fake.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domain.matched_job import MatchedJob


class JobMatchRepository(ABC):
    @abstractmethod
    def list_for_user(self, user_id: str) -> list[MatchedJob]:
        """Return all matches for the given user, repository order not defined."""
        raise NotImplementedError

    @abstractmethod
    def save(self, matched_job: MatchedJob) -> MatchedJob:
        """Persist a single match. Return the stored entity."""
        raise NotImplementedError