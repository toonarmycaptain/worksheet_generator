"""
Tests for the naming fractions worksheet PDFs, rendered from hand-built questions.

The question generator is not used: each question is built by hand with its response.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/naming_fractions_worksheet_pdf_expecteds.txt``. The text includes every question with
its fractions in their styles, the pictures, two column problems side by side and wide ones alone,
the lettered fractions and pictures, the answer lines, the answer bank with its pictures, the
pattern, the answer key and the page breaks. To regenerate sections after an intended change,
uncomment the ``write_section`` lines in ``test_pdf_draws_the_expected_text`` and run it (``-k``
selects cases).
"""

from collections.abc import Sequence

import pytest

from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    RHOMBUS,
    AreaModel,
    Circle,
    Grid,
    RadialPartition,
    Rectangle,
    RegularPolygon,
    SlicedCircle,
    Strip,
    TriangleGrid,
    equal_sizes,
    halved_by_diagonal,
    rectangle,
    striped,
    tiled,
    uneven_sizes,
)
from core.fraction_models.object_groups import ObjectGroup
from core.naming_fractions.data import (
    Asked,
    DrawSharesQuestionData,
    NameQuestionData,
    NamingFractionsQuestion,
    People,
    ShadeQuestionData,
    ShareQuestionData,
)
from core.question import FreeResponse, MultipleChoice, Question
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.helpers import GOLDENS, pdf_text, read_sections, render_naming_fractions

EXPECTED = GOLDENS / "naming_fractions_worksheet_pdf_expecteds.txt"
STACKED, SLASH, SLANTED = FractionStyle
EACH, TOGETHER, LEFT = Asked
FRIENDS = ("friend", "friends")
SHARE_EQUALLY = 7  # the last group story
ROUND_CAKE, SQUARE_CAKE, CHOCOLATE_BAR, PIZZA, WALL = 2, 3, 4, 6, 8  # whole stories
CIRCLE_IN_4 = RadialPartition(Circle(), equal_sizes(4))
UNCUT_PIZZA = AreaModel(RadialPartition(Circle(), equal_sizes(1)), look=DrawnObject.PIZZA)

NAME_CIRCLE = NameQuestionData(
    AreaModel(CIRCLE_IN_4, frozenset({0, 1, 2})), False, UnreducedFraction(3, 4)
)
NAME_COOKIES = NameQuestionData(
    ObjectGroup(DrawnObject.COOKIE, 8, 4, frozenset({0, 2, 5})),
    True,
    UnreducedFraction(5, 8, SLASH),
)
SHADE_STRIP = ShadeQuestionData(
    UnreducedFraction(2, 6, SLANTED),
    AreaModel(Strip(equal_sizes(6))),
    False,
    AreaModel(Strip(equal_sizes(6)), frozenset({0, 1})),
)
SHADE_DIVIDE = ShadeQuestionData(
    UnreducedFraction(3, 4),
    AreaModel(RadialPartition(RegularPolygon(4), equal_sizes(1))),
    True,
    AreaModel(striped(rectangle(1, 1), 4), frozenset({0, 1, 2})),
)
SHARE_BASEBALLS = ShareQuestionData(
    SHARE_EQUALLY,
    People(2, FRIENDS, ("Ana", "Ben")),
    DrawnObject.BASEBALL,
    8,
    EACH,
    1,
    ObjectGroup(DrawnObject.BASEBALL, 8, 4),
    UnreducedFraction(4, 8),
)
SHARE_WALL = ShareQuestionData(
    WALL,
    People(4, ("student", "students")),
    None,
    8,
    LEFT,
    1,
    AreaModel(Grid(2, 4)),
    UnreducedFraction(6, 8, SLASH),
)
SHARE_MANY = ShareQuestionData(  # too many cookies to draw
    SHARE_EQUALLY,
    People(4, FRIENDS, ("Eve",)),
    DrawnObject.COOKIE,
    60,
    TOGETHER,
    2,
    None,
    UnreducedFraction(30, 60),
)
DRAW_PIZZA = DrawSharesQuestionData(
    PIZZA, People(3, FRIENDS), UNCUT_PIZZA, EACH, 1, UnreducedFraction(1, 3)
)
WRITTEN = [
    Question(NAME_CIRCLE, FreeResponse()),
    Question(NAME_COOKIES, FreeResponse()),
    Question(SHARE_BASEBALLS, FreeResponse()),
    Question(SHADE_STRIP, FreeResponse()),
    Question(SHADE_DIVIDE, FreeResponse()),
    Question(SHARE_WALL, FreeResponse()),
    Question(DRAW_PIZZA, FreeResponse()),
    Question(SHARE_MANY, FreeResponse()),
    Question(NAME_CIRCLE, FreeResponse()),  # a column problem alone, at the end
]
CHOICES: list[NamingFractionsQuestion] = [
    Question(
        NAME_CIRCLE,
        MultipleChoice(
            (
                UnreducedFraction(1, 4),
                UnreducedFraction(3, 4),
                UnreducedFraction(1, 3),
                UnreducedFraction(3, 1),
            ),
            frozenset({1}),
        ),
    ),
    Question(
        SHADE_STRIP,
        MultipleChoice(
            (
                AreaModel(Strip(equal_sizes(6)), frozenset({0, 1, 2, 3})),
                AreaModel(Strip(tuple(uneven_sizes(6))), frozenset({0, 1})),
                AreaModel(Strip(equal_sizes(6)), frozenset({0, 1})),
                AreaModel(Strip(equal_sizes(8)), frozenset({0, 1})),
            ),
            frozenset({2}),
        ),
    ),
    Question(
        SHARE_BASEBALLS,
        MultipleChoice(
            (
                UnreducedFraction(2, 8),
                UnreducedFraction(4, 4),
                UnreducedFraction(4, 8),
                UnreducedFraction(4, 1),
            ),
            frozenset({2}),
        ),
    ),
    Question(
        DRAW_PIZZA,
        MultipleChoice(
            (
                UnreducedFraction(1, 2),
                UnreducedFraction(3, 1),
                UnreducedFraction(2, 3),
                UnreducedFraction(1, 3),
            ),
            frozenset({3}),
        ),
    ),
]
TILES = [
    Question(NAME_CIRCLE, FreeResponse()),
    Question(
        ShadeQuestionData(
            UnreducedFraction(2, 3),
            AreaModel(RadialPartition(Circle(), equal_sizes(3))),
            False,
            AreaModel(RadialPartition(Circle(), equal_sizes(3)), frozenset({0, 1})),
        ),
        FreeResponse(),
    ),
    Question(SHARE_BASEBALLS, FreeResponse()),
    Question(DRAW_PIZZA, FreeResponse()),
    Question(
        ShadeQuestionData(
            UnreducedFraction(5, 6, SLASH),
            ObjectGroup(DrawnObject.BALL, 6, 3),
            False,
            ObjectGroup(DrawnObject.BALL, 6, 3, frozenset(range(5))),
        ),
        FreeResponse(),
    ),
]

# Every kind of picture at its size: a rectangle cut from its centre, a sliced circle, a triangle
# grid, cut shapes on each lattice, and the wholes drawn as objects
PICTURES = [
    Question(
        NameQuestionData(
            AreaModel(RadialPartition(Rectangle(), equal_sizes(4)), frozenset({0})),
            False,
            UnreducedFraction(1, 4),
        ),
        FreeResponse(),
    ),
    Question(
        NameQuestionData(
            AreaModel(SlicedCircle(2), frozenset({1})), False, UnreducedFraction(1, 2)
        ),
        FreeResponse(),
    ),
    Question(
        NameQuestionData(
            AreaModel(TriangleGrid(2), frozenset({0, 2})), False, UnreducedFraction(2, 4)
        ),
        FreeResponse(),
    ),
    Question(
        NameQuestionData(
            AreaModel(halved_by_diagonal(RHOMBUS), frozenset({1})), False, UnreducedFraction(1, 2)
        ),
        FreeResponse(),
    ),
    Question(
        NameQuestionData(
            AreaModel(tiled(halved_by_diagonal(rectangle(1, 1)), 2, 2), frozenset({0, 3, 4})),
            False,
            UnreducedFraction(3, 8),
        ),
        FreeResponse(),
    ),
    Question(
        ShadeQuestionData(
            UnreducedFraction(2, 3),
            AreaModel(Grid(1, 1)),
            True,
            AreaModel(Grid(1, 3), frozenset({0, 1})),
        ),
        FreeResponse(),
    ),
    Question(
        DrawSharesQuestionData(
            SQUARE_CAKE,
            People(4, FRIENDS),
            AreaModel(Grid(1, 1), look=DrawnObject.SQUARE_CAKE),
            EACH,
            1,
            UnreducedFraction(1, 4),
        ),
        FreeResponse(),
    ),
    Question(
        DrawSharesQuestionData(
            CHOCOLATE_BAR,
            People(2, FRIENDS),
            AreaModel(Grid(1, 1), look=DrawnObject.CHOCOLATE_BAR),
            EACH,
            1,
            UnreducedFraction(1, 2),
        ),
        FreeResponse(),
    ),
    Question(
        DrawSharesQuestionData(
            ROUND_CAKE,
            People(6, FRIENDS),
            AreaModel(RadialPartition(Circle(), equal_sizes(1)), look=DrawnObject.ROUND_CAKE),
            TOGETHER,
            5,
            UnreducedFraction(5, 6),
        ),
        FreeResponse(),
    ),
]
# A tiles sheet of pictures to find, alone: the bank's boxes hold only pictures
PICTURE_TILES = [
    Question(
        ShadeQuestionData(
            UnreducedFraction(1, 2),
            AreaModel(Strip(equal_sizes(2))),
            False,
            AreaModel(Strip(equal_sizes(2)), frozenset({1})),
        ),
        FreeResponse(),
    ),
    Question(
        ShadeQuestionData(
            UnreducedFraction(3, 4),
            AreaModel(Grid(2, 2)),
            False,
            AreaModel(Grid(2, 2), frozenset({0, 1, 3})),
        ),
        FreeResponse(),
    ),
]


@pytest.mark.parametrize(
    ("case_name", "questions", "slot_of", "answer_key", "black_and_white", "title", "label"),
    [
        ("written", WRITTEN, None, True, False, "Naming Fractions", "Sheet A"),
        ("choices_black_and_white", CHOICES, None, True, True, "Naming Fractions", "Sheet A"),
        # a picture to shade's answer is a picture in the bank, and the boxes grow to fit it
        ("tiles", TILES, (0, 1, 6, 7, 2), True, False, "Naming Fractions", "Sheet A"),
        ("pictures", PICTURES, None, False, False, "Naming Fractions", "Sheet A"),
        ("tiles_pictures_only", PICTURE_TILES, (3, 8), False, False, "Naming Fractions", "Sheet A"),
        ("other_title_and_label", WRITTEN[:2], None, False, False, "Fractions", "Day 2"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: Sequence[NamingFractionsQuestion],
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    black_and_white: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of
    ``naming_fractions_worksheet_pdf_expecteds.txt``.

    One comparison covers each problem's question, its picture, its lettered choices, its answer
    line, the rows of problems and their page breaks, the answer bank and pattern, the answer key
    with each problem's fractions in their style, the shading's colour, and the title and label.
    """
    actual = pdf_text(
        render_naming_fractions(
            questions, slot_of, answer_key, title, label, black_and_white=black_and_white
        )
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
