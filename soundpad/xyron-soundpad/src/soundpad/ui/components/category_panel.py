from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from soundpad.services.library_service import CategoryEntry


class CategoryPanel(QListWidget):
    entry_selected = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._entries: dict[str, CategoryEntry] = {}
        self.setUniformItemSizes(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.currentItemChanged.connect(self._on_current_changed)

    def set_entries(self, entries: list[CategoryEntry], select_key: str | None = None) -> None:
        current = select_key or self.current_key()
        self.blockSignals(True)
        self.clear()
        self._entries = {entry.key: entry for entry in entries}
        for entry in entries:
            item = QListWidgetItem(f"{entry.name}  ({entry.count})")
            item.setData(Qt.ItemDataRole.UserRole, entry.key)
            self.addItem(item)
        self.blockSignals(False)
        self.select_key(current if current in self._entries else entries[0].key)

    def current_key(self) -> str | None:
        item = self.currentItem()
        return None if item is None else item.data(Qt.ItemDataRole.UserRole)

    def current_entry(self) -> CategoryEntry | None:
        key = self.current_key()
        return None if key is None else self._entries.get(key)

    def select_key(self, key: str) -> None:
        for row in range(self.count()):
            if self.item(row).data(Qt.ItemDataRole.UserRole) == key:
                self.setCurrentRow(row)
                return

    def _on_current_changed(self, current, _previous) -> None:
        if current is None:
            return
        entry = self._entries.get(current.data(Qt.ItemDataRole.UserRole))
        if entry is not None:
            self.entry_selected.emit(entry)
