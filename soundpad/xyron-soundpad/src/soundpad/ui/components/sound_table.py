from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView

from soundpad.ui.viewmodels.sound_table_model import (
    COLUMN_DURATION,
    COLUMN_HOTKEY,
    COLUMN_INDEX,
    COLUMN_NAME,
    SOUND_ID_ROLE,
)


class SoundTable(QTableView):
    files_dropped = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
        )
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.setWordWrap(False)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(24)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(False)

    def setModel(self, model) -> None:
        super().setModel(model)
        header = self.horizontalHeader()
        header.setSectionResizeMode(COLUMN_INDEX, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(COLUMN_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COLUMN_DURATION, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(COLUMN_HOTKEY, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(COLUMN_INDEX, 48)
        self.setColumnWidth(COLUMN_DURATION, 90)
        self.setColumnWidth(COLUMN_HOTKEY, 140)
        self.sortByColumn(COLUMN_INDEX, Qt.SortOrder.AscendingOrder)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths:
            event.acceptProposedAction()
            self.files_dropped.emit(paths)
        else:
            event.ignore()

    def selected_sound_ids(self) -> list[int]:
        model = self.model()
        rows = {index.row() for index in self.selectionModel().selectedRows()}
        return [model.index(row, 0).data(SOUND_ID_ROLE) for row in sorted(rows)]
