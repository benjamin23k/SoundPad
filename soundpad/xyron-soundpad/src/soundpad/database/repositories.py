from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from soundpad.database.models import Category, Sound

DEFAULT_CATEGORIES = ("Memes", "Games", "Anime", "Music")


@dataclass(frozen=True)
class SoundRecord:
    id: int
    name: str
    file_path: str
    duration_ms: int
    category_id: int | None
    hotkey: str | None
    volume: float
    play_count: int
    favorite: bool


def _to_record(sound: Sound) -> SoundRecord:
    return SoundRecord(
        id=sound.id,
        name=sound.name,
        file_path=sound.file_path,
        duration_ms=sound.duration_ms,
        category_id=sound.category_id,
        hotkey=sound.hotkey,
        volume=sound.volume,
        play_count=sound.play_count,
        favorite=sound.favorite,
    )


class CategoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def ensure_defaults(self) -> None:
        existing = set(self._session.scalars(select(Category.name)))
        for order, name in enumerate(DEFAULT_CATEGORIES):
            if name not in existing:
                self._session.add(Category(name=name, sort_order=order))
        self._session.flush()

    def list_all(self) -> list[Category]:
        stmt = select(Category).order_by(Category.sort_order, Category.name)
        return list(self._session.scalars(stmt))

    def counts(self) -> dict[int, int]:
        stmt = (
            select(Sound.category_id, func.count(Sound.id))
            .where(Sound.category_id.is_not(None))
            .group_by(Sound.category_id)
        )
        return {cid: total for cid, total in self._session.execute(stmt)}

    def add(self, name: str) -> Category:
        clean = name.strip()
        if not clean:
            raise ValueError("El nombre de la categoría no puede estar vacío")
        exists = self._session.scalar(select(Category.id).where(Category.name == clean))
        if exists is not None:
            raise ValueError(f"La categoría '{clean}' ya existe")
        next_order = (self._session.scalar(select(func.max(Category.sort_order))) or 0) + 1
        category = Category(name=clean, sort_order=next_order)
        self._session.add(category)
        self._session.flush()
        return category


class SoundRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        name: str,
        file_path: str,
        duration_ms: int = 0,
        category_id: int | None = None,
    ) -> SoundRecord:
        sound = Sound(
            name=name,
            file_path=file_path,
            duration_ms=duration_ms,
            category_id=category_id,
        )
        self._session.add(sound)
        self._session.flush()
        return _to_record(sound)

    def total(self) -> int:
        return self._session.scalar(select(func.count(Sound.id))) or 0

    def uncategorized_total(self) -> int:
        stmt = select(func.count(Sound.id)).where(Sound.category_id.is_(None))
        return self._session.scalar(stmt) or 0

    def total_play_count(self, category_id: int | None, scope: str) -> int:
        stmt = select(func.coalesce(func.sum(Sound.play_count), 0))
        stmt = self._apply_scope(stmt, category_id, scope)
        return int(self._session.scalar(stmt) or 0)

    def list(self, category_id: int | None, scope: str) -> list[SoundRecord]:
        stmt = select(Sound).order_by(Sound.id)
        stmt = self._apply_scope(stmt, category_id, scope)
        return [_to_record(sound) for sound in self._session.scalars(stmt)]

    def get(self, sound_id: int) -> SoundRecord | None:
        sound = self._session.get(Sound, sound_id)
        return None if sound is None else _to_record(sound)

    def increment_play_count(self, sound_id: int) -> None:
        sound = self._session.get(Sound, sound_id)
        if sound is not None:
            sound.play_count += 1
            self._session.flush()

    def delete_many(self, sound_ids: list[int]) -> list[str]:
        paths: list[str] = []
        for sound_id in sound_ids:
            sound = self._session.get(Sound, sound_id)
            if sound is not None:
                paths.append(sound.file_path)
                self._session.delete(sound)
        self._session.flush()
        return paths

    def rename(self, sound_id: int, new_name: str) -> None:
        clean = new_name.strip()
        if not clean:
            raise ValueError("El nombre del sonido no puede estar vacío")
        sound = self._session.get(Sound, sound_id)
        if sound is None:
            raise LookupError(f"Sonido {sound_id} no encontrado")
        sound.name = clean
        self._session.flush()

    @staticmethod
    def _apply_scope(stmt, category_id: int | None, scope: str):
        if scope == "all":
            return stmt
        if scope == "uncategorized":
            return stmt.where(Sound.category_id.is_(None))
        if scope == "category":
            return stmt.where(Sound.category_id == category_id)
        raise ValueError(f"Ámbito desconocido: {scope}")
