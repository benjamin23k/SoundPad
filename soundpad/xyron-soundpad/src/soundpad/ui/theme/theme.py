from dataclasses import dataclass

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


@dataclass(frozen=True)
class Palette:
    window: str = "#1e1f22"
    panel: str = "#25272b"
    panel_alt: str = "#2b2d31"
    base: str = "#1a1b1e"
    border: str = "#33363b"
    text: str = "#d7dade"
    text_dim: str = "#8b9098"
    accent: str = "#3b82d6"
    accent_hover: str = "#4a92e6"
    accent_soft: str = "#25405f"
    selection: str = "#2a4a73"
    danger: str = "#d65a5a"


DARK = Palette()


def build_stylesheet(p: Palette) -> str:
    return f"""
    QWidget {{
        background-color: {p.window};
        color: {p.text};
        font-family: "Segoe UI", "Noto Sans", "DejaVu Sans", sans-serif;
        font-size: 9pt;
    }}
    QMainWindow::separator {{ background: {p.border}; width: 1px; height: 1px; }}
    QMenuBar {{ background: {p.panel}; border-bottom: 1px solid {p.border}; padding: 1px 2px; }}
    QMenuBar::item {{ background: transparent; padding: 4px 10px; border-radius: 3px; }}
    QMenuBar::item:selected {{ background: {p.panel_alt}; }}
    QMenu {{ background: {p.panel}; border: 1px solid {p.border}; padding: 3px; }}
    QMenu::item {{ padding: 5px 24px 5px 22px; border-radius: 3px; }}
    QMenu::item:selected {{ background: {p.accent_soft}; }}
    QMenu::separator {{ height: 1px; background: {p.border}; margin: 4px 6px; }}
    QToolBar {{
        background: {p.panel};
        border: none;
        border-bottom: 1px solid {p.border};
        spacing: 4px;
        padding: 3px 6px;
    }}
    QToolBar QLabel, QStatusBar QLabel {{ background: transparent; }}
    QToolButton {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 3px;
        padding: 3px;
    }}
    QToolButton:hover {{ background: {p.panel_alt}; border-color: {p.border}; }}
    QToolButton:pressed {{ background: {p.accent_soft}; }}
    QToolButton:checked {{ background: {p.accent_soft}; border-color: {p.accent}; }}
    QToolButton:disabled {{ color: {p.text_dim}; }}
    QLineEdit {{
        background: {p.base};
        border: 1px solid {p.border};
        border-radius: 3px;
        padding: 4px 6px;
        selection-background-color: {p.selection};
    }}
    QLineEdit:focus {{ border-color: {p.accent}; }}
    QListWidget {{
        background: {p.panel};
        border: none;
        border-right: 1px solid {p.border};
        outline: none;
        padding: 2px;
    }}
    QListWidget::item {{ padding: 5px 8px; border-radius: 3px; }}
    QListWidget::item:hover {{ background: {p.panel_alt}; }}
    QListWidget::item:selected {{ background: {p.accent_soft}; color: {p.text}; }}
    QTableView {{
        background: {p.base};
        alternate-background-color: {p.window};
        border: none;
        gridline-color: {p.border};
        selection-background-color: {p.selection};
        selection-color: {p.text};
        outline: none;
    }}
    QTableView::item {{ padding: 2px 6px; border: none; }}
    QHeaderView::section {{
        background: {p.panel};
        color: {p.text_dim};
        border: none;
        border-right: 1px solid {p.border};
        border-bottom: 1px solid {p.border};
        padding: 4px 6px;
    }}
    QHeaderView::section:hover {{ color: {p.text}; }}
    QSlider::groove:horizontal {{ height: 4px; background: {p.border}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {p.accent}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {p.text};
        width: 10px; height: 10px; margin: -4px 0; border-radius: 5px;
    }}
    QSlider::handle:horizontal:hover {{ background: {p.accent_hover}; }}
    QSplitter::handle {{ background: {p.border}; }}
    QSplitter::handle:horizontal {{ width: 1px; }}
    QStatusBar {{ background: {p.panel}; border-top: 1px solid {p.border}; color: {p.text_dim}; }}
    QStatusBar::item {{ border: none; }}
    QFrame#statsPanel {{ background: {p.panel}; border-top: 1px solid {p.border}; }}
    QLabel#statValue {{ color: {p.text}; font-weight: 600; background: transparent; }}
    QLabel#statKey {{ color: {p.text_dim}; background: transparent; }}
    QLabel#timeLabel {{ font-family: "Consolas", "DejaVu Sans Mono", monospace; background: transparent; }}
    QPushButton {{
        background: {p.panel_alt};
        border: 1px solid {p.border};
        border-radius: 3px;
        padding: 4px 12px;
    }}
    QPushButton:hover {{ border-color: {p.accent}; }}
    QPushButton:pressed {{ background: {p.accent_soft}; }}
    QScrollBar:vertical {{ background: {p.base}; width: 10px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {p.border}; min-height: 24px; border-radius: 4px; margin: 1px; }}
    QScrollBar::handle:vertical:hover {{ background: {p.text_dim}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ background: {p.base}; height: 10px; margin: 0; }}
    QScrollBar::handle:horizontal {{ background: {p.border}; min-width: 24px; border-radius: 4px; margin: 1px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QToolTip {{ background: {p.panel_alt}; color: {p.text}; border: 1px solid {p.border}; padding: 3px; }}
    """


def apply_theme(app: QApplication, palette: Palette = DARK) -> None:
    app.setStyle("Fusion")
    qpalette = QPalette()
    qpalette.setColor(QPalette.ColorRole.Window, QColor(palette.window))
    qpalette.setColor(QPalette.ColorRole.WindowText, QColor(palette.text))
    qpalette.setColor(QPalette.ColorRole.Base, QColor(palette.base))
    qpalette.setColor(QPalette.ColorRole.AlternateBase, QColor(palette.window))
    qpalette.setColor(QPalette.ColorRole.Text, QColor(palette.text))
    qpalette.setColor(QPalette.ColorRole.Button, QColor(palette.panel_alt))
    qpalette.setColor(QPalette.ColorRole.ButtonText, QColor(palette.text))
    qpalette.setColor(QPalette.ColorRole.Highlight, QColor(palette.selection))
    qpalette.setColor(QPalette.ColorRole.HighlightedText, QColor(palette.text))
    qpalette.setColor(QPalette.ColorRole.ToolTipBase, QColor(palette.panel_alt))
    qpalette.setColor(QPalette.ColorRole.ToolTipText, QColor(palette.text))
    app.setPalette(qpalette)
    app.setStyleSheet(build_stylesheet(palette))
