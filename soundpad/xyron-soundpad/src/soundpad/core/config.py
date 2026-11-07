import json
import logging
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

SUPPORTED_SAMPLE_RATES = (44100, 48000)


class AudioSettings(BaseModel):
    sample_rate: int = 48000
    buffer_size: int = Field(default=512, ge=64, le=8192)
    master_volume: float = Field(default=1.0, ge=0.0, le=1.0)
    mic_volume: float = Field(default=1.0, ge=0.0, le=1.0)
    microphone_device: str | None = None
    virtual_output_device: str | None = None
    headphones_device: str | None = None
    output_mode: str = "both"

    def model_post_init(self, __context) -> None:
        if self.sample_rate not in SUPPORTED_SAMPLE_RATES:
            raise ValueError(f"Frecuencia de muestreo no soportada: {self.sample_rate}")
        if self.output_mode not in ("headphones", "microphone", "both"):
            raise ValueError(f"Modo de salida inválido: {self.output_mode}")


class UiSettings(BaseModel):
    theme: str = "dark"
    start_minimized: bool = False
    minimize_to_tray: bool = False
    window_width: int = Field(default=1100, ge=640)
    window_height: int = Field(default=680, ge=420)
    sidebar_width: int = Field(default=200, ge=120)
    last_category: str = "all"


class AppSettings(BaseModel):
    audio: AudioSettings = Field(default_factory=AudioSettings)
    ui: UiSettings = Field(default_factory=UiSettings)


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self.settings = AppSettings()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> AppSettings:
        if not self._path.exists():
            self.settings = AppSettings()
            return self.settings
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self.settings = AppSettings.model_validate(raw)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            backup = self._path.with_suffix(".corrupt.json")
            logger.error("Configuración inválida (%s). Se respalda en %s", exc, backup)
            try:
                os.replace(self._path, backup)
            except OSError:
                logger.exception("No se pudo respaldar la configuración dañada")
            self.settings = AppSettings()
        return self.settings

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.settings.model_dump_json(indent=2)
        fd, tmp_name = tempfile.mkstemp(
            dir=self._path.parent, prefix=".settings-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_name, self._path)
        except OSError:
            logger.exception("No se pudo guardar la configuración")
            Path(tmp_name).unlink(missing_ok=True)
            raise
