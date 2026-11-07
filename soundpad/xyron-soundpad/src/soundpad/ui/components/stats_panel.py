from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from soundpad.ui.theme import icons


class StatsPanel(QFrame):
    settings_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("statsPanel")
        self._values: dict[str, QLabel] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(18)

        for key, caption in (
            ("category", "Category"),
            ("sounds", "Sounds"),
            ("selected", "Selected"),
            ("plays", "Play count"),
        ):
            layout.addLayout(self._pair(key, caption))
        layout.addStretch(1)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setIcon(icons.icon("settings", "#d7dade", 16))
        self.settings_button.clicked.connect(self.settings_requested)
        layout.addWidget(self.settings_button)

        self.update_stats("-", 0, 0, 0)

    def _pair(self, key: str, caption: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(5)
        label = QLabel(f"{caption}:")
        label.setObjectName("statKey")
        value = QLabel("-")
        value.setObjectName("statValue")
        self._values[key] = value
        row.addWidget(label)
        row.addWidget(value)
        return row

    def update_stats(self, category: str, sounds: int, selected: int, plays: int) -> None:
        self._values["category"].setText(category)
        self._values["sounds"].setText(str(sounds))
        self._values["selected"].setText(str(selected))
        self._values["plays"].setText(str(plays))

    def value(self, key: str) -> str:
        return self._values[key].text()
