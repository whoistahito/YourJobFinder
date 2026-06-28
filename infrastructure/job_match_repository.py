"""SQLAlchemy ORM model + repository implementation for MatchedJob.

The ORM row lives here (not in db/models.py) so the domain layer never sees it.
`db/models.py` re-imports `OrmMatchedJob` so Flask-Migrate's autogenerate still
sees the table.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from extension import db
from domain.matched_job import MatchedJob
from domain.job_match_repository import JobMatchRepository


class OrmMatchedJob(db.Model):
    __tablename__ = "job_matches"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    title = db.Column(db.String, nullable=False)
    company = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=True)
    job_url = db.Column(db.String, nullable=False)
    date_posted = db.Column(db.String, nullable=True)
    score = db.Column(db.Integer, nullable=True)  # 0–100 or NULL when matcher skipped
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


def to_domain(orm: OrmMatchedJob) -> MatchedJob:
    return MatchedJob(
        id=orm.id,
        user_id=orm.user_id,
        title=orm.title,
        company=orm.company,
        location=orm.location,
        job_url=orm.job_url,
        date_posted=orm.date_posted,
        score=orm.score,
        created_at=orm.created_at,
    )


class SqlAlchemyJobMatchRepository(JobMatchRepository):
    """Concrete repo backed by Flask-SQLAlchemy. Must run inside an
    `app.app_context()` (or test equivalent)."""

    def __init__(self, db):
        self._db = db

    def list_for_user(self, user_id: str) -> list[MatchedJob]:
        if not user_id:
            return []
        rows = self._db.session.query(OrmMatchedJob).filter_by(user_id=user_id).all()
        return [to_domain(r) for r in rows]

    def save(self, matched_job: MatchedJob) -> MatchedJob:
        existing = (
            self._db.session.get(OrmMatchedJob, matched_job.id)
            if matched_job.id
            else None
        )
        if existing is None:
            existing = OrmMatchedJob(
                id=matched_job.id if matched_job.id else None,
                user_id=matched_job.user_id,
                title=matched_job.title,
                company=matched_job.company,
                location=matched_job.location,
                job_url=matched_job.job_url,
                date_posted=matched_job.date_posted,
                score=matched_job.score,
                created_at=matched_job.created_at,
            )
            self._db.session.add(existing)
        else:
            existing.user_id = matched_job.user_id
            existing.title = matched_job.title
            existing.company = matched_job.company
            existing.location = matched_job.location
            existing.job_url = matched_job.job_url
            existing.date_posted = matched_job.date_posted
            existing.score = matched_job.score
            existing.created_at = matched_job.created_at
        self._db.session.commit()
        return to_domain(existing)