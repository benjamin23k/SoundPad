import logging

from soundpad.audio.mixer import Mixer

logger = logging.getLogger(__name__)

try:
    import sounddevice as sd
except (ImportError, OSError) as exc:
    sd = None
    _IMPORT_ERROR: str | None = str(exc)
else:
    _IMPORT_ERROR = None


class AudioEngineError(Exception):
    pass


class AudioEngine:
    def __init__(
        self,
        mixer: Mixer,
        buffer_size: int = 512,
        device: str | int | None = None,
    ) -> None:
        self._mixer = mixer
        self._buffer_size = buffer_size
        self._device = device
        self._stream = None
        self.underruns = 0
        self.callback_errors = 0

    @staticmethod
    def is_available() -> bool:
        return sd is not None

    @staticmethod
    def unavailable_reason() -> str | None:
        return _IMPORT_ERROR

    @property
    def running(self) -> bool:
        return self._stream is not None and self._stream.active

    def start(self) -> None:
        if sd is None:
            raise AudioEngineError(f"sounddevice no está disponible: {_IMPORT_ERROR}")
        if self.running:
            return
        try:
            self._stream = sd.OutputStream(
                samplerate=self._mixer.sample_rate,
                blocksize=self._buffer_size,
                channels=2,
                dtype="float32",
                device=self._device,
                callback=self._callback,
            )
            self._stream.start()
        except Exception as exc:
            self._stream = None
            raise AudioEngineError(f"No se pudo abrir la salida de audio: {exc}") from exc
        logger.info(
            "Salida de audio iniciada: %s Hz, buffer %s", self._mixer.sample_rate, self._buffer_size
        )

    def stop(self) -> None:
        stream, self._stream = self._stream, None
        if stream is None:
            return
        try:
            stream.stop()
            stream.close()
        except Exception:
            logger.exception("Error al cerrar la salida de audio")

    def _callback(self, outdata, frames, _time, status) -> None:
        if status:
            self.underruns += 1
        try:
            outdata[:] = self._mixer.render(frames)
        except Exception:
            self.callback_errors += 1
            outdata.fill(0)
