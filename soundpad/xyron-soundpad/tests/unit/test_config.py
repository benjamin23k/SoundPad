import json

import pytest
from pydantic import ValidationError

from soundpad.core.config import AppSettings, AudioSettings, SettingsStore


def test_defaults_match_spec():
    settings = AppSettings()
    assert settings.audio.sample_rate == 48000
    assert settings.ui.theme == "dark"
    assert settings.audio.output_mode == "both"


def test_roundtrip_persists_values(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    store.load()
    store.settings.audio.master_volume = 0.4
    store.settings.ui.last_category = "3"
    store.save()

    reloaded = SettingsStore(path)
    reloaded.load()
    assert reloaded.settings.audio.master_volume == pytest.approx(0.4)
    assert reloaded.settings.ui.last_category == "3"


def test_corrupt_file_is_backed_up_and_defaults_used(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    store = SettingsStore(path)
    settings = store.load()
    assert settings == AppSettings()
    assert (tmp_path / "settings.corrupt.json").exists()


def test_invalid_values_are_rejected_on_load(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"audio": {"sample_rate": 12345}}), encoding="utf-8")
    store = SettingsStore(path)
    assert store.load() == AppSettings()
    assert (tmp_path / "settings.corrupt.json").exists()


def test_out_of_range_volume_raises():
    with pytest.raises(ValidationError):
        AudioSettings(master_volume=1.5)


def test_invalid_output_mode_raises():
    with pytest.raises(ValueError):
        AudioSettings(output_mode="speakers")
