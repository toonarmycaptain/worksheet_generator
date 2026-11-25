"""Tests for the objects that pictures show, and their names."""

from core.drawn_objects import OBJECT_NAMES, OTHER_NAMES, DrawnObject


def test_every_object_has_its_names() -> None:
    """Each object has its singular and plural names, for a question's wording, in order."""
    assert list(OBJECT_NAMES) == list(DrawnObject)


def test_other_names_differ_from_the_main_ones() -> None:
    """A story can call a hard candy a lolly; another name is never the main one."""
    assert all(OBJECT_NAMES[kind] not in names for kind, names in OTHER_NAMES.items())
