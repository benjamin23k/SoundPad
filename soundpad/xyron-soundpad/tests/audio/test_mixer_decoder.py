import numpy as np
import pytest
import soundfile as sf

from soundpad.audio.decoder import AudioDecodeError, load_audio, read_duration_ms
from soundpad.audio.mixer import Mixer


def tone(frames, value=0.25):
    return np.full((frames, 2), value, dtype=np.float32)


def write_wav(path, seconds=0.5, rate=44100, channels=1):
    frames = int(seconds * rate)
    t = np.arange(frames) / rate
    wave = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    data = wave if channels == 1 else np.stack([wave] * channels, axis=1)
    sf.write(str(path), data, rate)
    return path


def test_decoder_converts_mono_to_stereo_and_resamples(tmp_path):
    path = write_wav(tmp_path / "a.wav", seconds=0.5, rate=44100, channels=1)
    data = load_audio(path, 48000)
    assert data.dtype == np.float32
    assert data.shape[1] == 2
    assert data.shape[0] == pytest.approx(24000, abs=2)
    assert np.allclose(data[:, 0], data[:, 1])


def test_decoder_keeps_48k_untouched(tmp_path):
    path = write_wav(tmp_path / "a.wav", seconds=0.1, rate=48000, channels=2)
    assert load_audio(path, 48000).shape[0] == 4800


def test_decoder_rejects_garbage(tmp_path):
    bad = tmp_path / "bad.wav"
    bad.write_bytes(b"not audio at all")
    with pytest.raises(AudioDecodeError):
        load_audio(bad)


def test_duration_ms(tmp_path):
    path = write_wav(tmp_path / "a.wav", seconds=1.5, rate=48000)
    assert read_duration_ms(path) == 1500


def test_single_voice_plays_and_finishes():
    mixer = Mixer()
    mixer.play(1, tone(100))
    first = mixer.render(60)
    second = mixer.render(60)
    assert np.allclose(first, 0.25)
    assert np.allclose(second[:40], 0.25)
    assert np.allclose(second[40:], 0.0)
    snap = mixer.snapshot()
    assert snap.finished_sound_ids == (1,)
    assert snap.primary_sound_id is None


def test_simultaneous_voices_are_summed():
    mixer = Mixer()
    mixer.play(1, tone(50, 0.2))
    mixer.play(2, tone(50, 0.3))
    out = mixer.render(50)
    assert np.allclose(out, 0.5)
    assert set(mixer.snapshot().finished_sound_ids) == {1, 2}


def test_per_sound_and_master_volume():
    mixer = Mixer(master_volume=0.5)
    mixer.play(1, tone(10, 0.4), volume=0.5)
    assert np.allclose(mixer.render(10), 0.1)


def test_clipping_is_prevented():
    mixer = Mixer()
    for sound_id in range(5):
        mixer.play(sound_id, tone(32, 0.9))
    out = mixer.render(32)
    assert float(np.max(np.abs(out))) <= 1.0
    assert mixer.clipped_blocks == 1


def test_stop_all_silences_and_clears():
    mixer = Mixer()
    mixer.play(1, tone(1000))
    mixer.play(2, tone(1000))
    mixer.stop_all()
    assert not mixer.render(64).any()
    assert mixer.snapshot().active_sound_ids == ()


def test_pause_freezes_position_and_resume_continues():
    mixer = Mixer()
    mixer.play(1, tone(1000))
    mixer.render(100)
    assert mixer.toggle_pause() is True
    assert not mixer.render(100).any()
    assert mixer.snapshot().primary_position_frames == 100
    assert mixer.toggle_pause() is False
    mixer.render(100)
    assert mixer.snapshot().primary_position_frames == 200


def test_seek_primary():
    mixer = Mixer()
    mixer.play(1, tone(1000))
    mixer.seek_primary(0.5)
    assert mixer.snapshot().primary_position_frames == pytest.approx(500, abs=1)


def test_rejects_non_stereo_data():
    with pytest.raises(ValueError):
        Mixer().play(1, np.zeros((10, 1), dtype=np.float32))
