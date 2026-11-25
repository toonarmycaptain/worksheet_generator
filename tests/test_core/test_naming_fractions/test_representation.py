"""
Tests for what a naming fractions question shows: its question and answer key entry as written
maths, the names of the wholes its pictures show, and its tile question.

The stories are taken from the bank by position: the last group story, "{people} share {total}
{objects} equally.", and among the wholes the pizza (6), the round cake (2) and the wall (8).
"""

from fractions import Fraction

import pytest

from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    EQUILATERAL_TRIANGLE,
    HALF_HEXAGON,
    PARALLELOGRAM,
    REGULAR_HEXAGON,
    RHOMBUS,
    AreaModel,
    Circle,
    ConcaveOctagon,
    CutShape,
    Grid,
    Polygon,
    RadialPartition,
    Rectangle,
    RegularPolygon,
    SlicedCircle,
    Split,
    Strip,
    TriangleGrid,
    equal_sizes,
    halved_by_diagonal,
    lattice_triangles,
    quartered_by_diagonals,
    rectangle,
    striped,
)
from core.fraction_models.object_groups import ObjectGroup
from core.naming_fractions.data import (
    Asked,
    DrawSharesQuestionData,
    NameQuestionData,
    NamingFractionsQuestionData,
    People,
    ShadeQuestionData,
    ShareQuestionData,
)
from core.naming_fractions.representation import (
    TileAnswer,
    naming_fractions_tile_question,
    question,
    solution,
    whole_name,
)
from core.self_check_tiles import TileQuestion
from core.written_numbers import FractionStyle, Pieces, UnreducedFraction

EACH, TOGETHER, LEFT = Asked
FRIENDS = ("friend", "friends")
SHARE_EQUALLY = 7  # the last group story
ROUND_CAKE, PIZZA, WALL = 2, 6, 8
CIRCLE_IN_4 = RadialPartition(Circle(), equal_sizes(4))
THREE_QUARTERS = UnreducedFraction(3, 4)
THREE_EIGHTHS = UnreducedFraction(3, 8, FractionStyle.SLASH)
NOT_SHADED = NameQuestionData(
    ObjectGroup(DrawnObject.COOKIE, 4, 4, frozenset({0, 1, 2})), True, UnreducedFraction(1, 4)
)
SHADE_STRIP = ShadeQuestionData(
    THREE_EIGHTHS,
    AreaModel(Strip(equal_sizes(8))),
    False,
    AreaModel(Strip(equal_sizes(8)), frozenset({0, 1, 2})),
)
BASEBALLS = ShareQuestionData(
    SHARE_EQUALLY,
    People(4, FRIENDS),
    DrawnObject.BASEBALL,
    8,
    EACH,
    1,
    ObjectGroup(DrawnObject.BASEBALL, 8, 4),
    UnreducedFraction(2, 8),
)


@pytest.mark.parametrize(
    ("data", "choices", "tiles", "expected"),
    [
        (
            NameQuestionData(AreaModel(CIRCLE_IN_4, frozenset({0, 1, 2})), False, THREE_QUARTERS),
            False,
            False,
            ("What fraction of the circle is shaded?",),
        ),
        (NOT_SHADED, True, False, ("What fraction of the cookies are NOT shaded?",)),
        (SHADE_STRIP, False, False, ("Shade ", THREE_EIGHTHS, " of the strip.")),
        (SHADE_STRIP, True, False, ("Which model shows ", THREE_EIGHTHS, " shaded?")),
        (SHADE_STRIP, False, True, ("Find the picture that shows ", THREE_EIGHTHS, ".")),
        (
            ShadeQuestionData(
                THREE_QUARTERS,
                ObjectGroup(DrawnObject.BALL, 4, 4),
                False,
                ObjectGroup(DrawnObject.BALL, 4, 4, frozenset({0, 1, 2})),
            ),
            False,
            False,
            ("Shade ", THREE_QUARTERS, " of the balls."),
        ),
        (
            # an uncut square, divided in the answer into stripes
            ShadeQuestionData(
                THREE_QUARTERS,
                AreaModel(RadialPartition(RegularPolygon(4), equal_sizes(1))),
                True,
                AreaModel(striped(rectangle(1, 1), 4), frozenset({0, 1, 2})),
            ),
            False,
            False,
            ("Divide the square into 4 equal parts. Shade 3 of them.",),
        ),
        (
            BASEBALLS,
            False,
            False,
            (
                "Four friends share 8 baseballs equally. What fraction of the baseballs does each "
                "friend get? Circle each person's share.",
            ),
        ),
        (
            BASEBALLS,
            True,
            False,
            (
                "Four friends share 8 baseballs equally. What fraction of the baseballs does each "
                "friend get?",
            ),
        ),
        (
            BASEBALLS,
            False,
            True,
            (
                "Four friends share 8 baseballs equally. What fraction of the baseballs does each "
                "friend get?",
            ),
        ),
        (
            # too many to draw: no picture, so nothing to circle
            ShareQuestionData(
                SHARE_EQUALLY,
                People(3, FRIENDS, ("Ana", "Ben", "Cy")),
                DrawnObject.COOKIE,
                60,
                TOGETHER,
                2,
                None,
                UnreducedFraction(40, 60),
            ),
            False,
            False,
            (
                "Ana, Ben and Cy share 60 cookies equally. What fraction of the cookies do Ana and "
                "Ben get together?",
            ),
        ),
        (
            ShareQuestionData(
                SHARE_EQUALLY,
                People(4, FRIENDS, ("Eve",)),
                DrawnObject.COOKIE,
                8,
                TOGETHER,
                2,
                None,
                UnreducedFraction(4, 8),
            ),
            False,
            False,
            (
                "Eve and three friends share 8 cookies equally. What fraction of the cookies do "
                "two of them get together?",
            ),
        ),
        (
            ShareQuestionData(
                SHARE_EQUALLY,
                People(4, FRIENDS),
                DrawnObject.COOKIE,
                8,
                TOGETHER,
                3,
                None,
                UnreducedFraction(6, 8),
            ),
            False,
            False,
            (
                "Four friends share 8 cookies equally. What fraction of the cookies do three of "
                "the friends get together?",
            ),
        ),
        (
            ShareQuestionData(
                WALL,
                People(4, ("student", "students")),
                None,
                8,
                LEFT,
                1,
                AreaModel(Grid(2, 4)),
                UnreducedFraction(6, 8),
            ),
            False,
            False,
            (
                "Four students paint a wall, each the same amount. The wall is divided into 8 "
                "equal parts. One student takes a share first. What fraction of the wall is left? "
                "Circle each person's share.",
            ),
        ),
        (
            ShareQuestionData(
                WALL,
                People(2, FRIENDS, ("Ana",)),
                None,
                4,
                LEFT,
                1,
                AreaModel(Grid(2, 2)),
                UnreducedFraction(2, 4),
            ),
            True,
            False,
            (
                "Ana and one friend paint a wall, each the same amount. The wall is divided into 4 "
                "equal parts. Ana takes a share first. What fraction of the wall is left?",
            ),
        ),
        (
            DrawSharesQuestionData(
                PIZZA,
                People(2, FRIENDS, ("Ana",)),
                AreaModel(RadialPartition(Circle(), equal_sizes(1)), look=DrawnObject.PIZZA),
                EACH,
                1,
                UnreducedFraction(1, 2),
            ),
            False,
            False,
            (
                "Ana and one friend share a pizza equally. Draw lines to show the shares. What "
                "fraction of the pizza does each person get?",
            ),
        ),
        (
            DrawSharesQuestionData(
                ROUND_CAKE,
                People(6, ("cousin", "cousins")),
                AreaModel(RadialPartition(Circle(), equal_sizes(1)), look=DrawnObject.ROUND_CAKE),
                TOGETHER,
                5,
                UnreducedFraction(5, 6),
            ),
            True,
            False,
            (
                "Six cousins share a cake equally. Draw lines to show the shares. What fraction of "
                "the cake do five of the cousins get together?",
            ),
        ),
    ],
)
def test_question(
    data: NamingFractionsQuestionData, choices: bool, tiles: bool, expected: Pieces
) -> None:
    assert question(data, choices, tiles) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            NameQuestionData(AreaModel(CIRCLE_IN_4, frozenset({0, 1, 2})), False, THREE_QUARTERS),
            (THREE_QUARTERS, ": 3 of the 4 parts are shaded"),
        ),
        (NOT_SHADED, (UnreducedFraction(1, 4), ": 1 of the 4 cookies is not shaded")),
        (SHADE_STRIP, (THREE_EIGHTHS, ": any 3 of the 8 parts shaded")),
        (
            ShadeQuestionData(
                UnreducedFraction(4, 4),
                ObjectGroup(DrawnObject.BALL, 4, 4),
                False,
                ObjectGroup(DrawnObject.BALL, 4, 4, frozenset(range(4))),
            ),
            (UnreducedFraction(4, 4), ": all 4 of the 4 balls shaded"),
        ),
        (
            ShadeQuestionData(
                THREE_QUARTERS,
                AreaModel(RadialPartition(Circle(), equal_sizes(1))),
                True,
                AreaModel(CIRCLE_IN_4, frozenset({0, 1, 2})),
            ),
            (THREE_QUARTERS, ": 4 equal parts, any 3 of them shaded"),
        ),
        (BASEBALLS, (UnreducedFraction(2, 8), ": 8 baseballs shared by 4 is 2 each, 2 of the 8")),
        (
            ShareQuestionData(
                SHARE_EQUALLY,
                People(3, FRIENDS),
                DrawnObject.COOKIE,
                6,
                TOGETHER,
                2,
                None,
                UnreducedFraction(4, 6),
            ),
            (UnreducedFraction(4, 6), ": 2 each, so 2 people get 4 of the 6 cookies"),
        ),
        (
            ShareQuestionData(
                WALL,
                People(4, FRIENDS),
                None,
                8,
                LEFT,
                1,
                AreaModel(Grid(2, 4)),
                UnreducedFraction(6, 8),
            ),
            (UnreducedFraction(6, 8), ": one share is 2 of the 8 parts, leaving 6"),
        ),
        (
            DrawSharesQuestionData(
                PIZZA,
                People(3, FRIENDS),
                AreaModel(RadialPartition(Circle(), equal_sizes(1)), look=DrawnObject.PIZZA),
                EACH,
                1,
                UnreducedFraction(1, 3),
            ),
            (UnreducedFraction(1, 3), ": cut into 3 equal parts, one for each person"),
        ),
        (
            DrawSharesQuestionData(
                WALL,
                People(6, FRIENDS),
                AreaModel(Grid(1, 1)),
                TOGETHER,
                5,
                UnreducedFraction(5, 6),
            ),
            (UnreducedFraction(5, 6), ": cut into 6 equal parts; 5 people get 5 of them"),
        ),
    ],
)
def test_solution(data: NamingFractionsQuestionData, expected: Pieces) -> None:
    assert solution(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            NOT_SHADED,
            TileQuestion(
                "What fraction of the cookies are NOT shaded?",
                (UnreducedFraction(1, 4),),
                "1/4: 1 of the 4 cookies is not shaded",
            ),
        ),
        (
            # a picture in the bank
            SHADE_STRIP,
            TileQuestion(
                "Find the picture that shows 3/8.",
                AreaModel(Strip(equal_sizes(8)), frozenset({0, 1, 2})),
                "3/8: any 3 of the 8 parts shaded",
            ),
        ),
    ],
)
def test_naming_fractions_tile_question(
    data: NamingFractionsQuestionData, expected: TileQuestion[TileAnswer]
) -> None:
    assert naming_fractions_tile_question(data) == expected


@pytest.mark.parametrize(
    ("split", "expected"),
    [
        (Strip(equal_sizes(4)), "strip"),
        (Grid(2, 3), "rectangle"),
        (SlicedCircle(4), "circle"),
        (TriangleGrid(2), "triangle"),
        (CIRCLE_IN_4, "circle"),
        (RadialPartition(Rectangle(), equal_sizes(4)), "rectangle"),
        (RadialPartition(RegularPolygon(3), equal_sizes(3)), "triangle"),
        (RadialPartition(RegularPolygon(4), equal_sizes(4)), "square"),
        (RadialPartition(RegularPolygon(5), equal_sizes(5)), "pentagon"),
        (RadialPartition(RegularPolygon(6, on_corner=True), equal_sizes(6)), "hexagon"),
        (RadialPartition(RegularPolygon(8), equal_sizes(8)), "octagon"),
        (RadialPartition(RegularPolygon(7), equal_sizes(7)), "figure"),
        (RadialPartition(ConcaveOctagon(), equal_sizes(8)), "figure"),
        (halved_by_diagonal(RHOMBUS), "rhombus"),
        (quartered_by_diagonals(PARALLELOGRAM), "parallelogram"),
        (lattice_triangles(HALF_HEXAGON), "trapezoid"),
        (lattice_triangles(REGULAR_HEXAGON), "hexagon"),
        (lattice_triangles(EQUILATERAL_TRIANGLE), "triangle"),
        (striped(rectangle(1, 1), 4), "square"),
        (halved_by_diagonal(rectangle(2, 1)), "rectangle"),
        (
            # five corners
            CutShape(
                Polygon(((0, 0), (2, 0), (2, 1), (1, 2), (0, 1))),
                (((0, 0), (2, 0), (2, 1), (1, 2), (0, 1)),),
            ),
            "figure",
        ),
        (
            # four corners, not a rectangle
            CutShape(
                Polygon(((0, 0), (2, 0), (2, 1), (0, Fraction(1, 2)))),
                (((0, 0), (2, 0), (2, 1), (0, Fraction(1, 2))),),
            ),
            "figure",
        ),
    ],
)
def test_whole_name(split: Split, expected: str) -> None:
    assert whole_name(split) == expected
