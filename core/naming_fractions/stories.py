"""
The sharing stories naming fractions questions tell: people sharing a group of objects equally,
and people sharing one whole, cut into equal parts or for the student to cut.

New stories go at the top of each bank. Tests script ``random`` to take stories from the end of
a bank, so their wording stays the same.
"""

from dataclasses import dataclass

from core.drawn_objects import DrawnObject
from core.naming_fractions.data import Representation

# People a story can be about, singular and plural
FRIENDS = ("friend", "friends")
COUSINS = ("cousin", "cousins")
CLASSMATES = ("classmate", "classmates")
STUDENTS = ("student", "students")
TEAMMATES = ("teammate", "teammates")
NEIGHBORS = ("neighbor", "neighbors")


@dataclass(frozen=True)
class GroupStory:
    """
    A story of people sharing a group of objects equally. ``setup`` has slots for the people,
    ``{people}``, how many objects, ``{total}``, and their plural name, ``{objects}``; the
    people come first only at the start of a sentence. ``nouns`` are the people it suits, as
    (singular, plural).
    """

    setup: str
    nouns: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class WholeStory:
    """
    A story of people sharing one ``whole``, such as "pizza". ``setup`` has a slot for the
    people, ``{people}``, and ``cut`` for how many equal parts the whole is cut into,
    ``{total}``, when it comes cut. Each person ``verb``s a share: "What fraction of the wall
    does each student paint?" The whole is drawn as ``look``, or as a plain shape, and its
    ``representation`` is the kind of picture it is, which a sheet's choice of pictures follows.
    Every whole can come uncut, for the student to cut; one that can also come cut for sharing
    questions is ``precut``.
    """

    whole: str
    setup: str
    cut: str
    verb: str
    nouns: tuple[tuple[str, str], ...]
    representation: Representation
    look: DrawnObject | None = None
    precut: bool = True


GROUP_STORIES = (
    GroupStory("{people} put {total} {objects} into equal piles, one pile each.", (FRIENDS,)),
    GroupStory(
        "{people} find {total} {objects} in a closet and share them equally.",
        (COUSINS, FRIENDS),
    ),
    GroupStory(
        "A teacher hands out {total} {objects} to {people}, the same number to each.",
        (STUDENTS,),
    ),
    GroupStory(
        "There are {total} {objects} in a box. {people} share them equally.",
        (FRIENDS, NEIGHBORS),
    ),
    GroupStory(
        "{people} win {total} {objects} at a fair and share them equally.",
        (FRIENDS, COUSINS),
    ),
    GroupStory(
        "A coach gives {total} {objects} to {people}, the same number to each.",
        (TEAMMATES,),
    ),
    GroupStory("{total} {objects} are shared equally among {people}.", (CLASSMATES, FRIENDS)),
    GroupStory("{people} share {total} {objects} equally.", (FRIENDS, COUSINS, CLASSMATES)),
)

WHOLE_STORIES = (
    WholeStory(
        "brownies",
        "{people} share a pan of brownies equally.",
        "The brownies are cut into {total} equal pieces.",
        "get",
        (FRIENDS, COUSINS),
        Representation.GRID,
    ),
    WholeStory(
        "banner",
        "{people} color a banner, each the same amount.",
        "The banner is divided into {total} equal parts.",
        "color",
        (CLASSMATES, STUDENTS),
        Representation.STRIP,
    ),
    WholeStory(
        "cake",
        "{people} share a cake equally.",
        "",
        "get",
        (FRIENDS, COUSINS),
        Representation.CIRCLE,
        DrawnObject.ROUND_CAKE,
        precut=False,
    ),
    WholeStory(
        "cake",
        "{people} share a cake equally.",
        "The cake is cut into {total} equal pieces.",
        "get",
        (FRIENDS, COUSINS, NEIGHBORS),
        Representation.GRID,
        DrawnObject.SQUARE_CAKE,
    ),
    WholeStory(
        "chocolate bar",
        "{people} share a chocolate bar equally.",
        "The bar has {total} equal squares.",
        "get",
        (FRIENDS, COUSINS),
        Representation.GRID,
        DrawnObject.CHOCOLATE_BAR,
    ),
    WholeStory(
        "sandwich",
        "{people} share a sandwich equally.",
        "The sandwich is cut into {total} equal pieces.",
        "get",
        (FRIENDS, COUSINS),
        Representation.OTHER_SHAPE,
        DrawnObject.SANDWICH,
    ),
    WholeStory(
        "pizza",
        "{people} share a pizza equally.",
        "The pizza is cut into {total} equal slices.",
        "get",
        (FRIENDS, COUSINS, TEAMMATES),
        Representation.CIRCLE,
        DrawnObject.PIZZA,
    ),
    WholeStory(
        "garden",
        "{people} plant a garden, each the same amount.",
        "The garden is divided into {total} equal sections.",
        "plant",
        (NEIGHBORS, CLASSMATES),
        Representation.GRID,
    ),
    WholeStory(
        "wall",
        "{people} paint a wall, each the same amount.",
        "The wall is divided into {total} equal parts.",
        "paint",
        (STUDENTS, FRIENDS),
        Representation.GRID,
    ),
)
