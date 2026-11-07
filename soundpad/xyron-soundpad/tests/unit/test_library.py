import pytest

from soundpad.database.repositories import DEFAULT_CATEGORIES
from soundpad.services.library_service import LibraryService


def names(library):
    return [entry.name for entry in library.category_entries()]


def test_default_categories_seeded(library):
    assert names(library) == ["My Sounds", "Uncategorized", *DEFAULT_CATEGORIES]


def test_initialize_is_idempotent(database):
    service = LibraryService(database)
    service.initialize()
    service.initialize()
    assert names(service).count("Memes") == 1


def test_counts_per_category(library):
    entries = {e.name: e for e in library.category_entries()}
    memes_id = entries["Memes"].category_id
    library.add_sound_record("a", "a.wav", 1000, memes_id)
    library.add_sound_record("b", "b.wav", 2000, memes_id)
    library.add_sound_record("c", "c.wav", 500, None)

    refreshed = {e.name: e for e in library.category_entries()}
    assert refreshed["My Sounds"].count == 3
    assert refreshed["Uncategorized"].count == 1
    assert refreshed["Memes"].count == 2
    assert refreshed["Games"].count == 0


def test_sounds_for_scope(library):
    entries = {e.name: e for e in library.category_entries()}
    library.add_sound_record("a", "a.wav", 1000, entries["Games"].category_id)
    library.add_sound_record("b", "b.wav", 1000, None)

    assert [s.name for s in library.sounds_for(entries["Games"])] == ["a"]
    assert [s.name for s in library.sounds_for(entries["Uncategorized"])] == ["b"]
    assert len(library.sounds_for(entries["My Sounds"])) == 2


def test_add_category_and_duplicate_rejected(library):
    library.add_category("Podcasts")
    assert "Podcasts" in names(library)
    with pytest.raises(ValueError):
        library.add_category("Podcasts")
    with pytest.raises(ValueError):
        library.add_category("   ")


def test_rename_sound(library):
    record = library.add_sound_record("old", "x.wav", 100)
    library.rename_sound(record.id, "  new name ")
    entry = library.category_entries()[0]
    assert library.sounds_for(entry)[0].name == "new name"


def test_rename_rejects_empty_and_unknown(library):
    record = library.add_sound_record("old", "x.wav", 100)
    with pytest.raises(ValueError):
        library.rename_sound(record.id, " ")
    with pytest.raises(LookupError):
        library.rename_sound(9999, "name")
