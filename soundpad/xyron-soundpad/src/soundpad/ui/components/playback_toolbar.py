from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QSizePolicy, QSlider, QToolBar, QWidget

from soundpad.ui.theme import icons
from soundpad.utils.formatting import format_clock


class PlaybackToolbar(QToolBar):
    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    previous_clicked = Signal()
    next_clicked = Signal()
    headphones_toggled = Signal(bool)
    microphone_toggled = Signal(bool)
    seek_requested = Signal(int)
    volume_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Playback", parent)
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(20, 20))

        self.action_play = self._action("play", "Play", self.play_clicked)
        self.action_headphones = self._toggle("headphones", "Headphones (monitor)", self.headphones_toggled)
        self.action_microphone = self._toggle("microphone", "Microphone (virtual output)", self.microphone_toggled)
        self.addSeparator()
        self.action_pause = self._action("pause", "Pause", self.pause_clicked)
        self.action_stop = self._action("stop", "Stop", self.stop_clicked)
        self.action_previous = self._action("previous", "Previous", self.previous_clicked)
        self.action_next = self._action("next", "Next", self.next_clicked)
        self.addSeparator()

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setMinimumWidth(96)
        self.addWidget(self.time_label)

        self.progress = QSlider(Qt.Orientation.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.setMinimumWidth(180)
        self.progress.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.progress.sliderReleased.connect(lambda: self.seek_requested.emit(self.progress.value()))
        self.addWidget(self.progress)

        volume_icon = QLabel()
        volume_icon.setPixmap(icons.icon("volume", "#8b9098", 18).pixmap(18, 18))
        self.addWidget(volume_icon)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(100)
        self.volume.setFixedWidth(90)
        self.volume.valueChanged.connect(self.volume_changed)
        self.addWidget(self.volume)

    def _action(self, icon_name: str, text: str, signal: Signal) -> QAction:
        action = QAction(icons.icon(icon_name), text, self)
        action.setToolTip(text)
        action.triggered.connect(lambda _checked=False: signal.emit())
        self.addAction(action)
        return action

    def _toggle(self, icon_name: str, text: str, signal: Signal) -> QAction:
        action = QAction(icons.icon(icon_name), text, self)
        action.setToolTip(text)
        action.setCheckable(True)
        action.toggled.connect(signal.emit)
        self.addAction(action)
        return action

    def set_time(self, position_ms: int, duration_ms: int) -> None:
        self.time_label.setText(f"{format_clock(position_ms)} / {format_clock(duration_ms)}")
        if duration_ms > 0 and not self.progress.isSliderDown():
            self.progress.setValue(int(position_ms * 1000 / duration_ms))
        elif duration_ms <= 0:
            self.progress.setValue(0)
