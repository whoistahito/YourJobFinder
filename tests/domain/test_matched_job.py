"""Domain entity tests for MatchedJob.

TDD: these tests drive the design of the entity. No SQLAlchemy, no Flask.
Run: pytest tests/domain/test_matched_job.py
"""
from datetime import datetime, timezone

import pytest

from domain.matched_job import MatchedJob


def test_matched_job_holds_the_fields_the_dashboard_needs():
    created = datetime(2026, 6, 28, 7, 0, tzinfo=timezone.utc)
    job = MatchedJob(
        id=1,
        user_id="u-1",
        title="Senior Frontend Engineer",
        company="Linear",
        location="Remote (EU)",
        job_url="https://example.com/job/1",
        date_posted="2026-06-28",
        score=96,
        created_at=created,
    )
    assert job.title == "Senior Frontend Engineer"
    assert job.company == "Linear"
    assert job.location == "Remote (EU)"
    assert job.score == 96
    assert job.user_id == "u-1"


def test_score_is_an_integer_fit_percentage_0_to_100():
    MatchedJob(
        id=1, user_id="u-1", title="t", company="c", location="l",
        job_url="u", date_posted=None, score=0, created_at=datetime.now(timezone.utc),
    )
    MatchedJob(
        id=2, user_id="u-1", title="t", company="c", location="l",
        job_url="u", date_posted=None, score=100, created_at=datetime.now(timezone.utc),
    )


@pytest.mark.parametrize("bad_score", [-1, 101, 150])
def test_score_outside_0_100_is_rejected(bad_score):
    with pytest.raises(ValueError):
        MatchedJob(
            id=1, user_id="u-1", title="t", company="c", location="l",
            job_url="u", date_posted=None, score=bad_score,
            created_at=datetime.now(timezone.utc),
        )


def test_unscored_match_is_allowed_when_matcher_was_skipped():
    """A job from a profile-less user has no fit %; score=None must be valid."""
    job = MatchedJob(
        id=1, user_id="u-1", title="t", company="c", location="l",
        job_url="u", date_posted=None, score=None,
        created_at=datetime.now(timezone.utc),
    )
    assert job.score is None


def test_two_matched_jobs_with_same_id_are_equal():
    """Entity identity is the id, not field values."""
    a = MatchedJob(
        id=1, user_id="u-1", title="A", company="c", location="l",
        job_url="u", date_posted=None, score=80, created_at=datetime.now(timezone.utc),
    )
    b = MatchedJob(
        id=1, user_id="u-2", title="B", company="d", location="l",
        job_url="v", date_posted=None, score=20, created_at=datetime.now(timezone.utc),
    )
    assert a == b
    assert hash(a) == hash(b)