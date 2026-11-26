"""
Tests for the comparing fractions worksheet PDFs, rendered from hand-built questions.

The question generator is not used: each question is built by hand with its response.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/comparing_fractions_worksheet_pdf_expecteds.txt``. The text includes every question
with its fractions in their styles, the pictures in a row (strips, grids, circles, other shapes,
groups at one object size, number lines one above another), the fraction wall, the work under
the pictures with its circles to write in, two column problems side by side and wide ones alone,
the lettered choices in rows and wrapped, the lettered pictures, the answer lines, the answer
bank, the pattern, the answer key and the page breaks. To regenerate sections after an intended
change, uncomment the ``write_section`` lines in ``test_pdf_draws_the_expected_text`` and run it
(``-k`` selects cases).
"""

from collections.abc import Sequence

import pytest

from core.comparing_fractions.data import (
    ALL_OF_THESE,
    CANT_TELL,
    MORE,
    BiggerNumber,
    CompareQuestionData,
    ComparingFractionsQuestion,
    Comparison,
    DrawAsked,
    DrawQuestionData,
    EveryQuestionData,
    ExplainForm,
    ExplainQuestionData,
    Explanation,
    GreatestQuestionData,
    LessGreaterForm,
    LessGreaterQuestionData,
    PartSize,
    PartsOf,
    Pick,
    Picture,
    SameCount,
    StoryChoice,
    StoryForm,
    StoryKind,
    StoryReason,
    Verdict,
    WordAsked,
    WordQuestionData,
)
from core.comparing_fractions.stories import GROUP_STORIES, LENGTH_STORIES, WHOLE_STORIES
from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    AreaModel,
    Circle,
    ConcaveOctagon,
    FractionWall,
    Grid,
    RadialPartition,
    RegularPolygon,
    Strip,
    equal_sizes,
)
from core.fraction_models.number_lines import FractionLine, LengthUnit, LinePoint
from core.fraction_models.object_groups import ObjectGroup
from core.question import FreeResponse, MultipleChoice, Question
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.helpers import GOLDENS, pdf_text, read_sections, render_comparing_fractions

EXPECTED = GOLDENS / "comparing_fractions_worksheet_pdf_expecteds.txt"
STACKED, SLASH, SLANTED = FractionStyle
PIZZA = len(WHOLE_STORIES) - 1
WORM = len(LENGTH_STORIES) - 1
BLOCKS = len(GROUP_STORIES) - 1
WALL = FractionWall((1, 2, 3, 4, 6, 8), labelled=False)


def _f(numerator: int, denominator: int, style: FractionStyle = STACKED) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator, style)


def _shaded(count: int) -> frozenset[int]:
    """Return the first ``count`` parts, shaded."""
    return frozenset(range(count))


def _strip(parts: int, shaded: int) -> AreaModel:
    """Return a strip of ``parts`` equal parts, the first ``shaded`` of them shaded."""
    return AreaModel(Strip(equal_sizes(parts)), _shaded(shaded))


def _circle(parts: int, shaded: int, look: DrawnObject | None = None) -> AreaModel:
    """Return a circle cut into ``parts`` equal parts, the first ``shaded`` of them shaded."""
    return AreaModel(RadialPartition(Circle(), equal_sizes(parts)), _shaded(shaded), look=look)


def _hexagon(parts: int, shaded: int) -> AreaModel:
    """Return a hexagon cut into ``parts`` equal parts, the first ``shaded`` of them shaded."""
    return AreaModel(RadialPartition(RegularPolygon(6), equal_sizes(parts)), _shaded(shaded))


def _blocks(count: int, shaded: int) -> ObjectGroup:
    """Return a group of ``count`` blocks in rows of 4, the first ``shaded`` filled in."""
    return ObjectGroup(DrawnObject.BLOCK, count, 4, _shaded(shaded))


def _word(
    kind: StoryKind,
    story: int,
    pair: tuple[UnreducedFraction, UnreducedFraction],
    answer: str,
    *,
    unit: LengthUnit | None = None,
    sizes: tuple[str, str] | None = None,
    asked: WordAsked = WordAsked.WHO,
    form: StoryForm | None = None,
    pictures: tuple[Picture, ...] = (),
    more_or_less: bool = False,
) -> WordQuestionData:
    """Return a word problem of Ana and Ben asking who has more."""
    return WordQuestionData(
        kind,
        story,
        ("Ana", "Ben"),
        pair,
        unit,
        sizes,
        True,
        more_or_less,
        asked,
        form,
        pictures,
        answer,
    )


# A written sheet: two compare questions side by side (pictured, then alone), a wall, the
# fractions to circle, a sentence under groups, a story with its lines, a model and three blanks,
# two lines to mark, the greatest of pictures on an answer line, the least of fractions, models
# to circle, fractions to write, an explanation to write, and which of two drawn is greater
WRITTEN: list[ComparingFractionsQuestion] = [
    Question(
        CompareQuestionData((_f(2, 3), _f(2, 4)), (_strip(3, 2), _strip(4, 2)), None, False, ">"),
        FreeResponse(),
    ),
    Question(
        CompareQuestionData((_f(3, 8, SLASH), _f(5, 8, SLASH)), (), None, False, "<"),
        FreeResponse(),
    ),
    Question(CompareQuestionData((_f(2, 3), _f(2, 8)), (), WALL, False, ">"), FreeResponse()),
    Question(
        EveryQuestionData(_f(3, 8), True, (_f(3, 4), _f(5, 8), _f(1, 8)), (_f(3, 4), _f(5, 8))),
        FreeResponse(),
    ),
    Question(
        ExplainQuestionData(
            (_f(3, 6), _f(3, 8)),
            (_blocks(6, 3), _blocks(8, 3)),
            None,
            False,
            ExplainForm.CIRCLE,
            Explanation(Comparison(_f(3, 6), ">", _f(3, 8)), PartSize(6, 8, larger=True)),
        ),
        FreeResponse(),
    ),
    Question(
        _word(
            StoryKind.LENGTH,
            WORM,
            (_f(1, 2, SLANTED), _f(2, 2, SLANTED)),
            "Ben",
            unit=LengthUnit.FOOT,
            asked=WordAsked.SENTENCE,
            pictures=(
                FractionLine(2, unit=LengthUnit.FOOT, bar_to=1),
                FractionLine(2, unit=LengthUnit.FOOT, bar_to=2),
            ),
        ),
        FreeResponse(),
    ),
    Question(
        LessGreaterQuestionData(
            _f(4, 6),
            False,
            LessGreaterForm.DIVIDE,
            _hexagon(6, 4),
            _hexagon(1, 0),
            (),
            (_f(1, 6), _f(2, 6), _f(4, 8)),
        ),
        FreeResponse(),
    ),
    Question(
        DrawQuestionData(
            (_f(2, 3), _f(2, 4)), (FractionLine(1), FractionLine(1)), DrawAsked.SYMBOL, ">"
        ),
        FreeResponse(),
    ),
    Question(
        GreatestQuestionData(
            (_f(2, 3), _f(2, 6), _f(2, 8)),
            True,
            (
                AreaModel(Grid(1, 3), _shaded(2)),
                AreaModel(Grid(2, 3), _shaded(2)),
                AreaModel(Grid(2, 4), _shaded(2)),
            ),
            None,
            _f(2, 3),
        ),
        FreeResponse(),
    ),
    Question(
        GreatestQuestionData((_f(5, 8), _f(1, 8), _f(7, 8), _f(3, 8)), False, (), None, _f(1, 8)),
        FreeResponse(),
    ),
    Question(
        LessGreaterQuestionData(
            _f(4, 6),
            False,
            LessGreaterForm.CIRCLE,
            _strip(6, 4),
            _strip(1, 0),
            (_strip(6, 3), _strip(6, 5), _strip(8, 4), _strip(4, 4)),
            (_f(3, 6), _f(4, 8)),
        ),
        FreeResponse(),
    ),
    Question(
        LessGreaterQuestionData(
            _f(3, 8),
            True,
            LessGreaterForm.WRITE,
            _circle(8, 3),
            _circle(1, 0),
            (),
            (_f(4, 8), _f(5, 8), _f(3, 4), _f(3, 6)),
        ),
        FreeResponse(),
    ),
    Question(
        ExplainQuestionData(
            (_f(2, 6), _f(5, 6)),
            (),
            None,
            False,
            ExplainForm.WRITE,
            Explanation(Comparison(_f(2, 6), "<", _f(5, 6)), PartsOf(_f(2, 6), _f(5, 6), False)),
        ),
        FreeResponse(),
    ),
    Question(
        DrawQuestionData(
            (_f(3, 8), _f(5, 8)), (_strip(1, 0), _strip(1, 0)), DrawAsked.GREATER, "<"
        ),
        FreeResponse(),
    ),
]

# Choices: comparisons beside pictures and in words, explanations, statements that wrap, pictures
# to choose for "Which is NOT a way?" and "Which model shows?", lettered models, groups and
# lines, fractions with All of these, two blank circles, reasons, and fractions picked
CHOICES: list[ComparingFractionsQuestion] = [
    Question(
        CompareQuestionData(
            (_f(3, 6), _f(1, 6)),
            (FractionLine(6, jumps=3), FractionLine(6, jumps=1)),
            None,
            False,
            ">",
        ),
        MultipleChoice(
            (
                Comparison(_f(1, 3), ">", _f(1, 1)),
                Comparison(_f(1, 6), "<", _f(3, 6)),
                Comparison(_f(1, 6), ">", _f(3, 6)),
                Comparison(_f(3, 6), "=", _f(1, 6)),
            ),
            frozenset({1}),
        ),
    ),
    Question(
        CompareQuestionData((_f(2, 4), _f(2, 6)), (), None, True, ">"),
        MultipleChoice(
            (
                Comparison(_f(2, 6), ">", _f(2, 4)),
                Comparison(_f(2, 3), "=", _f(2, 4)),
                Comparison(_f(2, 4), ">", _f(2, 6)),
                Comparison(_f(1, 8), "=", _f(2, 8)),
            ),
            frozenset({2}),
        ),
    ),
    Question(
        ExplainQuestionData(
            (_f(5, 6), _f(5, 8)),
            (_circle(6, 5), _circle(8, 5)),
            None,
            False,
            ExplainForm.PAIR,
            Explanation(Comparison(_f(5, 6), ">", _f(5, 8)), PartSize(6, 8, larger=True)),
        ),
        MultipleChoice(
            (
                Explanation(Comparison(_f(5, 6), ">", _f(5, 8)), PartSize(8, 6, larger=True)),
                Explanation(Comparison(_f(1, 6), ">", _f(3, 8)), PartSize(6, 8, larger=True)),
                Explanation(Comparison(_f(5, 6), ">", _f(5, 8)), PartSize(6, 8, larger=True)),
                Explanation(Comparison(_f(5, 6), "=", _f(5, 8)), SameCount(5, False, True)),
            ),
            frozenset({2}),
        ),
    ),
    Question(
        _word(
            StoryKind.WHOLE,
            PIZZA,
            (_f(1, 3), _f(1, 4)),
            "Ana",
            form=StoryForm.REASONS,
            pictures=(_circle(3, 1, DrawnObject.PIZZA), _circle(4, 1, DrawnObject.PIZZA)),
        ),
        MultipleChoice(
            (
                StoryChoice(
                    Verdict.AHEAD,
                    "Ben",
                    StoryReason.DENOMINATOR,
                    Comparison(_f(1, 4), ">", _f(1, 3)),
                ),
                StoryChoice(Verdict.CANT_TELL, None, StoryReason.NONE),
                StoryChoice(
                    Verdict.AHEAD,
                    "Ana",
                    StoryReason.PART_SIZE,
                    Comparison(_f(1, 3), ">", _f(1, 4)),
                ),
                StoryChoice(Verdict.SAME, None, StoryReason.SAME_WHOLE),
            ),
            frozenset({2}),
        ),
    ),
    Question(
        _word(
            StoryKind.GROUP,
            BLOCKS,
            (_f(3, 6), _f(3, 8)),
            "Ana",
            form=StoryForm.WHO_SYMBOL,
        ),
        MultipleChoice(
            (
                StoryChoice(
                    Verdict.AHEAD,
                    "Ana",
                    StoryReason.FRACTION,
                    Comparison(_f(3, 6), ">", _f(3, 8)),
                    True,
                ),
                StoryChoice(
                    Verdict.AHEAD,
                    "Ben",
                    StoryReason.FRACTION,
                    Comparison(_f(3, 6), ">", _f(3, 8)),
                    True,
                ),
                StoryChoice(
                    Verdict.AHEAD,
                    "Ana",
                    StoryReason.FRACTION,
                    Comparison(_f(3, 6), "<", _f(3, 8)),
                    True,
                ),
                StoryChoice(
                    Verdict.AHEAD,
                    "Ben",
                    StoryReason.FRACTION,
                    Comparison(_f(3, 6), "<", _f(3, 8)),
                    True,
                ),
            ),
            frozenset({0}),
        ),
    ),
    Question(
        LessGreaterQuestionData(
            _f(4, 6),
            False,
            LessGreaterForm.NOT_A_WAY,
            _strip(6, 4),
            _strip(1, 0),
            (),
            (_f(4, 5),),
        ),
        MultipleChoice((_strip(12, 4), _strip(6, 1), _strip(5, 4), _strip(6, 2)), frozenset({2})),
    ),
    Question(
        GreatestQuestionData(
            (_f(1, 2), _f(1, 4), _f(1, 8)),
            True,
            (
                AreaModel(RadialPartition(ConcaveOctagon(), equal_sizes(2)), _shaded(1)),
                AreaModel(RadialPartition(ConcaveOctagon(), equal_sizes(4)), _shaded(1)),
                AreaModel(RadialPartition(ConcaveOctagon(), equal_sizes(8)), _shaded(1)),
            ),
            None,
            _f(1, 2),
        ),
        MultipleChoice(
            (
                AreaModel(RadialPartition(ConcaveOctagon(), equal_sizes(2)), _shaded(1)),
                AreaModel(RadialPartition(ConcaveOctagon(), equal_sizes(4)), _shaded(1)),
                AreaModel(RadialPartition(ConcaveOctagon(), equal_sizes(8)), _shaded(1)),
            ),
            frozenset({0}),
        ),
    ),
    Question(
        GreatestQuestionData(
            (_f(1, 3), _f(1, 4), _f(1, 6)),
            False,
            (_blocks(3, 1), _blocks(4, 1), _blocks(6, 1)),
            None,
            _f(1, 6),
        ),
        MultipleChoice((_blocks(3, 1), _blocks(4, 1), _blocks(6, 1)), frozenset({2})),
    ),
    Question(
        GreatestQuestionData(
            (_f(3, 4), _f(1, 4), _f(2, 4)),
            True,
            (
                FractionLine(4, points=(LinePoint(3),)),
                FractionLine(4, points=(LinePoint(1),)),
                FractionLine(4, points=(LinePoint(2),)),
            ),
            None,
            _f(3, 4),
        ),
        MultipleChoice(
            (
                FractionLine(4, points=(LinePoint(3),)),
                FractionLine(4, points=(LinePoint(1),)),
                FractionLine(4, points=(LinePoint(2),)),
            ),
            frozenset({0}),
        ),
    ),
    Question(
        EveryQuestionData(
            _f(1, 2), False, (_f(1, 6), _f(1, 4), _f(1, 3)), (_f(1, 6), _f(1, 4), _f(1, 3))
        ),
        MultipleChoice((_f(1, 6), _f(1, 4), _f(1, 3), ALL_OF_THESE), frozenset({3})),
    ),
    Question(
        DrawQuestionData(
            (_f(2, 3), _f(2, 4)), (_circle(1, 0), _circle(1, 0)), DrawAsked.SYMBOL, ">"
        ),
        MultipleChoice(
            (
                Comparison(_f(2, 3), "<", _f(2, 4)),
                Comparison(_f(2, 4), "<", _f(2, 3)),
                Comparison(_f(2, 3), "=", _f(2, 4)),
                Comparison(_f(2, 5), ">", _f(2, 3)),
            ),
            frozenset({1}),
        ),
    ),
]

CHOICES += [
    Question(
        LessGreaterQuestionData(
            _f(2, 3),
            True,
            LessGreaterForm.SHOWS,
            AreaModel(Grid(1, 3), _shaded(2)),
            AreaModel(Grid(1, 1)),
            (),
            (_f(2, 2),),
        ),
        MultipleChoice(
            (
                AreaModel(Grid(2, 3), _shaded(2)),
                AreaModel(Grid(2, 2), _shaded(2)),
                AreaModel(Grid(1, 3), _shaded(1)),
                AreaModel(Grid(2, 4), _shaded(2)),
            ),
            frozenset({1}),
        ),
    ),
    Question(
        ExplainQuestionData(
            (_f(5, 6), _f(5, 8)),
            (),
            None,
            False,
            ExplainForm.WHY,
            Explanation(Comparison(_f(5, 6), ">", _f(5, 8)), PartSize(6, 8, larger=True)),
        ),
        MultipleChoice(
            (
                BiggerNumber(8, 6, greater=True),
                PartSize(6, 8, larger=True),
                SameCount(5, total=False, pictured=False),
                PartSize(8, 6, larger=True),
            ),
            frozenset({1}),
        ),
    ),
    Question(
        DrawQuestionData(
            (_f(1, 4), _f(1, 2)), (FractionLine(1), FractionLine(1)), DrawAsked.LESS, "<"
        ),
        MultipleChoice(
            (
                Pick(_f(1, 2), Comparison(_f(1, 4), "<", _f(1, 2))),
                Pick(_f(1, 4), Comparison(_f(1, 4), "<", _f(1, 2))),
                Pick(_f(1, 4), Comparison(_f(1, 4), ">", _f(1, 2))),
                Pick(_f(1, 2), Comparison(_f(1, 4), ">", _f(1, 2))),
            ),
            frozenset({1}),
        ),
    ),
]

# A tiles sheet: a three, a pair one pictured and one not, a pair of names, more and less, and
# all and none
TILES: list[ComparingFractionsQuestion] = [
    Question(GreatestQuestionData((_f(1, 4), _f(1, 3)), True, (), None, _f(1, 3)), FreeResponse()),
    Question(GreatestQuestionData((_f(1, 4), _f(1, 2)), False, (), WALL, _f(1, 4)), FreeResponse()),
    Question(
        GreatestQuestionData((_f(1, 4), _f(1, 3), _f(1, 2)), True, (), None, _f(1, 2)),
        FreeResponse(),
    ),
    Question(
        GreatestQuestionData(
            (_f(5, 8), _f(3, 8)), True, (_strip(8, 5), _strip(8, 3)), None, _f(5, 8)
        ),
        FreeResponse(),
    ),
    Question(GreatestQuestionData((_f(3, 8), _f(5, 8)), False, (), None, _f(3, 8)), FreeResponse()),
    Question(_word(StoryKind.WHOLE, PIZZA, (_f(3, 4), _f(2, 4)), "Ana"), FreeResponse()),
    Question(
        WordQuestionData(
            StoryKind.WHOLE,
            PIZZA,
            ("Ben", "Ana"),
            (_f(5, 6), _f(4, 6)),
            None,
            None,
            True,
            False,
            WordAsked.WHO,
            None,
            (),
            "Ben",
        ),
        FreeResponse(),
    ),
    Question(
        _word(StoryKind.WHOLE, PIZZA, (_f(5, 8), _f(3, 8)), MORE, more_or_less=True),
        FreeResponse(),
    ),
    Question(
        EveryQuestionData(
            _f(1, 2), False, (_f(1, 6), _f(1, 4), _f(1, 3)), (_f(1, 6), _f(1, 4), _f(1, 3))
        ),
        FreeResponse(),
    ),
    Question(EveryQuestionData(_f(2, 2), True, (_f(2, 6), _f(2, 3), _f(1, 2)), ()), FreeResponse()),
]

# Wholes of different sizes, written, and its key
CANT_TELL_STORY: list[ComparingFractionsQuestion] = [
    Question(
        _word(
            StoryKind.WHOLE,
            PIZZA,
            (_f(5, 8), _f(3, 8)),
            CANT_TELL,
            sizes=("small", "large"),
        ),
        FreeResponse(),
    ),
    Question(
        _word(
            StoryKind.LENGTH,
            WORM,
            (_f(1, 3), _f(1, 4)),
            "Ana",
            unit=LengthUnit.INCH,
            form=StoryForm.PLAIN,
        ),
        MultipleChoice(
            (
                StoryChoice(Verdict.AHEAD, "Ana", StoryReason.NONE),
                StoryChoice(Verdict.AHEAD, "Ben", StoryReason.NONE),
                StoryChoice(Verdict.SAME, None, StoryReason.NONE),
                StoryChoice(Verdict.CANT_TELL, None, StoryReason.NONE),
            ),
            frozenset({0}),
        ),
    ),
    Question(
        ExplainQuestionData(
            (_f(6, 8), _f(8, 8)),
            (),
            None,
            True,
            ExplainForm.PAIR,
            Explanation(Comparison(_f(6, 8), "<", _f(8, 8)), PartsOf(_f(6, 8), _f(8, 8), False)),
        ),
        FreeResponse(),
    ),
]


@pytest.mark.parametrize(
    ("case_name", "questions", "slot_of", "answer_key", "black_and_white", "title", "label"),
    [
        ("written", WRITTEN, None, True, False, "Comparing Fractions", "Sheet A"),
        ("choices_black_and_white", CHOICES, None, True, True, "Comparing Fractions", "Sheet A"),
        (
            "tiles",
            TILES,
            (0, 1, 6, 7, 2, 3, 8, 9, 4, 5),
            True,
            False,
            "Comparing Fractions",
            "Sheet A",
        ),
        ("cant_tell", CANT_TELL_STORY, None, True, False, "Comparing Fractions", "Sheet A"),
        ("other_title_and_label", WRITTEN[:2], None, False, False, "Compare", "Day 2"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: Sequence[ComparingFractionsQuestion],
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    black_and_white: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of
    ``comparing_fractions_worksheet_pdf_expecteds.txt``.

    One comparison covers each problem's question, its pictures or wall, the work under them,
    its lettered choices or pictures, its answer line, the rows of problems and their page
    breaks, the answer bank and pattern, the answer key with each problem's fractions in their
    style, the shading's colour, and the title and label.
    """
    actual = pdf_text(
        render_comparing_fractions(
            questions, slot_of, answer_key, title, label, black_and_white=black_and_white
        )
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
