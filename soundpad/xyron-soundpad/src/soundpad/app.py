import logging
import sys

from PySide6.QtWidgets import QApplication

from soundpad import APP_NAME
from soundpad.audio.engine import AudioEngine
from soundpad.audio.mixer import Mixer
from soundpad.core.config import SettingsStore
from soundpad.core.logging_setup import configure_logging
from soundpad.core.paths import AppPaths
from soundpad.database.session import Database
from soundpad.services.library_service import LibraryService
from soundpad.services.playback_service import PlaybackService
from soundpad.ui.theme.theme import apply_theme
from soundpad.ui.views.main_window import MainWindow

logger = logging.getLogger(__name__)


def build_main_window(
    paths: AppPaths, engine: AudioEngine | None = None, use_real_engine: bool = False
) -> tuple[MainWindow, Database]:
    paths.ensure()
    store = SettingsStore(paths.settings_file)
    store.load()
    audio = store.settings.audio
    database = Database(paths.database_file)
    library = LibraryService(database, paths.sounds_dir)
    library.initialize()

    mixer = Mixer(audio.sample_rate, audio.master_volume)
    if engine is None and use_real_engine:
        if AudioEngine.is_available():
            engine = AudioEngine(mixer, audio.buffer_size, audio.headphones_device)
        else:
            logger.error("sounddevice no disponible: %s", AudioEngine.unavailable_reason())
    playback = PlaybackService(mixer, engine)
    if not playback.start():
        playback = PlaybackService(mixer, None)
    window = MainWindow(library, store, playback)
    return window, database


def run() -> int:
    paths = AppPaths.resolve()
    paths.ensure()
    configure_logging(paths.logs_dir)
    logger.info("Iniciando %s", APP_NAME)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    apply_theme(app)

    window, database = build_main_window(paths, use_real_engine=True)
    if window._settings.settings.ui.start_minimized:
        window.showMinimized()
    else:
        window.show()
    try:
        return app.exec()
    finally:
        database.dispose()
        logger.info("%s cerrado", APP_NAME)
