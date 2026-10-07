import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import pytest


@pytest.fixture(autouse=True)
def _init_test_db(tmp_path, monkeypatch):
    """Point DATABASE_URL at a temp sqlite file and create tables before each test."""
    db_file = tmp_path / "mia_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    import core.database as database

    database.engine.dispose()
    database.engine = database.create_engine(
        f"sqlite:///{db_file}", pool_pre_ping=True, connect_args={"check_same_thread": False}
    )
    database.SessionLocal = database.sessionmaker(
        bind=database.engine, autoflush=False, autocommit=False
    )
    database.init_db()
    yield

