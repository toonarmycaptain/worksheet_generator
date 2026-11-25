"""
Tests for the fractions on a number line question generator.

``test_questions`` scripts ``random``, so each case lists the questions that must be produced.
The names come from ``tests.data``, standing in for the bank, and these functions are replaced:

- ``random.shuffle`` reverses the list, so the question types are dealt from the last ticked, and
  a multiple-choice question's correct option is last, its wrong options in reverse.
- ``random.choice`` returns the last item: the largest denominator, then the last answer over it
  that isn't a whole (or the whole, when ``random.random`` lets it), the last pair of distances,
  story, unit and style, and the last of the ways to choose wrong answers that it's choosing
  among.
- ``random.sample`` takes the first items, so the names are handed out in order, and the wrong
  points left of the answer are tried from none up.
- ``random.random`` always returns the case's number: 0.0 makes every "one time in n" happen
  (wholes, stars, jumps, "how far", a line of other parts, "None of these" and it being right,
  points between ticks, a compare story's shorter distance first), and 0.99 none of them.

``test_questions_meet_the_rules`` runs the generator for real and checks every question against
the rules it promises.
"""

from collections import Counter
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
    QuestionType,
)
from core.fraction_number_lines.generator import (
    LETTER_SPACING,
    OFF_TICK_CLEARANCE,
    count_possible_answers,
    generate_fraction_number_lines_questions,
    unaskable_types,
)
from core.fraction_number_lines.stories import DISTANCE_STORIES
from core.names import NAMES as BANK_NAMES
from core.question import FreeResponse, MultipleChoice, Question
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.data import NAMES
from tests.helpers import choose_last, random_always_returns, reverse_shuffle, sample_first

NAME, MARK, DISTANCE, DIVIDE, COMPARE = QuestionType
MARK_IT, HOW_FAR = DistanceAsked
FARTHER, SHORTER, MORE_OR_LESS = Compared
STACKED, SLASH, SLANTED = FractionStyle
ALL_TYPES = (NAME, MARK, DISTANCE, DIVIDE, COMPARE)
BIKE = len(DISTANCE_STORIES) - 1  # the last story: "rode a bike … from home"
KILOMETER = LengthUnit.KILOMETER  # the bike story's last unit
FROM_HOME = (LinePicture(0, DrawnObject.HOUSE),)


def _f(numerator: int, denominator: int, style: FractionStyle = STACKED) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator, style)


def _point_at(parts: int, tick: int) -> FractionLine:
    """Return a line of ``parts`` parts with a dot on tick ``tick``."""
    return FractionLine(parts, points=(LinePoint(tick),))


def _story_line(parts: int, tick: int, letter: str, mark: Mark, jumps: bool) -> FractionLine:
    """Return a bike story's line in kilometers with point ``letter`` on tick ``tick``, the
    distance to it as jumps or an arrow, and the house at 0."""
    return FractionLine(
        parts,
        unit=KILOMETER,
        points=(LinePoint(tick, letter, mark),),
        jumps=tick if jumps else 0,
        arrow_to=None if jumps else tick,
        pictures=FROM_HOME,
    )


def _compare_line(parts: int) -> FractionLine:
    """Return a bike story's line in kilometers, with only the house at 0."""
    return FractionLine(parts, unit=KILOMETER, pictures=FROM_HOME)


@pytest.mark.parametrize(
    (
        "case_name",
        "drawn",
        "count",
        "question_types",
        "denominators",
        "styles",
        "multiple_choice",
        "distinct_answers",
        "expected",
    ),
    [
        (
            # each type once, dealt from the last: eighths, and the last answer that isn't a
            # whole; the bike story, its distance given, and a compare story asking "more or less"
            "written",
            0.99,
            5,
            ALL_TYPES,
            (2, 3, 4, 6, 8),
            (STACKED,),
            False,
            False,
            [
                Question(
                    CompareQuestionData(
                        BIKE,
                        ("Ana", "Ben"),
                        KILOMETER,
                        (_f(7, 8), _f(6, 8)),  # the longer first
                        MORE_OR_LESS,
                        _compare_line(8),
                        MORE,
                    ),
                    FreeResponse(),
                ),
                Question(
                    DivideQuestionData(_f(7, 8), FractionLine(1), _point_at(8, 7)), FreeResponse()
                ),
                Question(
                    DistanceQuestionData(
                        BIKE,
                        "Cy",
                        KILOMETER,
                        MARK_IT,
                        _f(7, 8),
                        _compare_line(8),  # only the start
                        _f(7, 8),
                    ),
                    FreeResponse(),
                ),
                Question(
                    MarkPointQuestionData(_f(7, 8), FractionLine(8), _point_at(8, 7)),
                    FreeResponse(),
                ),
                Question(NamePointQuestionData(_point_at(8, 7), _f(7, 8)), FreeResponse()),
            ],
        ),
        (
            # four choices each: comparisons, divided lines, lines with point C, points on the
            # line, and fractions
            "choices",
            0.99,
            5,
            ALL_TYPES,
            (2, 3, 4, 6, 8),
            (STACKED,),
            True,
            False,
            [
                Question(
                    CompareQuestionData(
                        BIKE,
                        ("Ana", "Ben"),
                        KILOMETER,
                        (_f(7, 8), _f(6, 8)),
                        MORE_OR_LESS,
                        _compare_line(8),
                        MORE,
                    ),
                    MultipleChoice(
                        (
                            Comparison(LESS, _f(7, 8), "<", _f(6, 8)),
                            Comparison(LESS, _f(7, 8), ">", _f(6, 8)),
                            Comparison(MORE, _f(7, 8), "<", _f(6, 8)),
                            Comparison(MORE, _f(7, 8), ">", _f(6, 8)),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    DivideQuestionData(_f(7, 8), FractionLine(1), _point_at(8, 7)),
                    MultipleChoice(
                        (
                            _point_at(9, 7),  # one part more
                            _point_at(7, 7),  # one part fewer, the point at its end
                            FractionLine(  # the right number of parts, unequal
                                8,
                                points=(LinePoint(7),),
                                sizes=tuple(
                                    Fraction(size, 84) for size in (7, 8, 9, 10, 11, 12, 13, 14)
                                ),
                            ),
                            _point_at(8, 7),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    DistanceQuestionData(
                        BIKE, "Cy", KILOMETER, MARK_IT, _f(7, 8), _compare_line(8), _f(7, 8)
                    ),
                    MultipleChoice(
                        (
                            _story_line(3, 2, "C", Mark.DOT, False),  # a line in thirds
                            _story_line(10, 7, "C", Mark.DOT, False),  # the same top number
                            _story_line(8, 8, "C", Mark.DOT, False),  # another point, the end
                            _story_line(8, 7, "C", Mark.DOT, False),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    MarkPointQuestionData(_f(7, 8), FractionLine(8), _point_at(8, 7)),
                    MultipleChoice(
                        # two left of 7/8 and one right, all on ticks: one part, the end, one
                        # tick to the left
                        (Fraction(1, 8), Fraction(1), Fraction(3, 4), Fraction(7, 8)),
                        frozenset({3}),
                    ),
                ),
                Question(
                    NamePointQuestionData(_point_at(8, 7), _f(7, 8)),
                    MultipleChoice(
                        (_f(7, 9), _f(1, 8), _f(1, 7), _f(7, 8)),  # ticks counted, the unit, 1/7
                        frozenset({3}),
                    ),
                ),
            ],
        ),
        (
            # every "one time in n": wholes, stars, jumps, 3/4 on a line of eighths, the last
            # style, and "None of these" right
            "choices_every_time_in_n",
            0.0,
            5,
            ALL_TYPES,
            (2, 3, 4),
            (STACKED, SLASH, SLANTED),
            True,
            False,
            [
                Question(
                    CompareQuestionData(
                        BIKE,
                        ("Ana", "Ben"),
                        KILOMETER,
                        (_f(2, 4, SLANTED), _f(3, 4, SLANTED)),  # the shorter first
                        MORE_OR_LESS,
                        _compare_line(4),
                        LESS,
                    ),
                    MultipleChoice(
                        (
                            Comparison(LESS, _f(2, 4, SLANTED), ">", _f(3, 4, SLANTED)),
                            Comparison(MORE, _f(2, 4, SLANTED), "<", _f(3, 4, SLANTED)),
                            Comparison(MORE, _f(2, 4, SLANTED), ">", _f(3, 4, SLANTED)),
                            Comparison(LESS, _f(2, 4, SLANTED), "<", _f(3, 4, SLANTED)),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    DivideQuestionData(_f(4, 4, SLANTED), FractionLine(1), _point_at(4, 4)),
                    MultipleChoice(
                        (
                            _point_at(5, 4),
                            _point_at(3, 3),
                            FractionLine(
                                4,
                                points=(LinePoint(4),),
                                sizes=(
                                    Fraction(3, 18),
                                    Fraction(4, 18),
                                    Fraction(5, 18),
                                    Fraction(6, 18),
                                ),
                            ),
                            _point_at(4, 4),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    DistanceQuestionData(
                        BIKE,
                        "Cy",
                        KILOMETER,
                        MARK_IT,
                        _f(3, 4, SLANTED),
                        _compare_line(8),
                        _f(6, 8, SLANTED),  # 3/4 on a line of eighths
                    ),
                    MultipleChoice(
                        (
                            # with 7/8 and 6/10, a grid of two lines' parts by two points
                            _story_line(10, 7, "C", Mark.STAR, True),
                            _story_line(10, 6, "C", Mark.STAR, True),
                            _story_line(8, 7, "C", Mark.STAR, True),
                            _story_line(8, 6, "C", Mark.STAR, True),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    MarkPointQuestionData(_f(4, 4, SLANTED), FractionLine(4), _point_at(4, 4)),
                    MultipleChoice(
                        # 4/4 left out: a tick, then two points between ticks
                        (Fraction(5, 8), Fraction(7, 8), Fraction(3, 4), NONE_OF_THESE),
                        frozenset({3}),
                    ),
                ),
                Question(
                    NamePointQuestionData(
                        FractionLine(4, points=(LinePoint(3, mark=Mark.STAR),)), _f(3, 4, SLANTED)
                    ),
                    MultipleChoice(
                        (_f(3, 5, SLANTED), _f(1, 4, SLANTED), _f(1, 3, SLANTED), NONE_OF_THESE),
                        frozenset({3}),
                    ),
                ),
            ],
        ),
        (
            # a story asking how far, with a star, jumps and its own parts
            "written_every_time_in_n",
            0.0,
            5,
            ALL_TYPES,
            (2, 4),
            (STACKED,),
            False,
            False,
            [
                Question(
                    CompareQuestionData(
                        BIKE,
                        ("Ana", "Ben"),
                        KILOMETER,
                        (_f(2, 4), _f(3, 4)),
                        MORE_OR_LESS,
                        _compare_line(4),
                        LESS,
                    ),
                    FreeResponse(),
                ),
                Question(
                    DivideQuestionData(_f(4, 4), FractionLine(1), _point_at(4, 4)), FreeResponse()
                ),
                Question(
                    DistanceQuestionData(
                        BIKE,
                        "Cy",
                        KILOMETER,
                        HOW_FAR,
                        _f(3, 4),
                        _story_line(4, 3, "C", Mark.STAR, True),
                        _f(3, 4),
                    ),
                    FreeResponse(),
                ),
                Question(
                    MarkPointQuestionData(_f(4, 4), FractionLine(4), _point_at(4, 4)),
                    FreeResponse(),
                ),
                Question(
                    NamePointQuestionData(
                        FractionLine(4, points=(LinePoint(3, mark=Mark.STAR),)), _f(3, 4)
                    ),
                    FreeResponse(),
                ),
            ],
        ),
        (
            # tiles: dividing a line left out, and the one compare question its share gives it
            # goes to naming; marking takes the values no written answer has, 1 and 1/4, while
            # 2/4 and 1/2 are both written answers, which count as written
            "tiles",
            0.99,
            5,
            ALL_TYPES,
            (2, 4),
            (STACKED,),
            False,
            True,
            [
                Question(
                    MarkPointQuestionData(_f(4, 4), FractionLine(4), _point_at(4, 4)),
                    FreeResponse(),
                ),
                Question(NamePointQuestionData(_point_at(4, 3), _f(3, 4)), FreeResponse()),
                Question(
                    DistanceQuestionData(
                        BIKE,
                        "Ana",
                        KILOMETER,
                        HOW_FAR,
                        _f(2, 4),
                        _story_line(4, 2, "A", Mark.DOT, False),
                        _f(2, 4),
                    ),
                    FreeResponse(),
                ),
                Question(
                    MarkPointQuestionData(_f(1, 4), FractionLine(4), _point_at(4, 1)),
                    FreeResponse(),
                ),
                Question(NamePointQuestionData(_point_at(2, 1), _f(1, 2)), FreeResponse()),
            ],
        ),
        (
            # five compare questions: Ana and Ben's "more" and Cy and Dot's "less", then a trio,
            # Eve vs Ben, Ben vs Ana and Ana vs Eve, each answered by one of its two names; the
            # five names in tests.data run out, so the trio reuses two
            "tiles_compare",
            0.99,
            5,
            (COMPARE,),
            (4,),
            (STACKED,),
            False,
            True,
            [
                Question(
                    CompareQuestionData(
                        BIKE,
                        ("Eve", "Ben"),
                        KILOMETER,
                        (_f(2, 4), _f(3, 4)),
                        SHORTER,
                        _compare_line(4),
                        "Eve",
                    ),
                    FreeResponse(),
                ),
                Question(
                    CompareQuestionData(
                        BIKE,
                        ("Ben", "Ana"),
                        KILOMETER,
                        (_f(1, 4), _f(3, 4)),
                        SHORTER,
                        _compare_line(4),
                        "Ben",
                    ),
                    FreeResponse(),
                ),
                Question(
                    CompareQuestionData(
                        BIKE,
                        ("Ana", "Eve"),
                        KILOMETER,
                        (_f(1, 4), _f(2, 4)),
                        SHORTER,
                        _compare_line(4),
                        "Ana",
                    ),
                    FreeResponse(),
                ),
                Question(
                    CompareQuestionData(
                        BIKE,
                        ("Cy", "Dot"),
                        KILOMETER,
                        (_f(2, 4), _f(3, 4)),  # every pair used, so they come round again
                        MORE_OR_LESS,
                        _compare_line(4),
                        LESS,
                    ),
                    FreeResponse(),
                ),
                Question(
                    CompareQuestionData(
                        BIKE,
                        ("Ana", "Ben"),
                        KILOMETER,
                        (_f(3, 4), _f(2, 4)),
                        MORE_OR_LESS,
                        _compare_line(4),
                        MORE,
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
    denominators: Sequence[int],
    styles: Sequence[FractionStyle],
    multiple_choice: bool,
    distinct_answers: bool,
    expected: list[FractionNumberLinesQuestion],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("core.fraction_number_lines.generator.NAMES", NAMES)
    choose_last(monkeypatch)
    reverse_shuffle(monkeypatch)
    sample_first(monkeypatch)
    random_always_returns(monkeypatch, drawn)

    questions = generate_fraction_number_lines_questions(
        count,
        question_types,
        denominators,
        styles=styles,
        multiple_choice=multiple_choice,
        distinct_answers=distinct_answers,
    )

    assert questions == expected


def _value(line: FractionLine) -> Fraction:
    """Return how far along a line its one point is, in wholes."""
    return Fraction(line.points[0].tick, line.parts)


def _compare_answer(data: CompareQuestionData) -> str:
    """Return the answer a compare story's distances give."""
    first_longer = data.distances[0].value > data.distances[1].value
    if data.compared is MORE_OR_LESS:
        return MORE if first_longer else LESS
    longer, shorter = data.names if first_longer else data.names[::-1]
    return longer if data.compared is FARTHER else shorter


def _true(comparison: Comparison) -> bool:
    """Return whether a comparison's symbol is right."""
    left, right = comparison.left.value, comparison.right.value
    return left > right if comparison.symbol == ">" else left < right


def _broken_question_rules(
    question: FractionNumberLinesQuestion, denominators: Sequence[int]
) -> list[str]:
    """Return the rules ``question``'s data breaks, as text, or none."""
    data = question.data
    broken = []
    match data:
        case NamePointQuestionData():
            if (data.line.points[0].tick, data.line.parts) != (
                data.answer.numerator,
                data.answer.denominator,
            ) or not 0 < data.answer.value < 1:
                broken.append(f"the point isn't at {data.answer}, below 1")
        case MarkPointQuestionData() | DivideQuestionData():
            fraction = data.fraction
            if data.answer != _point_at(fraction.denominator, fraction.numerator):
                broken.append(f"the answer doesn't mark {fraction}")
            if data.line.points or not 0 < fraction.value <= 1:
                broken.append("the line to mark has a point, or the fraction isn't up to 1")
            if isinstance(data, DivideQuestionData) and data.line.parts != 1:
                broken.append("the line to divide is divided")
        case DistanceQuestionData():
            if data.distance.denominator not in (2, 4, 8) or not 0 < data.distance.value < 1:
                broken.append(f"{data.distance} isn't in halves, fourths or eighths, below 1")
            if (
                data.answer.value != data.distance.value
                or data.answer.denominator != data.line.parts
            ):
                broken.append(f"{data.answer} isn't {data.distance} in the line's parts")
            points = [(point.tick, point.letter) for point in data.line.points]
            asked = [(data.answer.numerator, data.name[0])] if data.asked is HOW_FAR else []
            if points != asked:
                broken.append("the line's point isn't the asked point, or is shown when marked")
        case CompareQuestionData():
            first, second = data.distances
            if not first.denominator == second.denominator == data.line.parts in (4, 8):
                broken.append("the distances aren't in the line's fourths or eighths")
            if data.names[0][0] == data.names[1][0] or first == second:
                broken.append("the names share a letter, or the distances are the same")
            if data.answer != _compare_answer(data):
                broken.append(f"the story doesn't answer {data.answer}")
    fraction = (
        data.fraction
        if isinstance(data, MarkPointQuestionData | DivideQuestionData)
        else data.answer
    )
    if isinstance(fraction, UnreducedFraction) and fraction.denominator not in denominators:
        broken.append(f"{fraction} isn't over a denominator asked for")
    return broken


def _broken_choice_rules(question: FractionNumberLinesQuestion) -> list[str]:
    """Return the rules ``question``'s choices break, as text, or none."""
    data, response = question.data, question.response
    if not isinstance(response, MultipleChoice):
        return []
    broken = []
    options = response.options
    if len(options) != 4 or len(response.correct_indexes) != 1:
        return ["not four options with one correct"]
    correct = options[next(iter(response.correct_indexes))]
    match data:
        case NamePointQuestionData():
            values = [option.value for option in options if isinstance(option, UnreducedFraction)]
            right = NONE_OF_THESE if data.answer.value not in values else data.answer
            if correct != right or len(set(values)) != len(values):
                broken.append("the right choice isn't the answer, or values repeat")
        case MarkPointQuestionData():
            parts = data.line.parts
            points = [option for option in options if isinstance(option, Fraction)]
            right = data.fraction.value if data.fraction.value in points else NONE_OF_THESE
            if correct != right:
                broken.append("the right choice isn't the point")
            if any(abs(a - b) < LETTER_SPACING for a in points for b in points if a != b):
                broken.append("two lettered points are too close")
            for point in points:
                place = point * parts
                if place.denominator != 1 and abs(place - round(place)) < OFF_TICK_CLEARANCE:
                    broken.append("a point between ticks is too near one")
            on_ticks = [point for point in points if (point * parts).denominator == 1]
            if right != NONE_OF_THESE and len(on_ticks) < 2:
                broken.append("the right point is the only one on a tick")
        case DistanceQuestionData():
            values = [_value(option) for option in options if isinstance(option, FractionLine)]
            if not isinstance(correct, FractionLine) or _value(correct) != data.distance.value:
                broken.append("the right line's point isn't the distance")
            if len(set(values)) != 4:
                broken.append("two lines' points have the same value")
        case DivideQuestionData():
            if correct != data.answer:
                broken.append("the right line isn't the answer")
        case CompareQuestionData():
            if not isinstance(correct, Comparison) or (correct.word, _true(correct)) != (
                data.answer,
                True,
            ):
                broken.append("the right comparison isn't the answer's true one")
    return broken


def _broken_tile_rules(questions: Sequence[FractionNumberLinesQuestion]) -> list[str]:
    """Return the rules a tiles sheet breaks, as text, or none."""
    broken = []
    written = [
        q.data.answer
        for q in questions
        if isinstance(q.data, NamePointQuestionData | DistanceQuestionData | CompareQuestionData)
    ]
    pictures = [
        q.data.fraction.value for q in questions if isinstance(q.data, MarkPointQuestionData)
    ]
    values = Counter(
        [answer.value for answer in written if isinstance(answer, UnreducedFraction)] + pictures
    )
    if len(set(written)) < len(written) or any(values[value] > 1 for value in pictures):
        broken.append(f"answers repeat: {written}, {pictures}")
    if any(isinstance(q.data, DivideQuestionData) for q in questions):
        broken.append("a line to divide on a tiles sheet")
    compares = [q.data for q in questions if isinstance(q.data, CompareQuestionData)]
    words = [data.answer for data in compares if data.answer in (MORE, LESS)]
    if sorted(words) not in ([], [LESS, MORE]):
        broken.append(f"more and less don't come as a pair: {words}")
    in_compares = Counter(name for data in compares for name in data.names)
    for data in compares:
        if data.answer not in (MORE, LESS) and in_compares[data.answer] != 2:
            broken.append(f"{data.answer} isn't in exactly two compare questions")
    named = {q.data.name for q in questions if isinstance(q.data, DistanceQuestionData)}
    if named & set(in_compares):
        broken.append("a compare question's name is in another question")
    if len(compares) == 1:
        broken.append("a lone compare question")
    return broken


@pytest.mark.parametrize(
    ("question_types", "denominators", "multiple_choice", "distinct_answers", "count"),
    [
        (ALL_TYPES, (2, 3, 4, 6, 8), False, False, 12),
        (ALL_TYPES, (2, 3, 4, 6, 8), True, False, 12),
        (ALL_TYPES, (2, 3, 4, 6, 8), False, True, 12),
        (ALL_TYPES, tuple(range(2, 13)), True, False, 12),
        (ALL_TYPES, tuple(range(2, 1001)), False, False, 12),
        ((NAME, MARK), (2, 3), True, False, 12),  # halves and thirds: points between ticks
        ((MARK,), (12,), True, False, 12),  # twelfths: only ticks
        ((DISTANCE,), (2, 4, 8), True, False, 12),
        ((DISTANCE,), (2, 4, 8), False, True, 11),
        ((MARK, DISTANCE), (2, 4, 8), False, True, 12),
        ((COMPARE,), (4, 8), False, True, 11),  # pairs and a trio
        ((NAME, COMPARE), (2, 4), False, True, 12),  # 4 fractions, compare takes the rest
        ((DIVIDE, COMPARE), (4, 8), False, True, 2),
    ],
)
def test_questions_meet_the_rules(
    question_types: Sequence[QuestionType],
    denominators: Sequence[int],
    multiple_choice: bool,
    distinct_answers: bool,
    count: int,
) -> None:
    """
    Over 30 sheets, every question's line or story gives its answer, over a denominator asked
    for, distances in halves, fourths or eighths; its choices are four with one right, the
    answer or "None of these" when the answer isn't among them, no two lines or fractions of the
    same value, lettered points apart and clear of ticks, the right point never the only one on
    a tick. With distinct answers, no two written answers are the same, no line to find has
    another answer's value, no line is divided, and names come in pairs or trios that no other
    question uses, with more and less as a pair.
    """
    broken = []
    for _ in range(30):
        questions = generate_fraction_number_lines_questions(
            count,
            question_types,
            denominators,
            multiple_choice=multiple_choice,
            distinct_answers=distinct_answers,
        )
        for question in questions:
            broken += _broken_question_rules(question, denominators)
            broken += _broken_choice_rules(question)
            if multiple_choice != isinstance(question.response, MultipleChoice):
                broken.append("its response doesn't match the sheet")
        if distinct_answers:
            broken += _broken_tile_rules(questions)
        if len(questions) != count:
            broken.append(f"{len(questions)} questions, not {count}")
    assert broken == []


@pytest.mark.parametrize(
    ("question_types", "denominators", "expected"),
    [
        ((NAME,), (2, 3, 4, 6, 8), 18),  # every fraction below 1
        ((DISTANCE,), (2, 3, 4, 6, 8), 11),  # halves, fourths and eighths below 1
        ((MARK,), (2, 3, 4, 6, 8), 12),  # their values, 1 among them
        ((NAME, DISTANCE), (2, 3, 4, 6, 8), 18),  # the distances are among them
        ((NAME, MARK), (2, 4), 5),  # 1/2 and 2/4, 1/4, 3/4, and a line at 1
        ((MARK,), (10,), 0),  # too many parts for the answer bank
        ((DIVIDE,), (2, 3, 4), 0),  # left out of tiles
        ((DIVIDE, NAME), (2, 3, 4), 6),
        ((COMPARE,), (4, 8), len(BANK_NAMES)),  # one for each name, more than a sheet needs
        ((NAME, COMPARE), (2, 4), 4 + len(BANK_NAMES)),
    ],
)
def test_count_possible_answers(
    question_types: Sequence[QuestionType], denominators: Sequence[int], expected: int
) -> None:
    assert count_possible_answers(question_types, denominators) == expected


@pytest.mark.parametrize(
    ("question_types", "denominators", "distinct_answers", "expected"),
    [
        (ALL_TYPES, (2, 3, 4, 6, 8), False, []),
        (ALL_TYPES, (3, 6), False, [DISTANCE, COMPARE]),  # no halves, fourths or eighths
        (ALL_TYPES, (2,), False, [COMPARE]),  # halves have one point
        (ALL_TYPES, (13,), False, [NAME, MARK, DISTANCE, DIVIDE, COMPARE]),  # too many parts
        ((MARK,), (10,), False, []),
        ((MARK,), (10,), True, [MARK]),  # too many parts for the answer bank
        ((DIVIDE,), (13,), True, []),  # left out of tiles, not unaskable
    ],
)
def test_unaskable_types(
    question_types: Sequence[QuestionType],
    denominators: Sequence[int],
    distinct_answers: bool,
    expected: list[QuestionType],
) -> None:
    assert unaskable_types(question_types, denominators, distinct_answers) == expected


@pytest.mark.parametrize(
    ("count", "question_types", "denominators", "multiple_choice", "distinct_answers", "message"),
    [
        (
            2,
            (),
            (2, 4),
            False,
            False,
            "A question type, a denominator and a style are needed.",
        ),
        (
            2,
            ALL_TYPES,
            (2, 4),
            True,
            True,
            "Multiple-choice questions have no answers to keep distinct.",
        ),
        (
            2,
            (NAME, DISTANCE),
            (3,),
            False,
            False,
            "No question of type distance fits these settings.",
        ),
        (
            2,
            (DIVIDE,),
            (2, 4),
            False,
            True,
            "A self-check tiles sheet can't divide lines: no question has an answer.",
        ),
        (12, (DISTANCE,), (2, 4, 8), False, True, "At most 11 different answers, not 12."),
        (
            1,
            (COMPARE,),
            (4,),
            False,
            True,
            "Compare questions on a tiles sheet come at least two at a time.",
        ),
    ],
)
def test_generate_fraction_number_lines_questions_errors(
    count: int,
    question_types: Sequence[QuestionType],
    denominators: Sequence[int],
    multiple_choice: bool,
    distinct_answers: bool,
    message: str,
) -> None:
    with pytest.raises(ValueError) as error:
        generate_fraction_number_lines_questions(
            count,
            question_types,
            denominators,
            multiple_choice=multiple_choice,
            distinct_answers=distinct_answers,
        )
    assert str(error.value) == message
