import os
from dataclasses import dataclass
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class AppPaths:
    root: Path
    data_dir: Path
    sounds_dir: Path
    profiles_dir: Path
    database_dir: Path
    logs_dir: Path
    settings_file: Path
    database_file: Path
    assets_dir: Path

    @classmethod
    def resolve(cls, data_dir: Path | None = None) -> "AppPaths":
        root = project_root()
        env_dir = os.environ.get("XYRON_DATA_DIR")
        base = data_dir or (Path(env_dir) if env_dir else root / "data")
        return cls(
            root=root,
            data_dir=base,
            sounds_dir=base / "sounds",
            profiles_dir=base / "profiles",
            database_dir=base / "database",
            logs_dir=base / "logs",
            settings_file=base / "settings.json",
            database_file=base / "database" / "soundpad.db",
            assets_dir=root / "assets",
        )

    def ensure(self) -> None:
        for directory in (
            self.data_dir,
            self.sounds_dir,
            self.profiles_dir,
            self.database_dir,
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
