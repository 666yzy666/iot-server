from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import Settings

_engine = None
_SessionLocal = None


def _get_engine(settings: Settings | None = None):
    global _engine
    if _engine is None:
        s = settings or Settings.from_env()
        _engine = create_engine(s.database_url, pool_pre_ping=True)
    return _engine


def _get_session_local(settings: Settings | None = None):
    global _SessionLocal
    if _SessionLocal is None:
        engine = _get_engine(settings)
        _SessionLocal = sessionmaker(bind=engine, future=True)
    return _SessionLocal


def get_session(settings: Settings | None = None):
    local = _get_session_local(settings)
    with local() as session:
        yield session
