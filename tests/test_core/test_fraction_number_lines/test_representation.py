"""
Tests for what a fractions on a number line question shows: its question and answer key entry as
written maths, the unit after its answer line, its choices as written maths, and its tile
question.

The stories are taken from the end of the bank, where tests' stories stay as new ones go on at
the top: the bike ride from home (last), the hike at camp (fourth from last) and the frog (eighth
from last).
"""

import pytest

from core.drawn_objects import DrawnObject
from core.fraction_models.number_lines import FractionLine, LengthUnit, LinePicture, LinePoint, Mark
from core.fraction_number_lines.data import (
    LESS,
    Compared,
    CompareQuestionData,
    Comparison,
    DistanceAsked,
    DistanceQuestionData,
    DivideQuestionData,
    FractionNumberLinesQuestionData,
    MarkPointQuestionData,
    NamePointQuestionData,
)
from core.fraction_number_lines.representation import (
    TileAnswer,
    answer_unit,
    comparison_pieces,
    fraction_number_lines_tile_question,
    question,
    solution,
    tile_answer,
)
from core.fraction_number_lines.stories import DISTANCE_STORIES
from core.self_check_tiles import TileQuestion
from core.written_numbers import FractionStyle, Pieces, UnreducedFraction

MARK_IT, HOW_FAR = DistanceAsked
FARTHER, SHORTER, MORE_OR_LESS = Compared
BIKE, CAMP, FROG = (len(DISTANCE_STORIES) - offset for offset in (1, 4, 8))
MILE, METER = LengthUnit.MILE, LengthUnit.METER
THREE_QUARTERS = UnreducedFraction(3, 4)
THREE_EIGHTHS = UnreducedFraction(3, 8, FractionStyle.SLASH)
FIVE_EIGHTHS = UnreducedFraction(5, 8, FractionStyle.SLASH)
FIVE_SIXTHS = NamePointQuestionData(
    FractionLine(6, points=(LinePoint(5),)), UnreducedFraction(5, 6)
)
MARK_THREE_EIGHTHS = MarkPointQuestionData(
    THREE_EIGHTHS, FractionLine(8), FractionLine(8, points=(LinePoint(3),))
)
JAVIER_HOW_FAR = DistanceQuestionData(
    BIKE,
    "Javier",
    MILE,
    HOW_FAR,
    THREE_QUARTERS,
    FractionLine(
        4,
        unit=MILE,
        points=(LinePoint(3, "J"),),
        arrow_to=3,
        pictures=(LinePicture(0, DrawnObject.HOUSE),),
    ),
    THREE_QUARTERS,
)
JAVIER_MARK = DistanceQuestionData(
    BIKE,
    "Javier",
    MILE,
    MARK_IT,
    THREE_QUARTERS,
    FractionLine(4, unit=MILE, pictures=(LinePicture(0, DrawnObject.HOUSE),)),
    THREE_QUARTERS,
)
ANA_FROG = DistanceQuestionData(
    FROG,
    "Ana",
    METER,
    HOW_FAR,
    THREE_QUARTERS,
    FractionLine(
        4,
        unit=METER,
        points=(LinePoint(3, "A"),),
        jumps=3,
        pictures=(LinePicture(3, DrawnObject.FROG),),
    ),
    THREE_QUARTERS,
)
ANA_CAMP = DistanceQuestionData(
    CAMP,
    "Ana",
    MILE,
    MARK_IT,
    THREE_QUARTERS,
    FractionLine(4, unit=MILE, pictures=(LinePicture(0, DrawnObject.TENT),)),
    THREE_QUARTERS,
)
DIVIDE_SIXTHS = DivideQuestionData(
    UnreducedFraction(4, 6), FractionLine(1), FractionLine(6, points=(LinePoint(4),))
)


def _compare(story: int, compared: Compared, answer: str) -> CompareQuestionData:
    """Return a story of Ana going 3/8 and Ben 5/8 of a mile or meter, on a line of eighths."""
    unit = MILE if story == BIKE else METER
    return CompareQuestionData(
        story,
        ("Ana", "Ben"),
        unit,
        (THREE_EIGHTHS, FIVE_EIGHTHS),
        compared,
        FractionLine(8, unit=unit),
        answer,
    )


@pytest.mark.parametrize(
    ("data", "choices", "tiles", "expected"),
    [
        (FIVE_SIXTHS, False, False, ("What fraction does the point show?",)),
        (
            NamePointQuestionData(
                FractionLine(4, points=(LinePoint(3, mark=Mark.STAR),)), THREE_QUARTERS
            ),
            True,
            False,
            ("What fraction does the star show?",),
        ),
        (
            MARK_THREE_EIGHTHS,
            False,
            False,
            ("Mark and label ", THREE_EIGHTHS, " on the number line."),
        ),
        (MARK_THREE_EIGHTHS, True, False, ("Which point shows ", THREE_EIGHTHS, "?")),
        (
            MARK_THREE_EIGHTHS,
            False,
            True,
            ("Find the number line with a point at ", THREE_EIGHTHS, "."),
        ),
        (
            JAVIER_HOW_FAR,
            False,
            False,
            ("Point J shows where Javier stopped. How far from home did Javier ride?",),
        ),
        (
            # a thing of the person's, from nowhere in particular
            ANA_FROG,
            False,
            True,
            ("Point A shows where Ana's frog landed. How far did Ana's frog jump?",),
        ),
        (
            JAVIER_MARK,
            False,
            False,
            (
                "Javier rode a bike ",
                THREE_QUARTERS,
                " mile from home. Mark point J to show where Javier stopped.",
            ),
        ),
        (
            JAVIER_MARK,
            True,
            False,
            (
                "Javier rode a bike ",
                THREE_QUARTERS,
                " mile from home. Which number line shows where Javier stopped?",
            ),
        ),
        (
            # a scene before the story
            ANA_CAMP,
            False,
            False,
            (
                "At camp, Ana hiked ",
                THREE_QUARTERS,
                " mile from the tent. Mark point A to show where Ana stopped.",
            ),
        ),
        (
            DIVIDE_SIXTHS,
            False,
            False,
            ("Divide the number line into sixths. Mark and label ", UnreducedFraction(4, 6), "."),
        ),
        (
            DIVIDE_SIXTHS,
            True,
            False,
            (
                "Which number line is divided into sixths with ",
                UnreducedFraction(4, 6),
                " marked?",
            ),
        ),
        (
            # past twelfths, a number of equal parts
            DivideQuestionData(
                UnreducedFraction(5, 13), FractionLine(1), FractionLine(13, points=(LinePoint(5),))
            ),
            False,
            False,
            (
                "Divide the number line into 13 equal parts. Mark and label ",
                UnreducedFraction(5, 13),
                ".",
            ),
        ),
        (
            _compare(BIKE, FARTHER, "Ben"),
            False,
            False,
            (
                "Ana rode a bike ",
                THREE_EIGHTHS,
                " mile from home, and Ben rode ",
                FIVE_EIGHTHS,
                " mile. Mark point A for Ana and point B for Ben. Who rode farther?",
            ),
        ),
        (
            _compare(BIKE, MORE_OR_LESS, LESS),
            True,
            False,
            (
                "Ana rode a bike ",
                THREE_EIGHTHS,
                " mile from home, and Ben rode ",
                FIVE_EIGHTHS,
                " mile. Mark point A for Ana and point B for Ben. Did Ana ride more or less than "
                "Ben?",
            ),
        ),
        (
            _compare(FROG, SHORTER, "Ana"),
            False,
            True,
            (
                "Ana's frog jumped ",
                THREE_EIGHTHS,
                " meter, and Ben's jumped ",
                FIVE_EIGHTHS,
                " meter. Mark point A for Ana and point B for Ben. Whose frog jumped a shorter "
                "distance?",
            ),
        ),
        (
            _compare(FROG, MORE_OR_LESS, LESS),
            False,
            False,
            (
                "Ana's frog jumped ",
                THREE_EIGHTHS,
                " meter, and Ben's jumped ",
                FIVE_EIGHTHS,
                " meter. Mark point A for Ana and point B for Ben. Did Ana's frog jump more or "
                "less than Ben's?",
            ),
        ),
    ],
)
def test_question(
    data: FractionNumberLinesQuestionData, choices: bool, tiles: bool, expected: Pieces
) -> None:
    assert question(data, choices, tiles) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (FIVE_SIXTHS, (UnreducedFraction(5, 6), ": 5 of the 6 equal parts from 0")),
        (MARK_THREE_EIGHTHS, (THREE_EIGHTHS, ": 3 of the 8 equal parts from 0")),
        (JAVIER_HOW_FAR, (THREE_QUARTERS, " mile: point J is 3 of the 4 equal parts from 0")),
        (JAVIER_MARK, ("Point J at ", THREE_QUARTERS, ": 3 of the 4 equal parts from 0")),
        (
            # 3/4 mile on a line of eighths
            DistanceQuestionData(
                BIKE,
                "Javier",
                MILE,
                MARK_IT,
                THREE_QUARTERS,
                FractionLine(8, unit=MILE),
                UnreducedFraction(6, 8),
            ),
            (
                "Point J at ",
                UnreducedFraction(6, 8),
                ": 6 of the 8 equal parts from 0, which is ",
                THREE_QUARTERS,
                " mile",
            ),
        ),
        (DIVIDE_SIXTHS, ("6 equal parts; ", UnreducedFraction(4, 6), " is 4 of them from 0")),
        # from the answer's side: the answer's distance first
        (_compare(BIKE, FARTHER, "Ben"), ("Ben: ", FIVE_EIGHTHS, " > ", THREE_EIGHTHS)),
        (_compare(FROG, SHORTER, "Ana"), ("Ana: ", THREE_EIGHTHS, " < ", FIVE_EIGHTHS)),
        # the first person's first
        (_compare(BIKE, MORE_OR_LESS, LESS), ("less: ", THREE_EIGHTHS, " < ", FIVE_EIGHTHS)),
    ],
)
def test_solution(data: FractionNumberLinesQuestionData, expected: Pieces) -> None:
    assert solution(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (JAVIER_HOW_FAR, "mile"),
        (ANA_FROG, "meter"),
        (JAVIER_MARK, None),  # marked on the line
        (FIVE_SIXTHS, None),
    ],
)
def test_answer_unit(data: FractionNumberLinesQuestionData, expected: str | None) -> None:
    assert answer_unit(data) == expected


def test_comparison_pieces() -> None:
    """A comparison is its word, then the comparison: "Ben, 5/8 > 3/8"."""
    assert comparison_pieces(Comparison("Ben", FIVE_EIGHTHS, ">", THREE_EIGHTHS)) == (
        "Ben, ",
        FIVE_EIGHTHS,
        " > ",
        THREE_EIGHTHS,
    )


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            FIVE_SIXTHS,
            TileQuestion(
                "What fraction does the point show?",
                (UnreducedFraction(5, 6),),
                "5/6: 5 of the 6 equal parts from 0",
            ),
        ),
        (
            # a line in the bank
            MARK_THREE_EIGHTHS,
            TileQuestion(
                "Find the number line with a point at 3/8.",
                FractionLine(8, points=(LinePoint(3),)),
                "3/8: 3 of the 8 equal parts from 0",
            ),
        ),
        (
            # the fraction without its unit
            JAVIER_HOW_FAR,
            TileQuestion(
                "Point J shows where Javier stopped. How far from home did Javier ride?",
                (THREE_QUARTERS,),
                "3/4 mile: point J is 3 of the 4 equal parts from 0",
            ),
        ),
        (
            _compare(FROG, SHORTER, "Ana"),
            TileQuestion(
                "Ana's frog jumped 3/8 meter, and Ben's jumped 5/8 meter. Mark point A for Ana and "
                "point B for Ben. Whose frog jumped a shorter distance?",
                ("Ana",),
                "Ana: 3/8 < 5/8",
            ),
        ),
    ],
)
def test_fraction_number_lines_tile_question(
    data: FractionNumberLinesQuestionData, expected: TileQuestion[TileAnswer]
) -> None:
    assert fraction_number_lines_tile_question(data) == expected


def test_a_line_to_divide_has_no_tile_answer() -> None:
    """Dividing a line has many right answers, so none for a tile."""
    with pytest.raises(ValueError) as error:
        tile_answer(DIVIDE_SIXTHS)
    assert str(error.value) == "A line to divide has no single answer for a tile."
