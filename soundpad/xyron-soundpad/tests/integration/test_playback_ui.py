import numpy as np
import pytest
import soundfile as sf
from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import QDropEvent

from soundpad.audio.mixer import Mixer
from soundpad.database.session import Database
from soundpad.services.library_service import LibraryService
from soundpad.services.playback_service import PlaybackService
from soundpad.ui.theme.theme import apply_theme
from soundpad.ui.viewmodels.sound_table_model import COLUMN_NAME
from soundpad.ui.views.main_window import MainWindow


class FakeEngine:
    def __init__(self):
        self.started = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False


def make_wav(path, seconds=0.5, rate=48000):
    frames = int(seconds * rate)
    t = np.arange(frames) / rate
    sf.write(str(path), (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), rate)
    return str(path)


@pytest.fixture
def env(qtbot, tmp_path, settings_store):
    apply_theme(qtbot._request.getfixturevalue("qapp"))
    database = Database(None)
    library = LibraryService(database, tmp_path / "library")
    library.initialize()
    mixer = Mixer()
    playback = PlaybackService(mixer, FakeEngine())
    assert playback.start()
    window = MainWindow(library, settings_store, playback)
    qtbot.addWidget(window)
    window.show()
    sources = tmp_path / "src"
    sources.mkdir()
    files = [
        make_wav(sources / "alpha.wav", 0.5),
        make_wav(sources / "bravo.wav", 0.25),
        make_wav(sources / "charlie.wav", 0.75),
    ]
    yield window, playback, mixer, library, files
    playback.shutdown()
    database.dispose()


def test_import_adds_rows_with_duration(env):
    window, _playback, _mixer, _library, files = env
    window.import_paths(files)
    assert window.proxy.rowCount() == 3
    assert window.categories.item(0).text() == "My Sounds  (3)"
    assert window.stats.value("sounds") == "3"
    durations = sorted(window.proxy.index(r, 2).data() for r in range(3))
    assert durations == ["0:00.2", "0:00.5", "0:00.7"]


def test_import_into_selected_category(env):
    window, _p, _m, library, files = env
    window.categories.select_key(
        next(e.key for e in library.category_entries() if e.name == "Memes")
    )
    window.import_paths(files[:2])
    entries = {e.name: e for e in library.category_entries()}
    assert entries["Memes"].count == 2
    assert entries["Uncategorized"].count == 0


def test_drop_event_imports_files(env):
    window, _p, _m, _l, files = env
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(f) for f in files])
    event = QDropEvent(
        QPointF(10, 10),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    window.table.dropEvent(event)
    assert window.proxy.rowCount() == 3


def test_controls_enabled_when_engine_present(env):
    window, *_ = env
    assert window.act_play.isEnabled()
    assert window.toolbar.action_play.isEnabled()
    assert window.engine_state.text() == "Audio engine: running"


def test_play_selected_starts_voice_and_counts_play(env):
    window, playback, mixer, _l, files = env
    window.import_paths(files)
    window.table.selectRow(0)
    window.play_selected()
    assert len(mixer.snapshot().active_sound_ids) == 1
    assert playback.state == "playing"
    assert window.playback_state.text() == "Playing"
    assert window.stats.value("plays") == "1"


def test_multiple_sounds_play_simultaneously_and_stop_all(env):
    window, playback, mixer, _l, files = env
    window.import_paths(files)
    window.table.selectAll()
    window.play_selected()
    assert len(mixer.snapshot().active_sound_ids) == 3
    audible = mixer.render(480)
    assert float(np.abs(audible).max()) > 0
    window.stop_all()
    assert mixer.snapshot().active_sound_ids == ()
    assert not mixer.render(480).any()
    assert window.playback_state.text() == "Stopped"


def test_sound_finishes_and_state_returns_to_stopped(env):
    window, playback, mixer, _l, files = env
    window.import_paths(files[1:2])
    window.table.selectRow(0)
    window.play_selected()
    mixer.render(48000)
    playback.poll()
    assert playback.state == "stopped"
    assert window.playback_state.text() == "Stopped"


def test_pause_and_resume(env):
    window, playback, mixer, _l, files = env
    window.import_paths(files[:1])
    window.table.selectRow(0)
    window.play_selected()
    mixer.render(1000)
    window.toggle_pause()
    assert playback.state == "paused"
    assert not mixer.render(1000).any()
    window.play_selected()
    assert playback.state == "playing"
    assert mixer.render(1000).any()


def test_next_and_previous_wrap_around(env):
    window, playback, mixer, _l, files = env
    window.import_paths(files)
    window.table.sortByColumn(COLUMN_NAME, Qt.SortOrder.AscendingOrder)
    window.table.selectRow(0)
    window.play_next()
    first = playback.current_sound_id
    window.stop_all()
    window.table.selectRow(2)
    window.play_next()
    wrapped = playback.current_sound_id
    assert first != wrapped
    assert window.proxy.index(0, COLUMN_NAME).data() == "alpha"
    window.stop_all()
    window.table.selectRow(0)
    window.play_previous()
    assert window.proxy.index(2, COLUMN_NAME).data() == "charlie"
    assert playback.current_sound_id is not None


def test_double_click_plays_row(env, qtbot):
    window, playback, mixer, _l, files = env
    window.import_paths(files)
    window._on_double_clicked(window.proxy.index(1, 0))
    assert len(mixer.snapshot().active_sound_ids) == 1


def test_volume_slider_updates_mixer_and_settings(env):
    window, _p, mixer, _l, _f = env
    window.toolbar.volume.setValue(40)
    assert mixer.master_volume == pytest.approx(0.4)
    assert window._settings.settings.audio.master_volume == pytest.approx(0.4)


def test_remove_deletes_record_and_file(env, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    window, _p, _m, library, files = env
    window.import_paths(files)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    window.table.selectRow(0)
    window._remove_selected()
    assert window.proxy.rowCount() == 2


def test_playing_without_engine_reports_message(qtbot, library, settings_store, tmp_path):
    apply_theme(qtbot._request.getfixturevalue("qapp"))
    library.add_sound_record("x", str(tmp_path / "x.wav"), 100)
    window = MainWindow(library, settings_store, PlaybackService(Mixer(), None))
    qtbot.addWidget(window)
    window.show()
    window.refresh_categories()
    assert not window.act_play.isEnabled()
    window.play_record(window._record_at_proxy_row(0))
    assert "no está disponible" in window.statusBar().currentMessage()
