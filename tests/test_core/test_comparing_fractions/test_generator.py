"""
Tests for the comparing fractions question generator.

``test_questions`` scripts ``random``, so each case lists the questions that must be produced.
The names come from ``tests.data``, standing in for the bank, and these functions are replaced:

- ``random.shuffle`` reverses the list, so the question types are dealt from the last ticked, a
  set of fractions is reversed, and a multiple-choice question's correct option is last, its
  wrong options in reverse.
- ``random.choice`` returns the last item: the shared denominator, of the kinds of sharing; the
  last representation that fits, often No picture; the largest denominator and its last set not
  yet used; the pizza, the last story; and the last style.
- ``random.sample`` takes the first items, so the names are handed out in order and a tiles
  sheet's groups take the first lists of fractions.
- ``random.random`` always returns the case's number: 0.0 makes every "one time in n" happen (a
  fraction with itself, pictured stories, "Which is greater than", four fractions, "All of
  these" right, the all/none and more/less pairs on tiles), and 0.99 none of them.

``test_questions_meet_the_rules`` runs the generator for real and checks every question against
the rules it promises.
"""

from collections import Counter
from collections.abc import Sequence
from fractions import Fraction

import pytest

from core.comparing_fractions.choices import is_true, symbol
from core.comparing_fractions.data import (
    ALL_OF_THESE,
    CANT_TELL,
    LESS,
    MORE,
    SAME,
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
    QuestionType,
    Representation,
    SameCount,
    Shared,
    StoryChoice,
    StoryForm,
    StoryKind,
    StoryReason,
    Verdict,
    WordAsked,
    WordQuestionData,
)
from core.comparing_fractions.generator import (
    count_possible_answers,
    generate_comparing_fractions_questions,
    tile_count_fits,
    unaskable_types,
)
from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    AreaModel,
    Circle,
    FractionWall,
    RadialPartition,
    Strip,
    equal_sizes,
)
from core.fraction_models.number_lines import FractionLine
from core.fraction_models.object_groups import ObjectGroup
from core.names import NAMES as BANK_NAMES
from core.question import FreeResponse, MultipleChoice, Question
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.data import NAMES
from tests.helpers import choose_last, random_always_returns, reverse_shuffle, sample_first

COMPARE, EXPLAIN, WORD, LESS_GREATER, DRAW, GREATEST = QuestionType
ALL_TYPES = tuple(QuestionType)
STRIP, GRID, CIRCLE, OTHER, GROUP, LINE, WALL, NONE = Representation
ALL_REPS = tuple(Representation)
NUMERATOR, DENOMINATOR = Shared
BOTH = (NUMERATOR, DENOMINATOR)
DEFAULT = (2, 3, 4, 6, 8)
STACKED, SLASH, SLANTED = FractionStyle


def _f(numerator: int, denominator: int, style: FractionStyle = STACKED) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator, style)


def _shaded(count: int) -> frozenset[int]:
    """Return the first ``count`` parts, shaded."""
    return frozenset(range(count))


def _strip(parts: int, shaded: int) -> AreaModel:
    """Return a strip of ``parts`` equal parts, the first ``shaded`` of them shaded."""
    return AreaModel(Strip(equal_sizes(parts)), _shaded(shaded))


@pytest.mark.parametrize(
    (
        "case_name",
        "drawn",
        "count",
        "question_types",
        "representations",
        "shared",
        "multiple_choice",
        "distinct_answers",
        "expected",
    ),
    [
        (
            # each type once, dealt from the last: sixths and eighths' last sets, the pizza story,
            # a fraction to write less than 7/8, which of two blank number lines is less, and an
            # explanation to write
            "written",
            0.99,
            6,
            ALL_TYPES,
            (STRIP, LINE, NONE),
            BOTH,
            False,
            False,
            [
                Question(
                    GreatestQuestionData((_f(8, 8), _f(7, 8), _f(6, 8)), False, (), None, _f(6, 8)),
                    FreeResponse(),
                ),
                Question(
                    DrawQuestionData(
                        (_f(8, 8), _f(7, 8)),
                        (FractionLine(1), FractionLine(1)),
                        DrawAsked.LESS,
                        ">",
                    ),
                    FreeResponse(),
                ),
                Question(
                    LessGreaterQuestionData(
                        _f(7, 8),
                        False,
                        LessGreaterForm.WRITE,
                        _strip(8, 7),
                        _strip(1, 0),
                        (),
                        (
                            _f(1, 8),
                            _f(2, 8),
                            _f(3, 8),
                            _f(4, 8),
                            _f(5, 8),
                            _f(6, 8),
                            _f(7, 9),
                            _f(7, 10),
                            _f(7, 11),
                            _f(7, 12),
                        ),
                    ),
                    FreeResponse(),
                ),
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Ana", "Ben"),
                        (_f(6, 8), _f(8, 8)),
                        None,
                        None,
                        False,
                        False,
                        WordAsked.WHO,
                        None,
                        (),
                        "Ana",
                    ),
                    FreeResponse(),
                ),
                Question(
                    ExplainQuestionData(
                        (_f(7, 8), _f(6, 8)),
                        (),
                        None,
                        False,
                        ExplainForm.WRITE,
                        Explanation(
                            Comparison(_f(6, 8), "<", _f(7, 8)), PartsOf(_f(6, 8), _f(7, 8), False)
                        ),
                    ),
                    FreeResponse(),
                ),
                Question(
                    CompareQuestionData((_f(8, 8), _f(5, 8)), (), None, False, ">"), FreeResponse()
                ),
            ],
        ),
        (
            # the same, with choices: each written either way round, the right one last; which of
            # two is less, picked with a comparison; which model shows less than 7/8; reasons
            "choices",
            0.99,
            6,
            ALL_TYPES,
            (STRIP, LINE, NONE),
            BOTH,
            True,
            False,
            [
                Question(
                    GreatestQuestionData((_f(8, 8), _f(7, 8), _f(6, 8)), False, (), None, _f(6, 8)),
                    MultipleChoice(
                        (
                            _f(8, 8),
                            _f(7, 8),
                            _f(6, 8),
                        ),
                        frozenset({2}),
                    ),
                ),
                Question(
                    DrawQuestionData(
                        (_f(8, 8), _f(7, 8)),
                        (FractionLine(1), FractionLine(1)),
                        DrawAsked.LESS,
                        ">",
                    ),
                    MultipleChoice(
                        (
                            Pick(_f(7, 8), Comparison(_f(8, 8), "<", _f(7, 8))),
                            Pick(_f(8, 8), Comparison(_f(8, 8), "<", _f(7, 8))),
                            Pick(_f(8, 8), Comparison(_f(8, 8), ">", _f(7, 8))),
                            Pick(_f(7, 8), Comparison(_f(8, 8), ">", _f(7, 8))),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    LessGreaterQuestionData(
                        _f(7, 8),
                        False,
                        LessGreaterForm.SHOWS,
                        _strip(8, 7),
                        _strip(1, 0),
                        (),
                        (_f(7, 12),),
                    ),
                    MultipleChoice(
                        (
                            _strip(8, 8),
                            _strip(8, 7),
                            _strip(7, 7),
                            _strip(12, 7),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Ana", "Ben"),
                        (_f(6, 8), _f(8, 8)),
                        None,
                        None,
                        False,
                        False,
                        WordAsked.WHO,
                        StoryForm.WHO_SYMBOL,
                        (),
                        "Ana",
                    ),
                    MultipleChoice(
                        (
                            StoryChoice(
                                Verdict.AHEAD,
                                "Ben",
                                StoryReason.FRACTION,
                                Comparison(_f(6, 8), "<", _f(8, 8)),
                                True,
                            ),
                            StoryChoice(
                                Verdict.AHEAD,
                                "Ben",
                                StoryReason.FRACTION,
                                Comparison(_f(6, 8), ">", _f(8, 8)),
                                True,
                            ),
                            StoryChoice(
                                Verdict.AHEAD,
                                "Ana",
                                StoryReason.FRACTION,
                                Comparison(_f(6, 8), ">", _f(8, 8)),
                                True,
                            ),
                            StoryChoice(
                                Verdict.AHEAD,
                                "Ana",
                                StoryReason.FRACTION,
                                Comparison(_f(6, 8), "<", _f(8, 8)),
                                True,
                            ),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    ExplainQuestionData(
                        (_f(7, 8), _f(6, 8)),
                        (),
                        None,
                        False,
                        ExplainForm.WHY,
                        Explanation(
                            Comparison(_f(6, 8), "<", _f(7, 8)), PartsOf(_f(6, 8), _f(7, 8), False)
                        ),
                    ),
                    MultipleChoice(
                        (
                            PartsOf(_f(6, 8), _f(7, 8), True),
                            SameCount(8, True, False),
                            PartSize(6, 7, False),
                            PartsOf(_f(6, 8), _f(7, 8), False),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    CompareQuestionData((_f(8, 8), _f(5, 8)), (), None, False, ">"),
                    MultipleChoice(
                        (
                            Comparison(_f(8, 8), "=", _f(6, 8)),
                            Comparison(_f(7, 8), ">", _f(8, 8)),
                            Comparison(_f(8, 8), "<", _f(5, 8)),
                            Comparison(_f(5, 8), "<", _f(8, 8)),
                        ),
                        frozenset({3}),
                    ),
                ),
            ],
        ),
        (
            # every "one time in n": a fraction with itself, pictured pizzas, "All of these"
            # right; the second "less than" question about another fraction
            "often_choices",
            0.0,
            4,
            (COMPARE, WORD),
            (CIRCLE, NONE),
            BOTH,
            True,
            False,
            [
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Ana", "Ben"),
                        (_f(7, 8), _f(7, 8)),
                        None,
                        None,
                        True,
                        False,
                        WordAsked.WHO,
                        StoryForm.PLAIN,
                        (
                            AreaModel(
                                RadialPartition(Circle(), equal_sizes(8)),
                                _shaded(7),
                                look=DrawnObject.PIZZA,
                            ),
                            AreaModel(
                                RadialPartition(Circle(), equal_sizes(8)),
                                _shaded(7),
                                look=DrawnObject.PIZZA,
                            ),
                        ),
                        "the same",
                    ),
                    MultipleChoice(
                        (
                            StoryChoice(Verdict.CANT_TELL, None, StoryReason.NONE),
                            StoryChoice(Verdict.AHEAD, "Ben", StoryReason.NONE),
                            StoryChoice(Verdict.AHEAD, "Ana", StoryReason.NONE),
                            StoryChoice(Verdict.SAME, None, StoryReason.NONE),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    EveryQuestionData(
                        _f(1, 2),
                        False,
                        (_f(1, 6), _f(1, 4), _f(1, 3)),
                        (_f(1, 6), _f(1, 4), _f(1, 3)),
                    ),
                    MultipleChoice(
                        (
                            _f(1, 6),
                            _f(1, 4),
                            _f(1, 3),
                            "All of these",
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Cy", "Dot"),
                        (_f(6, 8), _f(6, 8)),
                        None,
                        None,
                        True,
                        False,
                        WordAsked.WHO,
                        StoryForm.PLAIN,
                        (
                            AreaModel(
                                RadialPartition(Circle(), equal_sizes(8)),
                                _shaded(6),
                                look=DrawnObject.PIZZA,
                            ),
                            AreaModel(
                                RadialPartition(Circle(), equal_sizes(8)),
                                _shaded(6),
                                look=DrawnObject.PIZZA,
                            ),
                        ),
                        "the same",
                    ),
                    MultipleChoice(
                        (
                            StoryChoice(Verdict.CANT_TELL, None, StoryReason.NONE),
                            StoryChoice(Verdict.AHEAD, "Dot", StoryReason.NONE),
                            StoryChoice(Verdict.AHEAD, "Cy", StoryReason.NONE),
                            StoryChoice(Verdict.SAME, None, StoryReason.NONE),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    EveryQuestionData(
                        _f(2, 2),
                        False,
                        (_f(2, 6), _f(2, 3), _f(1, 2)),
                        (_f(2, 6), _f(2, 3), _f(1, 2)),
                    ),
                    MultipleChoice(
                        (
                            _f(2, 6),
                            _f(2, 3),
                            _f(1, 2),
                            "All of these",
                        ),
                        frozenset({3}),
                    ),
                ),
            ],
        ),
        (
            # written: one fraction greater than 1/2 to circle, four fractions, the same amount
            "often_written",
            0.0,
            4,
            (COMPARE, WORD, GREATEST),
            (GRID, NONE),
            BOTH,
            False,
            False,
            [
                Question(
                    EveryQuestionData(_f(1, 2), True, (_f(1, 4), _f(1, 3), _f(2, 2)), (_f(2, 2),)),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData(
                        (_f(8, 8), _f(7, 8), _f(6, 8), _f(5, 8)), True, (), None, _f(8, 8)
                    ),
                    FreeResponse(),
                ),
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Ana", "Ben"),
                        (_f(7, 8), _f(7, 8)),
                        None,
                        None,
                        True,
                        False,
                        WordAsked.WHO,
                        None,
                        (),
                        "the same",
                    ),
                    FreeResponse(),
                ),
                Question(
                    EveryQuestionData(_f(1, 3), True, (_f(1, 6), _f(1, 4), _f(2, 3)), (_f(2, 3),)),
                    FreeResponse(),
                ),
            ],
        ),
        (
            # a three (the greatest third) and a pair sharing a numerator, the pair one pictured and
            # one not; two word problems about Ana and Ben, one answered by each
            "tiles",
            0.99,
            7,
            (COMPARE, WORD, GREATEST),
            (STRIP, NONE),
            BOTH,
            False,
            True,
            [
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Ben", "Ana"),
                        (_f(6, 8), _f(8, 8)),
                        None,
                        None,
                        False,
                        False,
                        WordAsked.WHO,
                        None,
                        (),
                        "Ben",
                    ),
                    FreeResponse(),
                ),
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Ana", "Ben"),
                        (_f(7, 8), _f(8, 8)),
                        None,
                        None,
                        False,
                        False,
                        WordAsked.WHO,
                        None,
                        (),
                        "Ana",
                    ),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData(
                        (_f(1, 8), _f(1, 6)), False, (_strip(8, 1), _strip(6, 1)), None, _f(1, 8)
                    ),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData((_f(1, 8), _f(1, 6)), True, (), None, _f(1, 6)),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData((_f(1, 4), _f(1, 3), _f(1, 2)), True, (), None, _f(1, 2)),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData((_f(1, 4), _f(1, 2)), False, (), None, _f(1, 4)),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData((_f(1, 4), _f(1, 3)), True, (), None, _f(1, 3)),
                    FreeResponse(),
                ),
            ],
        ),
        (
            # Greatest and least alone: a group of five unit fractions
            "tiles_greatest_alone",
            0.99,
            5,
            (GREATEST,),
            (NONE,),
            BOTH,
            False,
            True,
            [
                Question(
                    GreatestQuestionData((_f(1, 8), _f(1, 6), _f(1, 4)), True, (), None, _f(1, 4)),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData((_f(1, 6), _f(1, 4), _f(1, 3)), True, (), None, _f(1, 3)),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData((_f(1, 6), _f(1, 4), _f(1, 3)), False, (), None, _f(1, 6)),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData(
                        (_f(1, 8), _f(1, 6), _f(1, 3), _f(1, 2)), True, (), None, _f(1, 2)
                    ),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData(
                        (_f(1, 8), _f(1, 6), _f(1, 3), _f(1, 2)), False, (), None, _f(1, 8)
                    ),
                    FreeResponse(),
                ),
            ],
        ),
        (
            # a pair, the all/none pair, the more/less pair and a pair of names
            "tiles_often",
            0.0,
            8,
            (COMPARE, WORD),
            (STRIP, NONE),
            BOTH,
            False,
            True,
            [
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Ana", "Ben"),
                        (_f(8, 8), _f(5, 8)),
                        None,
                        None,
                        True,
                        True,
                        WordAsked.WHO,
                        None,
                        (),
                        "more",
                    ),
                    FreeResponse(),
                ),
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Cy", "Dot"),
                        (_f(6, 8), _f(7, 8)),
                        None,
                        None,
                        True,
                        True,
                        WordAsked.WHO,
                        None,
                        (),
                        "less",
                    ),
                    FreeResponse(),
                ),
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Eve", "Ana"),
                        (_f(8, 8), _f(6, 8)),
                        None,
                        None,
                        False,
                        False,
                        WordAsked.WHO,
                        None,
                        (),
                        "Ana",
                    ),
                    FreeResponse(),
                ),
                Question(
                    WordQuestionData(
                        StoryKind.WHOLE,
                        12,
                        ("Ana", "Eve"),
                        (_f(8, 8), _f(7, 8)),
                        None,
                        None,
                        False,
                        False,
                        WordAsked.WHO,
                        None,
                        (),
                        "Eve",
                    ),
                    FreeResponse(),
                ),
                Question(
                    EveryQuestionData(_f(2, 2), True, (_f(2, 6), _f(2, 3), _f(1, 2)), ()),
                    FreeResponse(),
                ),
                Question(
                    EveryQuestionData(
                        _f(1, 2),
                        False,
                        (_f(1, 6), _f(1, 4), _f(1, 3)),
                        (_f(1, 6), _f(1, 4), _f(1, 3)),
                    ),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData((_f(1, 3), _f(1, 2)), False, (), None, _f(1, 3)),
                    FreeResponse(),
                ),
                Question(
                    GreatestQuestionData(
                        (_f(1, 3), _f(1, 2)), True, (_strip(3, 1), _strip(2, 1)), None, _f(1, 2)
                    ),
                    FreeResponse(),
                ),
            ],
        ),
    ],
)
def test_questions(
    case_name: str,
    drawn: float,
    count: int,
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    shared: Sequence[Shared],
    multiple_choice: bool,
    distinct_answers: bool,
    expected: list[ComparingFractionsQuestion],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("core.comparing_fractions.generator.NAMES", NAMES)
    choose_last(monkeypatch)
    reverse_shuffle(monkeypatch)
    sample_first(monkeypatch)
    random_always_returns(monkeypatch, drawn)

    questions = generate_comparing_fractions_questions(
        count,
        question_types,
        representations,
        shared,
        DEFAULT,
        multiple_choice=multiple_choice,
        distinct_answers=distinct_answers,
    )

    assert questions == expected


def _shown(picture: Picture) -> Fraction:
    """Return the fraction a picture shows: its shaded parts of all, its shaded objects of all,
    or how far along its line it's marked, 0 when it isn't."""
    match picture:
        case AreaModel():
            return Fraction(len(picture.shaded), picture.split.parts)
        case ObjectGroup():
            return Fraction(len(picture.shaded), picture.count)
        case _:
            ticks = [point.tick for point in picture.points]
            marked = picture.jumps or picture.bar_to or (ticks[0] if ticks else 0)
            return Fraction(marked, picture.parts)


def _value(option: object) -> Fraction | None:
    """Return the value a choice shows, a fraction or a picture's, else ``None``."""
    if isinstance(option, UnreducedFraction):
        return option.value
    if isinstance(option, AreaModel | ObjectGroup | FractionLine):
        return _shown(option)
    return None


def _share_a_number(fractions: Sequence[UnreducedFraction], shared: Sequence[Shared]) -> bool:
    """Return whether ``fractions`` all share a numerator, or all a denominator, as ``shared``
    allows; a fraction with itself shares both."""
    numerators = {each.numerator for each in fractions}
    denominators = {each.denominator for each in fractions}
    return (len(numerators) == 1 and (NUMERATOR in shared or len(denominators) == 1)) or (
        len(denominators) == 1 and DENOMINATOR in shared
    )


def _word_answer(data: WordQuestionData) -> str:
    """Return the answer a word problem's story gives."""
    left, right = data.fractions
    if data.sizes is not None:
        return CANT_TELL
    if data.more_or_less:
        return MORE if left.value > right.value else LESS
    if left.value == right.value:
        return SAME
    first_ahead = left.value > right.value
    return data.names[0] if first_ahead == data.greater else data.names[1]


def _broken_picture_rules(
    fractions: Sequence[UnreducedFraction],
    pictures: Sequence[Picture],
    wall: FractionWall | None,
    representations: Sequence[Representation],
) -> list[str]:
    """Return the rules a question's pictures or wall break: they don't show its fractions, or
    show them in a representation that isn't ticked, or there's none though No picture isn't
    ticked."""
    broken = []
    if pictures and [_shown(each) for each in pictures] != [each.value for each in fractions]:
        broken.append(f"the pictures don't show {fractions}")
    if wall is not None and (
        WALL not in representations
        or not {each.denominator for each in fractions} <= set(wall.denominators)
    ):
        broken.append("a wall that isn't ticked, or lacks a row")
    if not pictures and wall is None and NONE not in representations:
        broken.append("no picture, though No picture isn't ticked")
    return broken


def _broken_question_rules(
    question: ComparingFractionsQuestion,
    representations: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
) -> list[str]:
    """Return the rules ``question``'s data breaks, as text, or none."""
    data = question.data
    broken = []
    match data:
        case CompareQuestionData() | ExplainQuestionData() | GreatestQuestionData():
            fractions: tuple[UnreducedFraction, ...] = data.fractions
            broken += _broken_picture_rules(fractions, data.pictures, data.wall, representations)
        case WordQuestionData():
            fractions = data.fractions
            if data.pictures:
                broken += _broken_picture_rules(fractions, data.pictures, None, representations)
        case DrawQuestionData():
            fractions = data.fractions
            if any(_shown(each) != 0 or each.parts != 1 for each in data.blanks):
                broken.append("a whole to divide is cut or shaded")
        case EveryQuestionData():
            fractions = (data.target, *data.fractions)
        case LessGreaterQuestionData():
            fractions = (data.fraction,)
    if any(each.denominator not in denominators for each in fractions):
        broken.append(f"{fractions} aren't over denominators asked for")
    if not isinstance(data, EveryQuestionData) and not _share_a_number(fractions, shared):
        broken.append(f"{fractions} don't share a ticked kind of number")
    match data:
        case CompareQuestionData() | DrawQuestionData():
            if data.answer != symbol(*data.fractions):
                broken.append(f"{data.answer} doesn't compare {data.fractions}")
        case EveryQuestionData():
            on_side = tuple(
                each for each in data.fractions if (each.value > data.target.value) == data.greater
            )
            sharing = all(_share_a_number((data.target, each), shared) for each in data.fractions)
            if data.answer != on_side or not sharing:
                broken.append("the answer isn't those on the asked side, or one shares no number")
        case ExplainQuestionData():
            comparison = data.answer.comparison
            if not is_true(comparison) or {comparison.left, comparison.right} != set(fractions):
                broken.append("the explanation isn't true of the fractions")
        case WordQuestionData():
            if data.answer != _word_answer(data):
                broken.append(f"the story doesn't answer {data.answer}")
        case LessGreaterQuestionData():
            if _shown(data.model) != data.fraction.value or _shown(data.blank) != 0:
                broken.append("the model doesn't show the fraction, or the blank is shaded")
            if isinstance(question.response, FreeResponse) and any(
                (each.value > data.fraction.value) != data.greater for each in data.answer
            ):
                broken.append("a way in the key isn't one")
            if data.form is LessGreaterForm.CIRCLE:
                ways = tuple(
                    _shown(each)
                    for each in data.pictures
                    if (
                        _shown(each) > data.fraction.value
                        if data.greater
                        else _shown(each) < data.fraction.value
                    )
                )
                if (
                    len(data.pictures) != 4
                    or ways != tuple(each.value for each in data.answer)
                    or not 1 <= len(ways) <= 3
                ):
                    broken.append("the models to circle aren't four, one to three of them ways")
        case GreatestQuestionData():
            pick = max if data.greatest else min
            values = [each.value for each in data.fractions]
            if data.answer.value != pick(values) or len(set(values)) != len(values):
                broken.append("the answer isn't the greatest (least), or values repeat")
    return broken


def _broken_choice_rules(question: ComparingFractionsQuestion) -> list[str]:
    """Return the rules ``question``'s choices break, as text, or none."""
    data, response = question.data, question.response
    if not isinstance(response, MultipleChoice):
        return []
    options: tuple[object, ...] = response.options
    if len(response.correct_indexes) != 1 or len(options) not in (3, 4):
        return ["not three or four options with one correct"]
    right = next(iter(response.correct_indexes))
    correct = options[right]
    broken = []
    if len(set(options)) != len(options):
        broken.append("choices repeat")
    true = [
        index
        for index, each in enumerate(options)
        if isinstance(each, Comparison) and is_true(each)
    ]
    if isinstance(correct, Comparison) and true != [right]:
        broken.append(f"comparisons true at {true}, not only {right}")
    match data:
        case EveryQuestionData():
            all_right = len(data.answer) == len(data.fractions)
            expected = len(data.fractions) if all_right else data.fractions.index(data.answer[0])
            if right != expected or options[-1] != ALL_OF_THESE or len(data.answer) not in (1, 3):
                broken.append("the right choice isn't the one, or All of these")
        case ExplainQuestionData():
            expected_right = data.answer if data.form is ExplainForm.PAIR else data.answer.reason
            if correct != expected_right:
                broken.append("the right explanation or reason isn't the answer's")
        case DrawQuestionData() if data.asked is not DrawAsked.SYMBOL:
            pick = max if data.asked is DrawAsked.GREATER else min
            wanted = pick(data.fractions, key=lambda each: each.value)
            if not (
                isinstance(correct, Pick) and correct.fraction == wanted and is_true(correct.claim)
            ):
                broken.append("the right pick isn't the fraction asked for, truly compared")
        case LessGreaterQuestionData():
            # a way is strictly less (greater): the same fraction isn't one
            values = [_value(each) for each in options]
            asked = [
                value is not None
                and (value > data.fraction.value if data.greater else value < data.fraction.value)
                for value in values
            ]
            # "Which is NOT a way?" has one that isn't; "Which model shows?" has one that is
            odd_one = data.form is LessGreaterForm.SHOWS
            if asked.count(odd_one) != 1 or asked[right] != odd_one:
                broken.append("the right picture isn't the one that is (isn't) a way")
            if values[right] != data.answer[0].value:
                broken.append("the right picture doesn't show the answer")
        case GreatestQuestionData():
            if _value(correct) != data.answer.value:
                broken.append("the right choice isn't the answer")
        case WordQuestionData():
            if not isinstance(correct, StoryChoice) or (
                correct.brief and correct.who != data.answer
            ):
                broken.append("the brief right choice isn't the answer")
    return broken


def _tile_answer(question: ComparingFractionsQuestion) -> object:
    """Return a tiles sheet's answer as the bank shows it."""
    data = question.data
    if isinstance(data, EveryQuestionData):
        return "all" if data.answer else "none"
    return data.answer


def _broken_tile_rules(questions: Sequence[ComparingFractionsQuestion]) -> list[str]:
    """Return the rules a tiles sheet breaks, as text, or none."""
    broken = []
    answers = [_tile_answer(each) for each in questions]
    if len(set(answers)) != len(answers):
        broken.append(f"answers repeat: {answers}")
    kinds = Counter(type(each.data) for each in questions)
    if kinds.keys() - {GreatestQuestionData, WordQuestionData, EveryQuestionData}:
        broken.append(f"a question with no single answer: {kinds}")
    groups = [each.data for each in questions if isinstance(each.data, GreatestQuestionData)]
    answered = Counter(data.answer for data in groups)
    offered = Counter(fraction for data in groups for fraction in data.fractions)
    if offered.keys() - answered.keys():
        broken.append("a fraction offered that no question answers")
    if any(offered[fraction] < 2 for fraction in answered):
        broken.append("an answer offered only by its own question")
    if answers.count("all") != answers.count("none"):
        broken.append("all and none don't come as a pair")
    words = [each.data for each in questions if isinstance(each.data, WordQuestionData)]
    if sorted(data.answer for data in words if data.answer in (MORE, LESS)) not in (
        [],
        [LESS, MORE],
    ):
        broken.append("more and less don't come as a pair")
    named = Counter(name for data in words if not data.more_or_less for name in data.names)
    for data in words:
        if data.answer in (SAME, CANT_TELL) or (not data.more_or_less and named[data.answer] != 2):
            broken.append(f"{data.answer} isn't a name in exactly two word problems")
    return broken


@pytest.mark.parametrize(
    (
        "question_types",
        "representations",
        "shared",
        "denominators",
        "multiple_choice",
        "distinct_answers",
        "count",
    ),
    [
        (ALL_TYPES, ALL_REPS, BOTH, DEFAULT, False, False, 12),
        (ALL_TYPES, ALL_REPS, BOTH, DEFAULT, True, False, 12),
        (ALL_TYPES, ALL_REPS, BOTH, DEFAULT, False, True, 12),
        (ALL_TYPES, ALL_REPS, BOTH, tuple(range(2, 13)), True, False, 12),
        (ALL_TYPES, ALL_REPS, BOTH, tuple(range(2, 1001)), False, False, 12),
        (
            ALL_TYPES,
            (STRIP, GRID, CIRCLE, OTHER),
            BOTH,
            DEFAULT,
            True,
            False,
            12,
        ),  # every one drawn
        ((COMPARE, WORD, GREATEST), (GROUP,), BOTH, DEFAULT, False, False, 12),
        ((COMPARE, EXPLAIN, DRAW, GREATEST), (LINE,), BOTH, DEFAULT, True, False, 12),
        ((COMPARE, EXPLAIN, GREATEST), (WALL,), BOTH, DEFAULT, True, False, 12),
        (ALL_TYPES, ALL_REPS, (NUMERATOR,), DEFAULT, True, False, 12),
        (ALL_TYPES, ALL_REPS, (DENOMINATOR,), DEFAULT, False, False, 12),
        ((GREATEST,), ALL_REPS, BOTH, DEFAULT, False, True, 10),  # groups of four or more
        ((COMPARE,), ALL_REPS, BOTH, DEFAULT, False, True, 11),  # pairs and threes
        ((COMPARE, GREATEST), (STRIP,), BOTH, DEFAULT, False, True, 12),  # every one drawn
        ((WORD,), ALL_REPS, BOTH, DEFAULT, False, True, 9),  # name pairs, a trio, more and less
        ((COMPARE, WORD), (NONE,), (NUMERATOR,), (2, 3), False, True, 5),  # pairs and names
    ],
)
def test_questions_meet_the_rules(
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    multiple_choice: bool,
    distinct_answers: bool,
    count: int,
) -> None:
    """
    Over 30 sheets, every question's fractions share a ticked kind of number, over denominators
    asked for, its pictures or wall show them in a ticked representation, and its answer is
    right; its choices are three or four with one right, the one true comparison, the one way
    that isn't, the answer. With distinct answers, no two answers are the same, only the types
    with one answer are asked, every fraction a question offers answers another, every answer
    is offered by another question too, all and none come as a pair, more and less as a pair,
    and names in pairs or a trio.
    """
    broken = []
    for _ in range(30):
        questions = generate_comparing_fractions_questions(
            count,
            question_types,
            representations,
            shared,
            denominators,
            multiple_choice=multiple_choice,
            distinct_answers=distinct_answers,
        )
        for question in questions:
            broken += _broken_question_rules(question, representations, shared, denominators)
            broken += _broken_choice_rules(question)
            if multiple_choice != isinstance(question.response, MultipleChoice):
                broken.append("its response doesn't match the sheet")
        if distinct_answers:
            broken += _broken_tile_rules(questions)
        if len(questions) != count:
            broken.append(f"{len(questions)} questions, not {count}")
    assert broken == []


@pytest.mark.parametrize(
    ("question_types", "representations", "shared", "denominators", "expected"),
    [
        # every fraction over the denominators, and the all/none pair
        ((COMPARE,), (NONE,), BOTH, DEFAULT, 23 + 2),
        ((COMPARE,), (STRIP,), BOTH, DEFAULT, 23),  # the pair has no picture
        ((GREATEST,), (NONE,), (DENOMINATOR,), DEFAULT, 4 + 6 + 8),  # fourths, sixths, eighths
        ((GREATEST,), (NONE,), (NUMERATOR,), DEFAULT, 5 + 5 + 4),  # numerators 1, 2 and 3
        ((COMPARE, GREATEST), (NONE,), (NUMERATOR,), (2, 3), 4),  # no all/none pair
        ((WORD,), ALL_REPS, BOTH, DEFAULT, len(BANK_NAMES)),  # one for each name
        ((COMPARE, WORD), (NONE,), BOTH, DEFAULT, 25 + len(BANK_NAMES)),
        ((EXPLAIN, DRAW), ALL_REPS, BOTH, DEFAULT, 0),  # left out of tiles
    ],
)
def test_count_possible_answers(
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    expected: int,
) -> None:
    assert count_possible_answers(question_types, representations, shared, denominators) == expected


@pytest.mark.parametrize(
    (
        "question_types",
        "representations",
        "shared",
        "denominators",
        "multiple_choice",
        "distinct_answers",
        "expected",
    ),
    [
        (ALL_TYPES, ALL_REPS, BOTH, DEFAULT, False, False, []),
        # nothing to shade or divide
        (ALL_TYPES, (NONE,), BOTH, DEFAULT, False, False, [LESS_GREATER, DRAW]),
        # a wall shows different denominators only, and no story is drawn on one
        (ALL_TYPES, (WALL,), (DENOMINATOR,), DEFAULT, False, False, list(ALL_TYPES)),
        # explained with choices, a shared denominator needs numerators of 2 or more
        ((EXPLAIN,), (NONE,), (DENOMINATOR,), (2,), True, False, [EXPLAIN]),
        ((EXPLAIN,), (NONE,), (DENOMINATOR,), (2,), False, False, []),
        ((DRAW,), (STRIP,), BOTH, (13, 14), False, False, [DRAW]),  # too many parts to divide
        # on tiles, the types with no single answer are left out, not unaskable
        (ALL_TYPES, ALL_REPS, BOTH, DEFAULT, False, True, []),
        ((GREATEST,), (NONE,), (NUMERATOR,), (2, 3), False, True, [GREATEST]),  # no four
        ((COMPARE, GREATEST), (NONE,), (NUMERATOR,), (2, 3), False, True, [GREATEST]),  # no three
        ((COMPARE,), (STRIP,), (NUMERATOR,), (2,), False, True, [COMPARE]),  # no pair
        ((WORD,), (WALL,), BOTH, DEFAULT, False, True, [WORD]),
    ],
)
def test_unaskable_types(
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    multiple_choice: bool,
    distinct_answers: bool,
    expected: list[QuestionType],
) -> None:
    assert (
        unaskable_types(
            question_types,
            representations,
            shared,
            denominators,
            multiple_choice=multiple_choice,
            distinct_answers=distinct_answers,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("count", "question_types", "shared", "denominators", "expected"),
    [
        (3, (COMPARE,), (NUMERATOR,), (2, 3), False),  # pairs only: no three
        (4, (COMPARE,), (NUMERATOR,), (2, 3), True),
        (5, (COMPARE,), (NUMERATOR,), DEFAULT, True),
        (3, (GREATEST,), BOTH, DEFAULT, False),  # groups of four or more
        (7, (GREATEST,), (DENOMINATOR,), (4, 6), False),  # 4, or 4 to 6
        (9, (GREATEST,), (DENOMINATOR,), (4, 6), True),  # 4 and 5
        (1, (WORD,), BOTH, DEFAULT, False),  # names come in pairs
        (2, (WORD,), BOTH, DEFAULT, True),
        # a lone word problem gives its place to the fractions, which can't take three: all
        # three are word problems
        (3, (COMPARE, WORD), (NUMERATOR,), (2, 3), True),
    ],
)
def test_tile_count_fits(
    count: int,
    question_types: Sequence[QuestionType],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    expected: bool,
) -> None:
    assert tile_count_fits(count, question_types, (NONE,), shared, denominators) is expected


@pytest.mark.parametrize(
    (
        "count",
        "question_types",
        "representations",
        "shared",
        "multiple_choice",
        "distinct_answers",
        "message",
    ),
    [
        (
            2,
            (),
            ALL_REPS,
            BOTH,
            False,
            False,
            "A question type, a representation, a kind of sharing, a denominator and a style are "
            "needed.",
        ),
        (
            2,
            ALL_TYPES,
            ALL_REPS,
            BOTH,
            True,
            True,
            "Multiple-choice questions have no answers to keep distinct.",
        ),
        (
            2,
            (EXPLAIN, DRAW),
            ALL_REPS,
            BOTH,
            False,
            True,
            "A self-check tiles sheet asks none of these types: none has one answer.",
        ),
        (
            2,
            (LESS_GREATER,),
            (NONE,),
            BOTH,
            False,
            False,
            "No question of type less_greater fits these settings.",
        ),
        (
            3,
            (GREATEST,),
            (NONE,),
            BOTH,
            False,
            True,
            "A tiles sheet of these types can't have 3 questions.",
        ),
    ],
)
def test_generate_comparing_fractions_questions_errors(
    count: int,
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    shared: Sequence[Shared],
    multiple_choice: bool,
    distinct_answers: bool,
    message: str,
) -> None:
    with pytest.raises(ValueError) as error:
        generate_comparing_fractions_questions(
            count,
            question_types,
            representations,
            shared,
            DEFAULT,
            multiple_choice=multiple_choice,
            distinct_answers=distinct_answers,
        )
    assert str(error.value) == message


def test_an_all_or_none_question_that_cant_be_made_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the all-or-none pair is planned but one of it can't be made after all, the sheet
    raises rather than coming up short."""
    monkeypatch.setattr("core.comparing_fractions.generator.every_question", lambda *_: None)
    random_always_returns(monkeypatch, 0.0)  # the pair comes
    with pytest.raises(ValueError) as error:
        generate_comparing_fractions_questions(
            4, (COMPARE,), (NONE,), BOTH, DEFAULT, distinct_answers=True
        )
    assert str(error.value) == "No fractions fit an all-or-none question."
