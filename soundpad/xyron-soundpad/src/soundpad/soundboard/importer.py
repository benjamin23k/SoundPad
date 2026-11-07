import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from soundpad.audio.decoder import AudioDecodeError, is_supported, read_duration_ms

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreparedSound:
    name: str
    stored_path: Path
    duration_ms: int


@dataclass
class ImportResult:
    imported: list[PreparedSound] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)


class SoundImporter:
    def __init__(self, sounds_dir: Path) -> None:
        self._sounds_dir = sounds_dir

    def prepare(self, sources: list[Path]) -> ImportResult:
        self._sounds_dir.mkdir(parents=True, exist_ok=True)
        result = ImportResult()
        for source in self._expand(sources):
            if not source.is_file():
                result.skipped.append((source.name, "no existe"))
                continue
            if not is_supported(source):
                result.skipped.append((source.name, "formato no soportado"))
                continue
            try:
                duration = read_duration_ms(source)
            except AudioDecodeError as exc:
                logger.warning("Importación omitida: %s", exc)
                result.skipped.append((source.name, "archivo de audio ilegible"))
                continue
            target = self._unique_target(source.name)
            try:
                shutil.copy2(source, target)
            except OSError as exc:
                logger.exception("No se pudo copiar %s", source)
                result.skipped.append((source.name, f"error al copiar: {exc.strerror or exc}"))
                continue
            result.imported.append(
                PreparedSound(name=source.stem, stored_path=target, duration_ms=duration)
            )
        return result

    def _expand(self, sources: list[Path]) -> list[Path]:
        expanded: list[Path] = []
        for source in sources:
            if source.is_dir():
                expanded.extend(sorted(p for p in source.rglob("*") if p.is_file()))
            else:
                expanded.append(source)
        return expanded

    def _unique_target(self, filename: str) -> Path:
        target = self._sounds_dir / filename
        stem, suffix = target.stem, target.suffix
        counter = 1
        while target.exists():
            target = self._sounds_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        return target
