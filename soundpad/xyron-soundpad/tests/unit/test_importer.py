import numpy as np
import soundfile as sf

from soundpad.services.library_service import LibraryService
from soundpad.soundboard.importer import SoundImporter


def make_wav(path, seconds=0.25, rate=48000):
    frames = int(seconds * rate)
    sf.write(str(path), np.zeros(frames, dtype=np.float32), rate)
    return path


def test_import_copies_files_and_reads_duration(tmp_path):
    (tmp_path / "src").mkdir()
    source = make_wav(tmp_path / "src" / "boom.wav")
    importer = SoundImporter(tmp_path / "library")
    result = importer.prepare([source])
    assert len(result.imported) == 1
    prepared = result.imported[0]
    assert prepared.name == "boom"
    assert prepared.duration_ms == 250
    assert prepared.stored_path.exists()
    assert source.exists()


def test_import_avoids_name_collisions(tmp_path):
    (tmp_path / "src").mkdir()
    source = make_wav(tmp_path / "src" / "boom.wav")
    importer = SoundImporter(tmp_path / "library")
    first = importer.prepare([source]).imported[0].stored_path
    second = importer.prepare([source]).imported[0].stored_path
    assert first != second
    assert first.exists() and second.exists()


def test_import_skips_unsupported_and_corrupt(tmp_path):
    (tmp_path / "src").mkdir()
    text = tmp_path / "src" / "notes.txt"
    text.write_text("hi")
    corrupt = tmp_path / "src" / "broken.mp3"
    corrupt.write_bytes(b"\x00" * 64)
    result = SoundImporter(tmp_path / "library").prepare([text, corrupt, tmp_path / "missing.wav"])
    assert result.imported == []
    assert len(result.skipped) == 3


def test_import_folder_recursively(tmp_path):
    folder = tmp_path / "pack" / "nested"
    folder.mkdir(parents=True)
    make_wav(folder / "a.wav")
    make_wav(tmp_path / "pack" / "b.wav")
    result = SoundImporter(tmp_path / "library").prepare([tmp_path / "pack"])
    assert len(result.imported) == 2


def test_library_import_persists_records(database, tmp_path):
    (tmp_path / "src").mkdir()
    source = make_wav(tmp_path / "src" / "ding.wav")
    library = LibraryService(database, tmp_path / "library")
    library.initialize()
    games = next(e for e in library.category_entries() if e.name == "Games")
    summary = library.import_files([source], games.category_id)
    assert summary.imported == 1
    entries = {e.name: e for e in library.category_entries()}
    assert entries["Games"].count == 1
    assert library.sounds_for(entries["Games"])[0].duration_ms == 250


def test_remove_sounds_deletes_record_and_file(database, tmp_path):
    (tmp_path / "src").mkdir()
    source = make_wav(tmp_path / "src" / "gone.wav")
    library = LibraryService(database, tmp_path / "library")
    library.initialize()
    library.import_files([source])
    entry = library.category_entries()[0]
    record = library.sounds_for(entry)[0]
    stored = tmp_path / "library" / "gone.wav"
    assert stored.exists()
    library.remove_sounds([record.id])
    assert library.sounds_for(library.category_entries()[0]) == []
    assert not stored.exists()


def test_register_play_increments_counter(library):
    record = library.add_sound_record("x", "x.wav", 10)
    library.register_play(record.id)
    library.register_play(record.id)
    entry = library.category_entries()[0]
    assert library.play_count_for(entry) == 2
