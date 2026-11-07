import sys
from pathlib import Path

import numpy as np
import soundfile as sf

RATE = 48000

SOUNDS = {
    "beep_a4": [(440.0, 0.6)],
    "beep_e5": [(659.3, 0.6)],
    "chime": [(523.3, 0.25), (659.3, 0.25), (784.0, 0.5)],
    "siren": [(600.0, 0.4), (900.0, 0.4), (600.0, 0.4), (900.0, 0.4)],
    "low_drone": [(110.0, 2.0)],
}


def synth(notes: list[tuple[float, float]]) -> np.ndarray:
    parts = []
    for frequency, seconds in notes:
        frames = int(RATE * seconds)
        t = np.arange(frames) / RATE
        envelope = np.minimum(1.0, np.minimum(t / 0.01, (seconds - t) / 0.05))
        parts.append(0.35 * np.sin(2 * np.pi * frequency * t) * envelope)
    return np.concatenate(parts).astype(np.float32)


def main(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name, notes in SOUNDS.items():
        sf.write(str(folder / f"{name}.wav"), synth(notes), RATE)
    print(f"{len(SOUNDS)} sonidos de prueba en {folder}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("test_sounds"))
