import threading
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Voice:
    voice_id: int
    sound_id: int
    data: np.ndarray
    volume: float
    position: int = 0

    @property
    def frames(self) -> int:
        return self.data.shape[0]


@dataclass(frozen=True)
class MixerSnapshot:
    active_sound_ids: tuple[int, ...]
    primary_sound_id: int | None
    primary_position_frames: int
    primary_total_frames: int
    paused: bool
    finished_sound_ids: tuple[int, ...]


@dataclass
class _State:
    voices: list[Voice] = field(default_factory=list)
    finished: list[int] = field(default_factory=list)
    primary_voice_id: int | None = None
    paused: bool = False
    next_voice_id: int = 1


class Mixer:
    def __init__(self, sample_rate: int = 48000, master_volume: float = 1.0) -> None:
        self.sample_rate = sample_rate
        self._master_volume = float(master_volume)
        self._lock = threading.Lock()
        self._state = _State()
        self.clipped_blocks = 0

    @property
    def master_volume(self) -> float:
        return self._master_volume

    def set_master_volume(self, value: float) -> None:
        self._master_volume = float(min(max(value, 0.0), 1.0))

    def play(self, sound_id: int, data: np.ndarray, volume: float = 1.0) -> int:
        if data.ndim != 2 or data.shape[1] != 2:
            raise ValueError("El audio debe ser estéreo con forma (frames, 2)")
        if data.dtype != np.float32:
            data = data.astype(np.float32)
        with self._lock:
            voice = Voice(
                voice_id=self._state.next_voice_id,
                sound_id=sound_id,
                data=data,
                volume=float(min(max(volume, 0.0), 2.0)),
            )
            self._state.next_voice_id += 1
            self._state.voices.append(voice)
            self._state.primary_voice_id = voice.voice_id
            self._state.paused = False
            return voice.voice_id

    def stop_all(self) -> None:
        with self._lock:
            self._state.voices.clear()
            self._state.primary_voice_id = None
            self._state.paused = False

    def stop_sound(self, sound_id: int) -> None:
        with self._lock:
            self._state.voices = [v for v in self._state.voices if v.sound_id != sound_id]
            self._refresh_primary()

    def pause(self) -> None:
        with self._lock:
            if self._state.voices:
                self._state.paused = True

    def resume(self) -> None:
        with self._lock:
            self._state.paused = False

    def toggle_pause(self) -> bool:
        with self._lock:
            if self._state.voices:
                self._state.paused = not self._state.paused
            return self._state.paused

    def seek_primary(self, fraction: float) -> None:
        with self._lock:
            voice = self._primary_voice()
            if voice is not None:
                voice.position = int(min(max(fraction, 0.0), 1.0) * (voice.frames - 1))

    def render(self, frames: int) -> np.ndarray:
        out = np.zeros((frames, 2), dtype=np.float32)
        with self._lock:
            if self._state.paused or not self._state.voices:
                return out
            remaining: list[Voice] = []
            for voice in self._state.voices:
                end = min(voice.position + frames, voice.frames)
                chunk = voice.data[voice.position:end]
                count = chunk.shape[0]
                if count:
                    out[:count] += chunk * voice.volume
                voice.position = end
                if voice.position >= voice.frames:
                    self._state.finished.append(voice.sound_id)
                else:
                    remaining.append(voice)
            self._state.voices = remaining
            self._refresh_primary()
        out *= self._master_volume
        peak = float(np.max(np.abs(out))) if out.size else 0.0
        if peak > 1.0:
            self.clipped_blocks += 1
            np.tanh(out, out=out)
        return out

    def snapshot(self) -> MixerSnapshot:
        with self._lock:
            voice = self._primary_voice()
            finished = tuple(self._state.finished)
            self._state.finished.clear()
            return MixerSnapshot(
                active_sound_ids=tuple(v.sound_id for v in self._state.voices),
                primary_sound_id=None if voice is None else voice.sound_id,
                primary_position_frames=0 if voice is None else voice.position,
                primary_total_frames=0 if voice is None else voice.frames,
                paused=self._state.paused,
                finished_sound_ids=finished,
            )

    def _primary_voice(self) -> Voice | None:
        for voice in self._state.voices:
            if voice.voice_id == self._state.primary_voice_id:
                return voice
        return None

    def _refresh_primary(self) -> None:
        if self._primary_voice() is None:
            self._state.primary_voice_id = (
                self._state.voices[-1].voice_id if self._state.voices else None
            )
            if not self._state.voices:
                self._state.paused = False
