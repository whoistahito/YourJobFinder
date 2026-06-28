"""Infrastructure-layer tests for SqlAlchemyJobMatchRepository.

These touch SQLAlchemy, but only against an in-memory sqlite DB built from the
ORM models — no SSH tunnel, no Postgres, no Flask appContext. They verify the
domain entity <-> ORM row translation and per-user filtering.
Run: pytest tests/infrastructure/test_sqlalchemy_job_match_repository.py
"""
from datetime import datetime, timezone

from extension import db
from infrastructure.app_factory import create_app
from infrastructure.job_match_repository import SqlAlchemyJobMatchRepository
from domain.matched_job import MatchedJob


def _mk(mid, user_id="u-1", score=80):
    return MatchedJob(
        id=mid, user_id=user_id, title=f"t{mid}", company="Linear",
        location="Remote (EU)", job_url=f"https://x/{mid}",
        date_posted="2026-06-28", score=score,
        created_at=datetime(2026, 6, 28, 7, 0, tzinfo=timezone.utc),
    )


def test_save_then_list_round_trips_every_field():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        repo = SqlAlchemyJobMatchRepository(db)

        saved = repo.save(_mk(1))
        assert saved == _mk(1)

        listed = repo.list_for_user("u-1")
        assert len(listed) == 1
        m = listed[0]
        assert m.id == 1
        assert m.user_id == "u-1"
        assert m.title == "t1"
        assert m.company == "Linear"
        assert m.location == "Remote (EU)"
        assert m.job_url == "https://x/1"
        assert m.date_posted == "2026-06-28"
        assert m.score == 80


def test_unscored_match_round_trips_with_none():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        repo = SqlAlchemyJobMatchRepository(db)
        repo.save(_mk(1, score=None))

        m = repo.list_for_user("u-1")[0]
        assert m.score is None


def test_list_for_user_filters_out_other_users_rows():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        repo = SqlAlchemyJobMatchRepository(db)
        repo.save(_mk(1, user_id="u-1", score=80))
        repo.save(_mk(2, user_id="u-2", score=70))

        assert len(repo.list_for_user("u-1")) == 1
        assert len(repo.list_for_user("u-2")) == 1
        assert repo.list_for_user("u-unknown") == []


def test_empty_user_id_returns_empty_list():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        repo = SqlAlchemyJobMatchRepository(db)
        repo.save(_mk(1, user_id="u-1"))
        assert repo.list_for_user("") == []