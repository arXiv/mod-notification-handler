# tests/conftest.py
"""
Pytest database fixtures.

This setup:
- creates a SQLite test database from SQLAlchemy metadata
- loads seed data from tests/data.sql
- caches the built DB based on the SQL file hash
- gives each test an isolated copy of the DB
"""
from pathlib import Path
import hashlib
import shutil
import tempfile
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import arxiv.db as arxiv_db
from arxiv.db import session_factory, Session
from arxiv.db.models import metadata, configure_db_engine

ROOT_DIR = Path(__file__).resolve().parent.parent

SQL_DATA_FILE = ROOT_DIR / "tests" / "data.sql"
SAVED_DB_DIR = ROOT_DIR / "tests" / "databases"

SAVED_DB_DIR.mkdir(exist_ok=True)

def hash_file(path: Path) -> str:
    """Create a hash of a file to detect changes."""
    digest = hashlib.md5()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()

def create_engine_for_db(db_file: Path):
    """Create SQLite engine."""
    return create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )

def saved_db_path(sql_digest: str) -> Path:
    """Get cached DB path."""
    return SAVED_DB_DIR / f"{sql_digest}.sqlite.db"

def build_seed_database(sql_digest: str) -> Path:
    """
    Build a fresh SQLite DB from metadata + data.sql.
    """
    db_path = saved_db_path(sql_digest)

    if db_path.exists():
        raise RuntimeError(f"DB already exists: {db_path}")

    print(f"Creating seeded test DB at: {db_path}")

    engine = create_engine_for_db(db_path)
    session_factory.configure(bind=engine)

    # create tables
    metadata.create_all(bind=engine)

    # load seed data
    with engine.begin() as conn:
        with open(SQL_DATA_FILE, "r", encoding="utf-8") as f:
            sql = f.read()

        # raw sqlite connection needed for executescript
        conn.connection.executescript(sql)

    print("Finished building seeded DB")

    return db_path

def get_seed_database() -> Path:
    """
    Get cached seeded DB or build it if needed.
    """
    sql_digest = hash_file(SQL_DATA_FILE)

    db_path = saved_db_path(sql_digest)

    if db_path.exists():
        return db_path

    return build_seed_database(sql_digest)

@pytest.fixture()
def db_session():
    """
    Gives each test an isolated database session.

    Each test:
    - gets a copy of the seeded DB
    - can safely modify data
    - does not affect other tests
    """

    seed_db = get_seed_database()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_db = Path(tmpdir) / "test.sqlite.db"

        shutil.copyfile(seed_db, tmp_db)

        engine = create_engine_for_db(tmp_db)

        # Save original engines so we can restore after the test
        original_classic = arxiv_db._classic_engine
        original_latexml = arxiv_db._latexml_engine

        # Point arxiv.db.Session() at the isolated test db
        configure_db_engine(engine, None)
        Session.remove()

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )

        session = SessionLocal()

        try:
            yield session
        finally:
            session.close()
            engine.dispose()
            # Restore original engines
            configure_db_engine(original_classic, original_latexml)
            Session.remove()

