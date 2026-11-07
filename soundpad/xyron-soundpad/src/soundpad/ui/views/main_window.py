import logging
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from soundpad import APP_NAME, __version__
from soundpad.audio.decoder import SUPPORTED_EXTENSIONS
from soundpad.core.config import SettingsStore
from soundpad.database.repositories import SoundRecord
from soundpad.services.library_service import CategoryEntry, LibraryService
from soundpad.services.playback_service import (
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_STOPPED,
    PlaybackService,
)
from soundpad.ui.components.category_panel import CategoryPanel
from soundpad.ui.components.playback_toolbar import PlaybackToolbar
from soundpad.ui.components.sound_table import SoundTable
from soundpad.ui.components.stats_panel import StatsPanel
from soundpad.ui.theme import icons
from soundpad.ui.viewmodels.sound_table_model import (
    COLUMN_NAME,
    SoundFilterProxy,
    SoundTableModel,
)

logger = logging.getLogger(__name__)

AUDIO_FILTER = "Audio files ({})".format(" ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS))


class MainWindow(QMainWindow):
    def __init__(
        self,
        library: LibraryService,
        settings: SettingsStore,
        playback: PlaybackService | None = None,
    ) -> None:
        super().__init__()
        self._library = library
        self._settings = settings
        self._playback = playback
        self._current_entry: CategoryEntry | None = None

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(icons.icon("app", size=32))
        ui = settings.settings.ui
        self.resize(ui.window_width, ui.window_height)
        self.setMinimumSize(720, 460)

        self._build_model()
        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._build_central()
        self._build_status_bar()
        self._connect_signals()
        self._apply_playback_availability()
        self.refresh_categories(select_key=ui.last_category)

    def _build_model(self) -> None:
        self.table_model = SoundTableModel(self)
        self.proxy = SoundFilterProxy(self)
        self.proxy.setSourceModel(self.table_model)

    def _build_actions(self) -> None:
        self.act_add_sounds = QAction("Add Sounds...", self)
        self.act_add_sounds.setShortcut(QKeySequence.StandardKey.Open)
        self.act_add_folder = QAction("Add Folder...", self)
        self.act_add_category = QAction("New Category...", self)
        self.act_add_category.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.act_remove = QAction("Remove from Library", self)
        self.act_remove.setShortcut(QKeySequence.StandardKey.Delete)
        self.act_exit = QAction("Exit", self)
        self.act_exit.setShortcut(QKeySequence("Alt+F4"))

        self.act_rename = QAction("Rename", self)
        self.act_rename.setShortcut(QKeySequence("F2"))
        self.act_select_all = QAction("Select All", self)
        self.act_select_all.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.act_find = QAction("Find", self)
        self.act_find.setShortcut(QKeySequence.StandardKey.Find)

        self.act_play = QAction(icons.icon("play"), "Play", self)
        self.act_play.setShortcut(QKeySequence("Return"))
        self.act_pause = QAction(icons.icon("pause"), "Pause / Resume", self)
        self.act_pause.setShortcut(QKeySequence("Space"))
        self.act_stop = QAction(icons.icon("stop"), "Stop All", self)
        self.act_stop.setShortcut(QKeySequence("Esc"))
        self.act_previous = QAction(icons.icon("previous"), "Previous", self)
        self.act_previous.setShortcut(QKeySequence("Ctrl+Left"))
        self.act_next = QAction(icons.icon("next"), "Next", self)
        self.act_next.setShortcut(QKeySequence("Ctrl+Right"))

        self.act_always_on_top = QAction("Always on Top", self)
        self.act_always_on_top.setCheckable(True)
        self.act_settings = QAction(icons.icon("settings"), "Settings", self)
        self.act_settings.setEnabled(False)

        self.act_about = QAction("About", self)

    def _build_menus(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction(self.act_add_sounds)
        file_menu.addAction(self.act_add_folder)
        file_menu.addAction(self.act_add_category)
        file_menu.addSeparator()
        file_menu.addAction(self.act_remove)
        file_menu.addSeparator()
        file_menu.addAction(self.act_exit)

        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(self.act_rename)
        edit_menu.addAction(self.act_select_all)
        edit_menu.addAction(self.act_find)

        play_menu = menu.addMenu("&Play")
        for action in (self.act_play, self.act_pause, self.act_stop):
            play_menu.addAction(action)
        play_menu.addSeparator()
        play_menu.addAction(self.act_previous)
        play_menu.addAction(self.act_next)

        window_menu = menu.addMenu("&Window")
        window_menu.addAction(self.act_always_on_top)
        window_menu.addAction(self.act_settings)

        help_menu = menu.addMenu("&Help")
        help_menu.addAction(self.act_about)

    def _build_toolbar(self) -> None:
        self.toolbar = PlaybackToolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.toolbar.action_headphones.setEnabled(False)
        self.toolbar.action_microphone.setEnabled(False)
        self.toolbar.volume.setValue(int(self._settings.settings.audio.master_volume * 100))

    def _build_central(self) -> None:
        self.categories = CategoryPanel()
        self.categories.setMinimumWidth(140)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search sounds...")
        self.search.setClearButtonEnabled(True)

        self.table = SoundTable()
        self.table.setModel(self.proxy)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(6, 6, 0, 0)
        right_layout.setSpacing(6)
        right_layout.addWidget(self.search)
        right_layout.addWidget(self.table, 1)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.categories)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setChildrenCollapsible(False)
        sidebar = self._settings.settings.ui.sidebar_width
        self.splitter.setSizes([sidebar, max(self.width() - sidebar, 400)])

        self.stats = StatsPanel()

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.splitter, 1)
        layout.addWidget(self.stats)
        self.setCentralWidget(container)

    def _build_status_bar(self) -> None:
        bar = self.statusBar()
        bar.setSizeGripEnabled(True)
        self.playback_state = QLabel("Stopped")
        self.output_mode = QLabel(f"Output: {self._settings.settings.audio.output_mode}")
        self.engine_state = QLabel("Audio engine: unavailable")
        bar.addWidget(self.playback_state)
        bar.addPermanentWidget(self.engine_state)
        bar.addPermanentWidget(self.output_mode)

    def _connect_signals(self) -> None:
        self.categories.entry_selected.connect(self._on_entry_selected)
        self.search.textChanged.connect(self._on_search_changed)
        self.table.selectionModel().selectionChanged.connect(self._update_stats)
        self.table.doubleClicked.connect(self._on_double_clicked)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.files_dropped.connect(self._on_files_dropped)
        self.table_model.rename_requested.connect(self._on_rename_requested)

        self.act_add_sounds.triggered.connect(self._add_sounds_dialog)
        self.act_add_folder.triggered.connect(self._add_folder_dialog)
        self.act_add_category.triggered.connect(self._add_category)
        self.act_remove.triggered.connect(self._remove_selected)
        self.act_exit.triggered.connect(self.close)
        self.act_rename.triggered.connect(self._rename_selected)
        self.act_select_all.triggered.connect(self.table.selectAll)
        self.act_find.triggered.connect(self._focus_search)
        self.act_always_on_top.toggled.connect(self._set_always_on_top)
        self.act_about.triggered.connect(self._show_about)

        self.act_play.triggered.connect(self.play_selected)
        self.act_pause.triggered.connect(self.toggle_pause)
        self.act_stop.triggered.connect(self.stop_all)
        self.act_previous.triggered.connect(self.play_previous)
        self.act_next.triggered.connect(self.play_next)

        self.toolbar.play_clicked.connect(self.play_selected)
        self.toolbar.pause_clicked.connect(self.toggle_pause)
        self.toolbar.stop_clicked.connect(self.stop_all)
        self.toolbar.previous_clicked.connect(self.play_previous)
        self.toolbar.next_clicked.connect(self.play_next)
        self.toolbar.seek_requested.connect(self._on_seek)
        self.toolbar.volume_changed.connect(self._on_volume_changed)

        if self._playback is not None:
            self._playback.state_changed.connect(self._on_state_changed)
            self._playback.position_changed.connect(self.toolbar.set_time)
            self._playback.sound_started.connect(self._on_sound_started)
            self._playback.sound_finished.connect(self._on_sound_finished)
            self._playback.error.connect(self._on_playback_error)

    def _apply_playback_availability(self) -> None:
        enabled = self._playback is not None and self._playback.engine_available
        for action in (
            self.act_play,
            self.act_pause,
            self.act_stop,
            self.act_previous,
            self.act_next,
            self.toolbar.action_play,
            self.toolbar.action_pause,
            self.toolbar.action_stop,
            self.toolbar.action_previous,
            self.toolbar.action_next,
        ):
            action.setEnabled(enabled)
        self.toolbar.progress.setEnabled(enabled)
        self.toolbar.volume.setEnabled(enabled)
        self.engine_state.setText(
            "Audio engine: running" if enabled else "Audio engine: unavailable"
        )
        if self._playback is not None:
            self._playback.set_master_volume(self._settings.settings.audio.master_volume)

    def refresh_categories(self, select_key: str | None = None) -> None:
        entries = self._library.category_entries()
        self.categories.set_entries(entries, select_key=select_key)
        entry = self.categories.current_entry()
        if entry is not None:
            self._load_entry(entry)

    def _on_entry_selected(self, entry: CategoryEntry) -> None:
        self._load_entry(entry)

    def _load_entry(self, entry: CategoryEntry) -> None:
        self._current_entry = entry
        self.table_model.set_records(self._library.sounds_for(entry))
        if self._playback is not None:
            self.table_model.set_playing(self._playback.current_sound_id)
        self._update_stats()

    def _on_search_changed(self, text: str) -> None:
        self.proxy.set_search(text)
        self._update_stats()

    def _update_stats(self, *_args) -> None:
        entry = self._current_entry
        if entry is None:
            self.stats.update_stats("-", 0, 0, 0)
            return
        selected = len(self.table.selectionModel().selectedRows())
        self.stats.update_stats(
            entry.name,
            self.proxy.rowCount(),
            selected,
            self._library.play_count_for(entry),
        )

    def _record_at_proxy_row(self, row: int) -> SoundRecord | None:
        if not 0 <= row < self.proxy.rowCount():
            return None
        source = self.proxy.mapToSource(self.proxy.index(row, 0))
        return self.table_model.record_at(source.row())

    def _selected_records(self) -> list[SoundRecord]:
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        records = [self._record_at_proxy_row(row) for row in rows]
        return [record for record in records if record is not None]

    def _current_proxy_row(self) -> int | None:
        if self._playback is None or self._playback.current_sound_id is None:
            selected = self.table.selectionModel().selectedRows()
            return selected[0].row() if selected else None
        for row in range(self.proxy.rowCount()):
            record = self._record_at_proxy_row(row)
            if record is not None and record.id == self._playback.current_sound_id:
                return row
        return None

    def play_record(self, record: SoundRecord) -> None:
        if self._playback is None or not self._playback.engine_available:
            self.statusBar().showMessage("El motor de audio no está disponible", 4000)
            return
        self._playback.play(record)

    def play_selected(self) -> None:
        if self._playback is None:
            return
        if self._playback.state == STATE_PAUSED:
            self._playback.resume()
            return
        for record in self._selected_records():
            self.play_record(record)

    def toggle_pause(self) -> None:
        if self._playback is not None:
            self._playback.toggle_pause()

    def stop_all(self) -> None:
        if self._playback is not None:
            self._playback.stop_all()

    def play_next(self) -> None:
        self._step(1)

    def play_previous(self) -> None:
        self._step(-1)

    def _step(self, direction: int) -> None:
        count = self.proxy.rowCount()
        if count == 0:
            return
        current = self._current_proxy_row()
        target = 0 if current is None else (current + direction) % count
        record = self._record_at_proxy_row(target)
        if record is None:
            return
        self.table.selectRow(target)
        self.play_record(record)

    def _on_double_clicked(self, index: QModelIndex) -> None:
        if index.column() == COLUMN_NAME:
            return
        record = self._record_at_proxy_row(index.row())
        if record is not None:
            self.play_record(record)

    def _on_sound_started(self, sound_id: int) -> None:
        try:
            self._library.register_play(sound_id)
        except Exception:
            logger.exception("No se pudo registrar la reproducción de %s", sound_id)
        self.table_model.set_playing(sound_id)
        self._update_stats()

    def _on_sound_finished(self, sound_id: int) -> None:
        if self._playback is None or self._playback.current_sound_id != sound_id:
            self.table_model.set_playing(None)

    def _on_state_changed(self, state: str) -> None:
        labels = {STATE_STOPPED: "Stopped", STATE_PLAYING: "Playing", STATE_PAUSED: "Paused"}
        self.playback_state.setText(labels.get(state, state))
        if state == STATE_STOPPED:
            self.table_model.set_playing(None)
            self.toolbar.set_time(0, 0)

    def _on_playback_error(self, message: str) -> None:
        self.statusBar().showMessage(message, 6000)

    def _on_seek(self, value: int) -> None:
        if self._playback is not None:
            self._playback.seek(value / 1000)

    def _on_volume_changed(self, value: int) -> None:
        volume = value / 100
        self._settings.settings.audio.master_volume = volume
        if self._playback is not None:
            self._playback.set_master_volume(volume)

    def _target_category_id(self) -> int | None:
        entry = self._current_entry
        if entry is not None and entry.scope == "category":
            return entry.category_id
        return None

    def import_paths(self, paths: list[str]) -> None:
        summary = self._library.import_files([Path(p) for p in paths], self._target_category_id())
        key = self.categories.current_key()
        self.refresh_categories(select_key=key)
        message = f"Imported {summary.imported} sound(s)"
        if summary.skipped:
            message += f", skipped {len(summary.skipped)}"
            for name, reason in summary.skipped:
                logger.warning("Omitido %s: %s", name, reason)
        self.statusBar().showMessage(message, 6000)

    def _on_files_dropped(self, paths: list[str]) -> None:
        self.import_paths(paths)

    def _add_sounds_dialog(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Add Sounds", "", AUDIO_FILTER)
        if paths:
            self.import_paths(paths)

    def _add_folder_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Add Folder")
        if folder:
            self.import_paths([folder])

    def _remove_selected(self) -> None:
        records = self._selected_records()
        if not records:
            return
        answer = QMessageBox.question(
            self,
            "Remove from Library",
            f"Remove {len(records)} sound(s) from the library? Stored copies will be deleted.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if self._playback is not None:
            self._playback.stop_all()
        self._library.remove_sounds([record.id for record in records])
        self.refresh_categories(select_key=self.categories.current_key())

    def _show_context_menu(self, position) -> None:
        index = self.table.indexAt(position)
        if index.isValid() and not self.table.selectionModel().isRowSelected(index.row()):
            self.table.selectRow(index.row())
        menu = QMenu(self)
        has_selection = bool(self.table.selectionModel().selectedRows())
        play = menu.addAction(icons.icon("play"), "Play")
        play.setEnabled(has_selection and self.act_play.isEnabled())
        play.triggered.connect(self.play_selected)
        rename = menu.addAction("Rename")
        rename.setEnabled(has_selection)
        rename.triggered.connect(self._rename_selected)
        menu.addSeparator()
        remove = menu.addAction("Remove from Library")
        remove.setEnabled(has_selection)
        remove.triggered.connect(self._remove_selected)
        menu.exec(self.table.viewport().mapToGlobal(position))

    def _on_rename_requested(self, sound_id: int, new_name: str) -> None:
        try:
            self._library.rename_sound(sound_id, new_name)
        except (ValueError, LookupError):
            logger.exception("No se pudo renombrar el sonido %s", sound_id)
            self.statusBar().showMessage("No se pudo renombrar el sonido", 4000)
            if self._current_entry is not None:
                self._load_entry(self._current_entry)

    def _rename_selected(self) -> None:
        indexes = self.table.selectionModel().selectedRows(COLUMN_NAME)
        if indexes:
            self.table.edit(indexes[0])

    def _focus_search(self) -> None:
        self.search.setFocus()
        self.search.selectAll()

    def _add_category(self) -> None:
        name, accepted = QInputDialog.getText(self, "New Category", "Category name:")
        if not accepted:
            return
        try:
            self._library.add_category(name)
        except ValueError as exc:
            QMessageBox.warning(self, "New Category", str(exc))
            return
        self.refresh_categories()

    def _set_always_on_top(self, enabled: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.show()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"{APP_NAME} {__version__}\nSoundboard con micrófono virtual para Windows.",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        ui = self._settings.settings.ui
        ui.window_width = max(self.width(), 640)
        ui.window_height = max(self.height(), 420)
        sizes = self.splitter.sizes()
        if sizes and sizes[0] >= 120:
            ui.sidebar_width = sizes[0]
        key = self.categories.current_key()
        if key:
            ui.last_category = key
        if self._playback is not None:
            self._playback.shutdown()
        try:
            self._settings.save()
        except OSError:
            logger.exception("No se pudo guardar la configuración al cerrar")
        super().closeEvent(event)
