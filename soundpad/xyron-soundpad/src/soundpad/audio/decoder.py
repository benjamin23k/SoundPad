from pathlib import Path

import numpy as np
import soundfile as sf

SUPPORTED_EXTENSIONS = (".wav", ".mp3", ".ogg", ".flac")


class AudioDecodeError(Exception):
    pass


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def load_audio(path: Path, target_rate: int = 48000) -> np.ndarray:
    try:
        data, rate = sf.read(str(path), dtype="float32", always_2d=True)
    except (sf.LibsndfileError, RuntimeError, OSError) as exc:
        raise AudioDecodeError(f"No se pudo decodificar {path.name}: {exc}") from exc
    if data.shape[0] == 0:
        raise AudioDecodeError(f"{path.name} no contiene audio")
    data = _to_stereo(data)
    if rate != target_rate:
        data = _resample(data, rate, target_rate)
    return np.ascontiguousarray(data, dtype=np.float32)


def read_duration_ms(path: Path) -> int:
    try:
        info = sf.info(str(path))
        if info.samplerate > 0 and info.frames > 0:
            return int(info.frames * 1000 / info.samplerate)
    except (sf.LibsndfileError, RuntimeError, OSError):
        pass
    try:
        from mutagen import File as MutagenFile

        meta = MutagenFile(str(path))
        if meta is not None and meta.info is not None:
            return int(meta.info.length * 1000)
    except Exception as exc:
        raise AudioDecodeError(f"No se pudo leer la duración de {path.name}: {exc}") from exc
    raise AudioDecodeError(f"No se pudo leer la duración de {path.name}")


def _to_stereo(data: np.ndarray) -> np.ndarray:
    channels = data.shape[1]
    if channels == 1:
        return np.repeat(data, 2, axis=1)
    if channels == 2:
        return data
    return data[:, :2]


def _resample(data: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    frames = data.shape[0]
    target_frames = max(1, int(round(frames * target_rate / source_rate)))
    source_positions = np.arange(frames, dtype=np.float64)
    target_positions = np.linspace(0, frames - 1, target_frames)
    out = np.empty((target_frames, data.shape[1]), dtype=np.float32)
    for channel in range(data.shape[1]):
        out[:, channel] = np.interp(target_positions, source_positions, data[:, channel])
    return out
