"""Tests for the objects that pictures show, and their names."""

import pytest

from core.drawn_objects import OBJECT_NAMES, OTHER_NAMES, DrawnObject, ObjectUse, objects_for


def test_every_object_has_its_names() -> None:
    """Each object has its singular and plural names, for a question's wording, in order."""
    assert list(OBJECT_NAMES) == list(DrawnObject)


def test_other_names_differ_from_the_main_ones() -> None:
    """A story can call a hard candy a lolly; another name is never the main one."""
    assert all(OBJECT_NAMES[kind] not in names for kind, names in OTHER_NAMES.items())


@pytest.mark.parametrize(
    ("use", "expected"),
    [
        (
            ObjectUse.SHARING,
            (
                DrawnObject.APPLE,
                DrawnObject.BALL,
                DrawnObject.BALLOON,
                DrawnObject.BANANA,
                DrawnObject.BASEBALL,
                DrawnObject.BASKETBALL,
                DrawnObject.BLOCK,
                DrawnObject.BOOK,
                DrawnObject.BUTTON,
                DrawnObject.CANDY_BAR,
                DrawnObject.CHOCOLATE_BAR,
                DrawnObject.COOKIE,
                DrawnObject.CRAYON,
                DrawnObject.CUPCAKE,
                DrawnObject.FOOTBALL,
                DrawnObject.GIFT,
                DrawnObject.GRANOLA_BAR,
                DrawnObject.HARD_CANDY,
                DrawnObject.LOLLIPOP,
                DrawnObject.PENCIL,
                DrawnObject.TEDDY_BEAR,
                DrawnObject.TROPHY,
            ),
        ),
        (
            ObjectUse.CUTTING,
            (
                DrawnObject.CHOCOLATE_BAR,
                DrawnObject.PIZZA,
                DrawnObject.ROUND_CAKE,
                DrawnObject.SANDWICH,
                DrawnObject.SQUARE_CAKE,
            ),
        ),
    ],
)
def test_objects_for(use: ObjectUse, expected: tuple[DrawnObject, ...]) -> None:
    """Houses and animals aren't shared out; only the wholes are cut."""
    assert objects_for(use) == expected
