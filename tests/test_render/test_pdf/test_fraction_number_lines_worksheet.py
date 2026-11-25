"""
Tests for the fractions on a number line worksheet PDFs, rendered from hand-built questions.

The question generator is not used: each question is built by hand with its response.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/fraction_number_lines_worksheet_pdf_expecteds.txt``. The text includes every question
with its fractions in their styles, the number lines with their points, distances and pictures,
two column problems side by side and wide ones alone, the lettered choices in rows, the lettered
points on a line, the lettered lines one under another, the answer lines with their units, the
answer bank with its small lines, the pattern, the answer key and the page breaks. To regenerate
sections after an intended change, uncomment the ``write_section`` lines in
``test_pdf_draws_the_expected_text`` and run it (``-k`` selects cases).
"""

from collections.abc import Sequence
from fractions import Fraction

import pytest

from core.drawn_objects import DrawnObject
from core.fraction_models.number_lines import FractionLine, LengthUnit, LinePicture, LinePoint, Mark
from core.fraction_number_lines.data import (
    LESS,
    MORE,
    NONE_OF_THESE,
    Compared,
    CompareQuestionData,
    Comparison,
    DistanceAsked,
    DistanceQuestionData,
    DivideQuestionData,
    FractionNumberLinesQuestion,
    MarkPointQuestionData,
    NamePointQuestionData,
)
from core.fraction_number_lines.stories import DISTANCE_STORIES
from core.question import FreeResponse, MultipleChoice, Question
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.helpers import GOLDENS, pdf_text, read_sections, render_fraction_number_lines

EXPECTED = GOLDENS / "fraction_number_lines_worksheet_pdf_expecteds.txt"
STACKED, SLASH, SLANTED = FractionStyle
MARK_IT, HOW_FAR = DistanceAsked
FARTHER, SHORTER, MORE_OR_LESS = Compared
BIKE, ANT, FROG = (len(DISTANCE_STORIES) - offset for offset in (1, 6, 8))  # from the end
MILE, YARD, METER = LengthUnit.MILE, LengthUnit.YARD, LengthUnit.METER
FROM_HOME = (LinePicture(0, DrawnObject.HOUSE),)
ANT_HOUSE = (LinePicture(0, DrawnObject.HOUSE),)


def _f(numerator: int, denominator: int, style: FractionStyle = STACKED) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator, style)


def _point_at(parts: int, tick: int) -> FractionLine:
    """Return a line of ``parts`` parts with a dot on tick ``tick``."""
    return FractionLine(parts, points=(LinePoint(tick),))


def _ant_line(parts: int, tick: int) -> FractionLine:
    """Return the ant story's line in yards: point A on tick ``tick``, an arrow from 0, its house
    at 0 and the ant over the point."""
    return FractionLine(
        parts,
        unit=YARD,
        points=(LinePoint(tick, "A"),),
        arrow_to=tick,
        pictures=(*ANT_HOUSE, LinePicture(tick, DrawnObject.ANT)),
    )


NAME_SIXTHS = NamePointQuestionData(_point_at(6, 5), _f(5, 6))
NAME_STAR = NamePointQuestionData(
    FractionLine(4, points=(LinePoint(3, mark=Mark.STAR),)), _f(3, 4, SLASH)
)
MARK_EIGHTHS = MarkPointQuestionData(_f(3, 8, SLANTED), FractionLine(8), _point_at(8, 3))
MARK_THIRDS = MarkPointQuestionData(_f(1, 3), FractionLine(3), _point_at(3, 1))
JAVIER_HOW_FAR = DistanceQuestionData(
    BIKE,
    "Javier",
    MILE,
    HOW_FAR,
    _f(3, 4),
    FractionLine(4, unit=MILE, points=(LinePoint(3, "J", Mark.STAR),), jumps=3, pictures=FROM_HOME),
    _f(3, 4),
)
ANA_ANT = DistanceQuestionData(
    ANT, "Ana", YARD, MARK_IT, _f(2, 8), FractionLine(8, unit=YARD, pictures=ANT_HOUSE), _f(2, 8)
)
DIVIDE_FOURTHS = DivideQuestionData(_f(3, 4), FractionLine(1), _point_at(4, 3))
FROGS = CompareQuestionData(
    FROG,
    ("Ana", "Ben"),
    METER,
    (_f(3, 8), _f(5, 8)),
    FARTHER,
    FractionLine(8, unit=METER),
    "Ben",
)
WRITTEN: list[FractionNumberLinesQuestion] = [
    Question(NAME_SIXTHS, FreeResponse()),
    Question(MARK_EIGHTHS, FreeResponse()),
    Question(JAVIER_HOW_FAR, FreeResponse()),
    Question(ANA_ANT, FreeResponse()),
    Question(DIVIDE_FOURTHS, FreeResponse()),
    Question(FROGS, FreeResponse()),
    Question(NAME_STAR, FreeResponse()),  # a column problem alone, at the end
]
CHOICES: list[FractionNumberLinesQuestion] = [
    Question(
        NAME_SIXTHS,
        # "None of these" right: two choices to a row
        MultipleChoice((_f(1, 5), _f(1, 6), _f(5, 7), NONE_OF_THESE), frozenset({3})),
    ),
    Question(
        MARK_THIRDS,
        # lettered on the line: where 1/4 and 1/2 would be, between the ticks, and 2/3; then
        # "None of these" as the fourth letter
        MultipleChoice(
            (Fraction(1, 4), Fraction(1, 3), Fraction(1, 2), NONE_OF_THESE), frozenset({1})
        ),
    ),
    Question(
        MARK_EIGHTHS,
        MultipleChoice(
            (Fraction(2, 8), Fraction(5, 8), Fraction(3, 8), Fraction(1, 8)), frozenset({2})
        ),
    ),
    Question(
        ANA_ANT,
        MultipleChoice(
            (_ant_line(4, 2), _ant_line(8, 2), _ant_line(8, 1), _ant_line(10, 2)),
            frozenset({1}),
        ),
    ),
    Question(
        DIVIDE_FOURTHS,
        MultipleChoice(
            (
                _point_at(3, 3),
                FractionLine(
                    4,
                    points=(LinePoint(3),),
                    sizes=(Fraction(1, 6), Fraction(1, 3), Fraction(2, 9), Fraction(5, 18)),
                ),
                _point_at(4, 3),
                _point_at(5, 3),
            ),
            frozenset({2}),
        ),
    ),
    Question(
        FROGS,
        MultipleChoice(
            (
                Comparison("Ana", _f(3, 8), "<", _f(5, 8)),
                Comparison("Ben", _f(5, 8), ">", _f(3, 8)),
                Comparison("Ana", _f(3, 8), ">", _f(5, 8)),
                Comparison("Ben", _f(5, 8), "<", _f(3, 8)),
            ),
            frozenset({1}),
        ),
    ),
]
TILES: list[FractionNumberLinesQuestion] = [
    Question(NAME_SIXTHS, FreeResponse()),
    Question(MARK_EIGHTHS, FreeResponse()),  # a small line in the bank
    Question(JAVIER_HOW_FAR, FreeResponse()),  # 3/4 without its unit
    Question(
        CompareQuestionData(
            BIKE,
            ("Cy", "Dot"),
            MILE,
            (_f(1, 4), _f(3, 4)),
            MORE_OR_LESS,
            FractionLine(4, unit=MILE, pictures=FROM_HOME),
            LESS,
        ),
        FreeResponse(),
    ),
    Question(
        CompareQuestionData(
            BIKE,
            ("Eve", "Fay"),
            MILE,
            (_f(3, 4), _f(2, 4)),
            MORE_OR_LESS,
            FractionLine(4, unit=MILE, pictures=FROM_HOME),
            MORE,
        ),
        FreeResponse(),
    ),
]


@pytest.mark.parametrize(
    ("case_name", "questions", "slot_of", "answer_key", "black_and_white", "title", "label"),
    [
        ("written", WRITTEN, None, True, False, "Fractions on a Number Line", "Sheet A"),
        (
            "choices_black_and_white",
            CHOICES,
            None,
            True,
            True,
            "Fractions on a Number Line",
            "Sheet A",
        ),
        ("tiles", TILES, (0, 1, 6, 7, 2), True, False, "Fractions on a Number Line", "Sheet A"),
        ("other_title_and_label", WRITTEN[:2], None, False, False, "Number Lines", "Day 2"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: Sequence[FractionNumberLinesQuestion],
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    black_and_white: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of
    ``fraction_number_lines_worksheet_pdf_expecteds.txt``.

    One comparison covers each problem's question, its number line, its lettered choices, points
    or lines, its answer line and unit, the rows of problems and their page breaks, the answer
    bank and pattern, the answer key with each problem's fractions in their style, the marks'
    colour, and the title and label.
    """
    actual = pdf_text(
        render_fraction_number_lines(
            questions, slot_of, answer_key, title, label, black_and_white=black_and_white
        )
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
