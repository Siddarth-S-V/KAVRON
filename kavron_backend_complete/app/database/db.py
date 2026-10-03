from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()

database_url = settings.database_url

connect_args: dict = {}

if database_url.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
    }


engine = create_engine(
    database_url,
    connect_args=connect_args,
    future=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def init_db() -> None:
    """
    Import every SQLAlchemy model before create_all().
    """

    from app.database import models  # noqa: F401

    db_path = None

    if database_url.startswith("sqlite:///"):
        raw_path = database_url.replace(
            "sqlite:///",
            "",
            1,
        )

        db_path = Path(raw_path)

        if db_path.parent:
            db_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

    print("=" * 70)
    print("KAVRON DATABASE INITIALIZATION")
    print(f"DATABASE URL: {database_url}")

    if db_path is not None:
        print(f"DATABASE FILE: {db_path.resolve()}")

    print(
        "REGISTERED TABLES:",
        list(Base.metadata.tables.keys()),
    )

    Base.metadata.create_all(
        bind=engine,
        checkfirst=True,
    )

    # Lightweight SQLite migrations for packages upgraded in-place.
    # create_all() does not add new columns to an existing table.
    if database_url.startswith("sqlite:///"):
        inspector = inspect(engine)
        camera_columns = {col["name"] for col in inspector.get_columns("cameras")}
        migrations = {
            "latitude": "ALTER TABLE cameras ADD COLUMN latitude FLOAT",
            "longitude": "ALTER TABLE cameras ADD COLUMN longitude FLOAT",
            "location_accuracy_m": "ALTER TABLE cameras ADD COLUMN location_accuracy_m FLOAT",
            "location_source": "ALTER TABLE cameras ADD COLUMN location_source VARCHAR(32) DEFAULT 'manual'",
        }
        with engine.begin() as conn:
            for column, statement in migrations.items():
                if column not in camera_columns:
                    conn.execute(text(statement))
                    print(f"[KAVRON] Database migration applied: cameras.{column}")

    print("DATABASE READY")
    print("=" * 70)


def db_session():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()