from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)

from soundpad.database.repositories import SoundRecord
from soundpad.utils.formatting import format_duration

COLUMN_INDEX = 0
COLUMN_NAME = 1
COLUMN_DURATION = 2
COLUMN_HOTKEY = 3
HEADERS = ("#", "Tag / Name", "Duration", "Hotkey")

SORT_ROLE = Qt.ItemDataRole.UserRole + 1
SOUND_ID_ROLE = Qt.ItemDataRole.UserRole + 2
PLAYING_ROLE = Qt.ItemDataRole.UserRole + 3


class SoundTableModel(QAbstractTableModel):
    rename_requested = Signal(int, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[SoundRecord] = []
        self._playing_id: int | None = None

    def set_records(self, records: list[SoundRecord]) -> None:
        self.beginResetModel()
        self._rows = list(records)
        self.endResetModel()

    def record_at(self, row: int) -> SoundRecord:
        return self._rows[row]

    def set_playing(self, sound_id: int | None) -> None:
        previous = self._playing_id
        self._playing_id = sound_id
        for target in (previous, sound_id):
            if target is None:
                continue
            for row, record in enumerate(self._rows):
                if record.id == target:
                    self.dataChanged.emit(
                        self.index(row, 0),
                        self.index(row, len(HEADERS) - 1),
                        [Qt.ItemDataRole.DisplayRole, PLAYING_ROLE],
                    )

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return HEADERS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        record = self._rows[index.row()]
        column = index.column()
        if role == SOUND_ID_ROLE:
            return record.id
        if role == PLAYING_ROLE:
            return record.id == self._playing_id
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if column == COLUMN_INDEX:
                return index.row() + 1
            if column == COLUMN_NAME:
                return record.name
            if column == COLUMN_DURATION:
                return format_duration(record.duration_ms)
            if column == COLUMN_HOTKEY:
                return record.hotkey or ""
        if role == SORT_ROLE:
            if column == COLUMN_INDEX:
                return index.row()
            if column == COLUMN_NAME:
                return record.name.casefold()
            if column == COLUMN_DURATION:
                return record.duration_ms
            if column == COLUMN_HOTKEY:
                return (record.hotkey or "").casefold()
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column in (COLUMN_INDEX, COLUMN_DURATION):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.ItemDataRole.FontRole and record.id == self._playing_id:
            font = QFont()
            font.setBold(True)
            return font
        if role == Qt.ItemDataRole.ForegroundRole and record.id == self._playing_id:
            return QColor("#4a92e6")
        return None

    def flags(self, index):
        base = super().flags(index)
        if not index.isValid():
            return base
        flags = base | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if index.column() == COLUMN_NAME:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.EditRole or index.column() != COLUMN_NAME:
            return False
        clean = str(value).strip()
        if not clean:
            return False
        record = self._rows[index.row()]
        if clean == record.name:
            return False
        self._rows[index.row()] = SoundRecord(
            id=record.id,
            name=clean,
            file_path=record.file_path,
            duration_ms=record.duration_ms,
            category_id=record.category_id,
            hotkey=record.hotkey,
            volume=record.volume,
            play_count=record.play_count,
            favorite=record.favorite,
        )
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
        self.rename_requested.emit(record.id, clean)
        return True


class SoundFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._needle = ""
        self.setSortRole(SORT_ROLE)
        self.setDynamicSortFilter(True)

    def set_search(self, text: str) -> None:
        self.beginFilterChange()
        self._needle = text.strip().casefold()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        if not self._needle:
            return True
        model = self.sourceModel()
        record = model.record_at(source_row)
        haystack = f"{record.name} {record.hotkey or ''}".casefold()
        return self._needle in haystack
