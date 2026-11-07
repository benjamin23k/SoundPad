import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PySide6.QtWidgets import QApplication

from soundpad.app import build_main_window
from soundpad.core.paths import AppPaths
from soundpad.ui.theme.theme import apply_theme


def main(output: Path) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app)
    with tempfile.TemporaryDirectory() as tmp:
        paths = AppPaths.resolve(data_dir=Path(tmp))
        window, database = build_main_window(paths)
        library = window._library
        entries = {e.name: e for e in library.category_entries()}
        samples = [
            ("Airhorn", 1800, "Memes"),
            ("Bruh", 900, "Memes"),
            ("Vine boom", 1400, "Memes"),
            ("Victory fanfare", 4200, "Games"),
            ("Level up", 2100, "Games"),
            ("Nani", 1100, "Anime"),
            ("Sad violin", 6500, "Music"),
            ("Door knock", 700, None),
        ]
        for name, duration, category in samples:
            cid = entries[category].category_id if category else None
            library.add_sound_record(name, f"{name}.wav", duration, cid)
        window.refresh_categories(select_key="all")
        window.resize(1100, 640)
        window.show()
        app.processEvents()
        window.grab().save(str(output))
        database.dispose()


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("preview.png"))
