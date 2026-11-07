import logging
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal

from soundpad.audio.decoder import AudioDecodeError, load_audio
from soundpad.audio.engine import AudioEngine, AudioEngineError
from soundpad.audio.mixer import Mixer
from soundpad.database.repositories import SoundRecord

logger = logging.getLogger(__name__)

STATE_STOPPED = "stopped"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"


class PlaybackService(QObject):
    state_changed = Signal(str)
    position_changed = Signal(int, int)
    sound_started = Signal(int)
    sound_finished = Signal(int)
    error = Signal(str)

    def __init__(
        self,
        mixer: Mixer,
        engine: AudioEngine | None,
        parent: QObject | None = None,
        poll_interval_ms: int = 50,
    ) -> None:
        super().__init__(parent)
        self._mixer = mixer
        self._engine = engine
        self._cache: dict[str, np.ndarray] = {}
        self._state = STATE_STOPPED
        self._current_sound_id: int | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(poll_interval_ms)
        self._timer.timeout.connect(self._poll)

    @property
    def state(self) -> str:
        return self._state

    @property
    def current_sound_id(self) -> int | None:
        return self._current_sound_id

    @property
    def sample_rate(self) -> int:
        return self._mixer.sample_rate

    @property
    def engine_available(self) -> bool:
        return self._engine is not None

    def start(self) -> bool:
        if self._engine is None:
            return False
        try:
            self._engine.start()
        except AudioEngineError as exc:
            logger.error("%s", exc)
            self.error.emit(str(exc))
            self._engine = None
            return False
        self._timer.start()
        return True

    def shutdown(self) -> None:
        self._timer.stop()
        self._mixer.stop_all()
        if self._engine is not None:
            self._engine.stop()

    def play(self, record: SoundRecord) -> bool:
        try:
            data = self._load(record.file_path)
        except AudioDecodeError as exc:
            logger.error("%s", exc)
            self.error.emit(str(exc))
            return False
        self._mixer.play(record.id, data, record.volume)
        self._current_sound_id = record.id
        self._set_state(STATE_PLAYING)
        self.sound_started.emit(record.id)
        return True

    def toggle_pause(self) -> None:
        if self._state == STATE_STOPPED:
            return
        paused = self._mixer.toggle_pause()
        self._set_state(STATE_PAUSED if paused else STATE_PLAYING)

    def resume(self) -> None:
        if self._state == STATE_PAUSED:
            self._mixer.resume()
            self._set_state(STATE_PLAYING)

    def stop_all(self) -> None:
        self._mixer.stop_all()
        self._current_sound_id = None
        self._set_state(STATE_STOPPED)
        self.position_changed.emit(0, 0)

    def seek(self, fraction: float) -> None:
        self._mixer.seek_primary(fraction)

    def set_master_volume(self, value: float) -> None:
        self._mixer.set_master_volume(value)

    def poll(self) -> None:
        self._poll()

    def _poll(self) -> None:
        snap = self._mixer.snapshot()
        for sound_id in snap.finished_sound_ids:
            self.sound_finished.emit(sound_id)
        if snap.primary_sound_id is None:
            if self._state != STATE_STOPPED:
                self._current_sound_id = None
                self._set_state(STATE_STOPPED)
                self.position_changed.emit(0, 0)
            return
        rate = self._mixer.sample_rate
        self._current_sound_id = snap.primary_sound_id
        self.position_changed.emit(
            int(snap.primary_position_frames * 1000 / rate),
            int(snap.primary_total_frames * 1000 / rate),
        )

    def _load(self, file_path: str) -> np.ndarray:
        cached = self._cache.get(file_path)
        if cached is None:
            cached = load_audio(Path(file_path), self._mixer.sample_rate)
            if len(self._cache) >= 64:
                self._cache.pop(next(iter(self._cache)))
            self._cache[file_path] = cached
        return cached

    def _set_state(self, state: str) -> None:
        if state != self._state:
            self._state = state
            self.state_changed.emit(state)
