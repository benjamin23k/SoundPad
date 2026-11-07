import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from soundpad.database.models import Base

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_file: Path | None) -> None:
        if db_file is None:
            url = "sqlite+pysqlite:///:memory:"
        else:
            db_file.parent.mkdir(parents=True, exist_ok=True)
            url = f"sqlite+pysqlite:///{db_file.as_posix()}"
        self.engine: Engine = create_engine(url, future=True)
        event.listen(self.engine, "connect", _configure_sqlite)
        self._factory = sessionmaker(self.engine, expire_on_commit=False, future=True)

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)
        logger.info("Esquema de base de datos verificado")

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()


def _configure_sqlite(dbapi_connection, _record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
