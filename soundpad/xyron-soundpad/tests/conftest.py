import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from soundpad.core.config import SettingsStore
from soundpad.core.logging_setup import reset_logging
from soundpad.database.session import Database
from soundpad.services.library_service import LibraryService


@pytest.fixture(autouse=True)
def _isolated_logging():
    yield
    reset_logging()


@pytest.fixture
def database():
    db = Database(None)
    yield db
    db.dispose()


@pytest.fixture
def library(database):
    service = LibraryService(database)
    service.initialize()
    return service


@pytest.fixture
def settings_store(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    store.load()
    return store
