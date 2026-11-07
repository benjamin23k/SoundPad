import logging
from dataclasses import dataclass
from pathlib import Path

from soundpad.database.repositories import (
    CategoryRepository,
    SoundRecord,
    SoundRepository,
)
from soundpad.database.session import Database
from soundpad.soundboard.importer import ImportResult, SoundImporter

logger = logging.getLogger(__name__)

SCOPE_ALL = "all"
SCOPE_UNCATEGORIZED = "uncategorized"


@dataclass(frozen=True)
class CategoryEntry:
    key: str
    name: str
    count: int
    scope: str
    category_id: int | None
    is_system: bool


@dataclass(frozen=True)
class ImportSummary:
    imported: int
    skipped: list[tuple[str, str]]


class LibraryService:
    def __init__(self, database: Database, sounds_dir: Path | None = None) -> None:
        self._db = database
        self._importer = SoundImporter(sounds_dir) if sounds_dir is not None else None

    def initialize(self) -> None:
        self._db.create_schema()
        with self._db.session() as session:
            CategoryRepository(session).ensure_defaults()

    def category_entries(self) -> list[CategoryEntry]:
        with self._db.session() as session:
            categories = CategoryRepository(session)
            sounds = SoundRepository(session)
            counts = categories.counts()
            entries = [
                CategoryEntry(
                    key=SCOPE_ALL,
                    name="My Sounds",
                    count=sounds.total(),
                    scope="all",
                    category_id=None,
                    is_system=True,
                ),
                CategoryEntry(
                    key=SCOPE_UNCATEGORIZED,
                    name="Uncategorized",
                    count=sounds.uncategorized_total(),
                    scope="uncategorized",
                    category_id=None,
                    is_system=True,
                ),
            ]
            for category in categories.list_all():
                entries.append(
                    CategoryEntry(
                        key=str(category.id),
                        name=category.name,
                        count=counts.get(category.id, 0),
                        scope="category",
                        category_id=category.id,
                        is_system=False,
                    )
                )
            return entries

    def sounds_for(self, entry: CategoryEntry) -> list[SoundRecord]:
        with self._db.session() as session:
            return SoundRepository(session).list(entry.category_id, entry.scope)

    def get_sound(self, sound_id: int) -> SoundRecord | None:
        with self._db.session() as session:
            return SoundRepository(session).get(sound_id)

    def play_count_for(self, entry: CategoryEntry) -> int:
        with self._db.session() as session:
            return SoundRepository(session).total_play_count(
                entry.category_id, entry.scope
            )

    def register_play(self, sound_id: int) -> None:
        with self._db.session() as session:
            SoundRepository(session).increment_play_count(sound_id)

    def add_category(self, name: str) -> None:
        with self._db.session() as session:
            CategoryRepository(session).add(name)

    def rename_sound(self, sound_id: int, new_name: str) -> None:
        with self._db.session() as session:
            SoundRepository(session).rename(sound_id, new_name)

    def add_sound_record(
        self,
        name: str,
        file_path: str,
        duration_ms: int = 0,
        category_id: int | None = None,
    ) -> SoundRecord:
        with self._db.session() as session:
            return SoundRepository(session).add(
                name, file_path, duration_ms, category_id
            )

    def import_files(
        self, sources: list[Path], category_id: int | None = None
    ) -> ImportSummary:
        if self._importer is None:
            raise RuntimeError("La importación requiere un directorio de sonidos")
        result: ImportResult = self._importer.prepare(sources)
        with self._db.session() as session:
            repo = SoundRepository(session)
            for prepared in result.imported:
                repo.add(
                    prepared.name,
                    str(prepared.stored_path),
                    prepared.duration_ms,
                    category_id,
                )
        return ImportSummary(imported=len(result.imported), skipped=result.skipped)

    def remove_sounds(self, sound_ids: list[int]) -> None:
        with self._db.session() as session:
            paths = SoundRepository(session).delete_many(sound_ids)
        for raw in paths:
            try:
                Path(raw).unlink(missing_ok=True)
            except OSError:
                logger.exception("No se pudo borrar el archivo %s", raw)
