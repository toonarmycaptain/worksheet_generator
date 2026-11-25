"""
Tests for the naming fractions question generator.

``test_questions`` scripts ``random``, so each case lists the questions that must be produced.
The names come from ``tests.data``, standing in for the bank, and these functions are replaced:

- ``random.shuffle`` reverses the list, so the question types are dealt from the last ticked, and
  a multiple-choice question's correct option is last, its wrong options in reverse.
- ``random.choice`` returns the last item: the largest denominator, then the last answer over it
  that isn't a whole (or the whole, when ``random.random`` lets it), the last way a story can
  have it, the last representation, split, story, object, noun and style, and the last place
  for side-by-side shading to start.
- ``random.sample`` takes the first items, so scattered shading is the first parts.
- ``random.random`` always returns the case's number: 0.0 makes every "one time in n" happen
  (wholes, names in stories, whole stories, scattered shading, dividing first, the answer as the
  choice of the most-repeated numbers), and 0.99 none of them.

``test_questions_meet_the_rules`` runs the generator for real and checks every question against
the rules it promises.
"""

from collections import Counter
from collections.abc import Sequence
from fractions import Fraction

import pytest

from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    PARALLELOGRAM,
    AreaModel,
    Circle,
    Grid,
    RadialPartition,
    RegularPolygon,
    equal_sizes,
    rectangle,
    striped,
)
from core.fraction_models.object_groups import ObjectGroup
from core.naming_fractions.data import (
    Asked,
    DrawSharesQuestionData,
    NameQuestionData,
    NamingFractionsQuestion,
    People,
    QuestionType,
    Representation,
    ShadeQuestionData,
    ShareQuestionData,
)
from core.naming_fractions.generator import (
    count_possible_answers,
    generate_naming_fractions_questions,
    unaskable_types,
)
from core.question import FreeResponse, MultipleChoice, Question
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.data import NAMES
from tests.helpers import choose_last, random_always_returns, reverse_shuffle, sample_first

NAME, SHADE, SHARE, DRAW_SHARES = QuestionType
STRIP, GRID, CIRCLE, OTHER_SHAPE, GROUP = Representation
STACKED, SLASH, SLANTED = FractionStyle
EACH, TOGETHER, LEFT = Asked
ALL_TYPES = (NAME, SHADE, SHARE, DRAW_SHARES)
ALL_REPRESENTATIONS = (STRIP, GRID, CIRCLE, OTHER_SHAPE, GROUP)
FRIENDS = ("friend", "friends")
SIXTHS = equal_sizes(6)


@pytest.mark.parametrize(
    (
        "case_name",
        "drawn",
        "count",
        "question_types",
        "representations",
        "denominators",
        "styles",
        "multiple_choice",
        "distinct_answers",
        "expected",
    ),
    [
        (
            # each type once, dealt from the last: the largest denominator, eighths, and the last
            # answer over it that isn't a whole; a group story, and groups of the last object
            "written",
            0.99,
            4,
            ALL_TYPES,
            ALL_REPRESENTATIONS,
            (2, 3, 4, 6, 8),
            (STACKED,),
            False,
            False,
            [
                Question(
                    DrawSharesQuestionData(
                        8,  # the wall, uncut
                        People(8, FRIENDS),
                        AreaModel(Grid(1, 1)),
                        TOGETHER,
                        7,
                        UnreducedFraction(7, 8),
                    ),
                    FreeResponse(),
                ),
                Question(
                    ShareQuestionData(
                        7,  # "{people} share {total} {objects} equally."
                        People(8, ("classmate", "classmates")),
                        DrawnObject.TROPHY,
                        8,
                        LEFT,
                        1,
                        ObjectGroup(DrawnObject.TROPHY, 8, 4),
                        UnreducedFraction(7, 8),
                    ),
                    FreeResponse(),
                ),
                Question(
                    ShadeQuestionData(
                        UnreducedFraction(7, 8),
                        ObjectGroup(DrawnObject.XYLOPHONE, 8, 4),
                        False,
                        ObjectGroup(DrawnObject.XYLOPHONE, 8, 4, frozenset(range(1, 8))),
                    ),
                    FreeResponse(),
                ),
                Question(
                    NameQuestionData(
                        ObjectGroup(DrawnObject.XYLOPHONE, 8, 4, frozenset(range(1, 8))),
                        False,
                        UnreducedFraction(7, 8),
                    ),
                    FreeResponse(),
                ),
            ],
        ),
        (
            # wholes, a story about "Eve and three friends" sharing a whole, the last style, and
            # four choices each; a shade question chooses from pictures
            "choices_every_time_in_n",
            0.0,
            4,
            ALL_TYPES,
            ALL_REPRESENTATIONS,
            (2, 3, 4),
            (STACKED, SLASH, SLANTED),
            True,
            False,
            [
                Question(
                    DrawSharesQuestionData(
                        8,
                        People(4, FRIENDS, ("Eve",)),
                        AreaModel(Grid(1, 1)),
                        TOGETHER,
                        3,
                        UnreducedFraction(3, 4, SLANTED),
                    ),
                    MultipleChoice(
                        (
                            UnreducedFraction(1, 3, SLANTED),  # 1 over the people asked
                            UnreducedFraction(4, 3, SLANTED),  # flipped
                            UnreducedFraction(3, 3, SLANTED),  # the cuts counted
                            UnreducedFraction(3, 4, SLANTED),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    ShareQuestionData(
                        8,  # the wall, cut in 4
                        People(4, FRIENDS, ("Eve",)),
                        None,
                        4,
                        LEFT,
                        1,
                        AreaModel(Grid(2, 2)),
                        UnreducedFraction(3, 4, SLANTED),
                    ),
                    MultipleChoice(
                        (
                            UnreducedFraction(2, 4, SLANTED),  # over the total, filling in
                            UnreducedFraction(3, 1, SLANTED),  # what's left over one share
                            UnreducedFraction(1, 4, SLANTED),  # one share, not what's left
                            UnreducedFraction(3, 4, SLANTED),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    ShadeQuestionData(
                        UnreducedFraction(4, 4, SLANTED),
                        ObjectGroup(DrawnObject.XYLOPHONE, 4, 4),
                        False,
                        ObjectGroup(DrawnObject.XYLOPHONE, 4, 4, frozenset(range(4))),
                    ),
                    MultipleChoice(
                        (
                            # one part less, the same number of 8, the unshaded parts counted as
                            # the whole: none, so 4 beside 1 more
                            ObjectGroup(DrawnObject.XYLOPHONE, 4, 4, frozenset(range(3))),
                            ObjectGroup(DrawnObject.XYLOPHONE, 5, 5, frozenset(range(4))),
                            ObjectGroup(DrawnObject.XYLOPHONE, 8, 4, frozenset(range(4))),
                            ObjectGroup(DrawnObject.XYLOPHONE, 4, 4, frozenset(range(4))),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    NameQuestionData(
                        ObjectGroup(DrawnObject.XYLOPHONE, 4, 4, frozenset(range(4))),
                        False,
                        UnreducedFraction(4, 4, SLANTED),
                    ),
                    MultipleChoice(
                        (
                            UnreducedFraction(4, 3, SLANTED),  # a part too few
                            UnreducedFraction(4, 5, SLANTED),  # a part too many
                            UnreducedFraction(1, 4, SLANTED),  # filling in
                            UnreducedFraction(4, 4, SLANTED),
                        ),
                        frozenset({3}),
                    ),
                ),
            ],
        ),
        (
            # strips and circles: a pizza story, and circles to choose from, one cut unequally
            "choices_strips_and_circles",
            0.99,
            4,
            ALL_TYPES,
            (STRIP, CIRCLE),
            (3, 6),
            (STACKED,),
            True,
            False,
            [
                Question(
                    DrawSharesQuestionData(
                        6,  # the pizza, uncut
                        People(6, ("teammate", "teammates")),
                        AreaModel(
                            RadialPartition(Circle(), equal_sizes(1)), look=DrawnObject.PIZZA
                        ),
                        TOGETHER,
                        5,
                        UnreducedFraction(5, 6),
                    ),
                    MultipleChoice(
                        (
                            UnreducedFraction(1, 5),
                            UnreducedFraction(6, 5),
                            UnreducedFraction(5, 5),
                            UnreducedFraction(5, 6),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    ShareQuestionData(
                        6,  # the pizza, cut in 6
                        People(6, ("teammate", "teammates")),
                        None,
                        6,
                        LEFT,
                        1,
                        AreaModel(RadialPartition(Circle(), SIXTHS), look=DrawnObject.PIZZA),
                        UnreducedFraction(5, 6),
                    ),
                    MultipleChoice(
                        (
                            UnreducedFraction(2, 6),
                            UnreducedFraction(5, 1),
                            UnreducedFraction(1, 6),
                            UnreducedFraction(5, 6),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    ShadeQuestionData(
                        UnreducedFraction(5, 6),
                        AreaModel(RadialPartition(Circle(), SIXTHS)),
                        False,
                        AreaModel(RadialPartition(Circle(), SIXTHS), frozenset(range(1, 6))),
                    ),
                    MultipleChoice(
                        (
                            AreaModel(
                                RadialPartition(
                                    Circle(),
                                    tuple(Fraction(size, 45) for size in (10, 9, 8, 7, 6, 5)),
                                ),
                                frozenset(range(1, 6)),
                            ),
                            AreaModel(
                                RadialPartition(Circle(), equal_sizes(11)), frozenset(range(6, 11))
                            ),
                            AreaModel(RadialPartition(Circle(), SIXTHS), frozenset({5})),
                            AreaModel(RadialPartition(Circle(), SIXTHS), frozenset(range(1, 6))),
                        ),
                        frozenset({3}),
                    ),
                ),
                Question(
                    NameQuestionData(
                        AreaModel(RadialPartition(Circle(), SIXTHS), frozenset(range(1, 6))),
                        False,
                        UnreducedFraction(5, 6),
                    ),
                    MultipleChoice(
                        (
                            UnreducedFraction(6, 5),
                            UnreducedFraction(5, 7),
                            UnreducedFraction(1, 6),
                            UnreducedFraction(5, 6),
                        ),
                        frozenset({3}),
                    ),
                ),
            ],
        ),
        (
            # tiles: distinct written answers, and a picture's value, 1, used by no written one
            "tiles",
            0.99,
            4,
            ALL_TYPES,
            ALL_REPRESENTATIONS,
            (2, 4),
            (STACKED,),
            False,
            True,
            [
                Question(
                    DrawSharesQuestionData(
                        8,
                        People(4, FRIENDS),
                        AreaModel(Grid(1, 1)),
                        TOGETHER,
                        3,
                        UnreducedFraction(3, 4),
                    ),
                    FreeResponse(),
                ),
                Question(
                    ShareQuestionData(
                        7,
                        People(4, ("classmate", "classmates")),
                        DrawnObject.TROPHY,
                        4,
                        EACH,
                        1,
                        ObjectGroup(DrawnObject.TROPHY, 4, 4),
                        UnreducedFraction(1, 4),
                    ),
                    FreeResponse(),
                ),
                Question(
                    ShadeQuestionData(
                        UnreducedFraction(4, 4),
                        ObjectGroup(DrawnObject.XYLOPHONE, 4, 4),
                        False,
                        ObjectGroup(DrawnObject.XYLOPHONE, 4, 4, frozenset(range(4))),
                    ),
                    FreeResponse(),
                ),
                Question(
                    NameQuestionData(
                        ObjectGroup(DrawnObject.XYLOPHONE, 4, 4, frozenset({2, 3})),
                        False,
                        UnreducedFraction(2, 4),
                    ),
                    FreeResponse(),
                ),
            ],
        ),
        (
            # grids and other shapes: a square to divide, and a parallelogram in stripes
            "written_every_time_in_n",
            0.0,
            4,
            ALL_TYPES,
            (GRID, OTHER_SHAPE),
            (4, 6),
            (STACKED,),
            False,
            False,
            [
                Question(
                    DrawSharesQuestionData(
                        8,
                        People(6, FRIENDS, ("Eve",)),
                        AreaModel(Grid(1, 1)),
                        TOGETHER,
                        5,
                        UnreducedFraction(5, 6),
                    ),
                    FreeResponse(),
                ),
                Question(
                    ShareQuestionData(
                        8,
                        People(6, FRIENDS, ("Eve",)),
                        None,
                        6,
                        LEFT,
                        1,
                        AreaModel(Grid(2, 3)),
                        UnreducedFraction(5, 6),
                    ),
                    FreeResponse(),
                ),
                Question(
                    ShadeQuestionData(
                        UnreducedFraction(6, 6),
                        AreaModel(RadialPartition(RegularPolygon(4), equal_sizes(1))),
                        True,
                        AreaModel(striped(rectangle(1, 1), 6), frozenset(range(6))),
                    ),
                    FreeResponse(),
                ),
                Question(
                    NameQuestionData(
                        AreaModel(striped(PARALLELOGRAM, 6, side=1), frozenset(range(6))),
                        False,
                        UnreducedFraction(6, 6),
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
    denominators: Sequence[int],
    styles: Sequence[FractionStyle],
    multiple_choice: bool,
    distinct_answers: bool,
    expected: list[NamingFractionsQuestion],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("core.naming_fractions.generator.NAMES", NAMES)
    choose_last(monkeypatch)
    reverse_shuffle(monkeypatch)
    sample_first(monkeypatch)
    random_always_returns(monkeypatch, drawn)

    questions = generate_naming_fractions_questions(
        count,
        question_types,
        representations,
        denominators,
        styles=styles,
        multiple_choice=multiple_choice,
        distinct_answers=distinct_answers,
    )

    assert questions == expected


def _parts_and_shaded(picture: AreaModel | ObjectGroup) -> tuple[int, int, bool]:
    """Return a picture's parts, how many are shaded, and whether its parts are equal."""
    if isinstance(picture, ObjectGroup):
        return picture.count, len(picture.shaded), True
    return picture.parts, len(picture.shaded), picture.split.equal_parts


def _broken_rules(
    question: NamingFractionsQuestion, denominators: Sequence[int], choices: bool
) -> list[str]:
    """Return the rules ``question`` breaks, as text, or none."""
    data, response = question.data, question.response
    broken = []
    if isinstance(data, ShadeQuestionData):
        fraction = data.fraction
        parts, shaded, equal = _parts_and_shaded(data.answer)
        if (shaded, parts, equal) != (fraction.numerator, fraction.denominator, True):
            broken.append(f"shaded picture isn't {fraction}")
        if _parts_and_shaded(data.picture)[1] != 0:
            broken.append("the picture to shade has shading")
    else:
        fraction = data.answer
    if fraction.denominator not in denominators or not 0 < fraction.value <= 1:
        broken.append(f"{fraction} isn't a fraction up to 1 over a denominator asked for")
    if isinstance(data, NameQuestionData):
        parts, shaded, _ = _parts_and_shaded(data.picture)
        named = parts - shaded if data.unshaded else shaded
        if (named, parts) != (fraction.numerator, fraction.denominator):
            broken.append(f"the picture doesn't show {fraction}")
    if isinstance(data, ShareQuestionData):
        share = data.total // data.people.count
        expected = {EACH: share, TOGETHER: data.together * share, LEFT: data.total - share}
        if data.total % data.people.count or fraction.numerator != expected[data.asked]:
            broken.append(f"the story doesn't give {fraction}")
    if isinstance(data, DrawSharesQuestionData):
        expected = {EACH: 1, TOGETHER: data.together}
        if (expected[data.asked], data.people.count) != (fraction.numerator, fraction.denominator):
            broken.append(f"the story doesn't give {fraction}")
    if choices != isinstance(response, MultipleChoice):
        broken.append("its response doesn't match the sheet")
    if isinstance(response, MultipleChoice):
        options = response.options
        if len(options) != 4 or len(response.correct_indexes) != 1:
            broken.append("not four options with one correct")
        correct = options[next(iter(response.correct_indexes))]
        if correct != (data.answer if isinstance(data, ShadeQuestionData) else fraction):
            broken.append("the correct option isn't the answer")
        values = (
            [
                Fraction(shaded, parts) if equal else None
                for parts, shaded, equal in map(_parts_and_shaded, options)
            ]
            if isinstance(data, ShadeQuestionData)
            else [option.value for option in options]
        )
        if values.count(fraction.value) != 1:
            broken.append("another option shows the answer's value")
    return broken


@pytest.mark.parametrize(
    (
        "question_types",
        "representations",
        "denominators",
        "multiple_choice",
        "distinct_answers",
        "count",
    ),
    [
        (ALL_TYPES, ALL_REPRESENTATIONS, (2, 3, 4, 6, 8), False, False, 12),
        (ALL_TYPES, ALL_REPRESENTATIONS, (2, 3, 4, 6, 8), True, False, 12),
        (ALL_TYPES, ALL_REPRESENTATIONS, (2, 3, 4, 6, 8), False, True, 12),
        (ALL_TYPES, ALL_REPRESENTATIONS, tuple(range(2, 21)), True, False, 12),
        (ALL_TYPES, ALL_REPRESENTATIONS, tuple(range(2, 1001)), False, False, 12),
        (ALL_TYPES, (STRIP,), (2, 3, 4, 6, 8), True, False, 12),
        (ALL_TYPES, (OTHER_SHAPE,), (2, 3, 4, 6, 8, 12), True, False, 12),
        ((NAME, SHADE, SHARE), (GROUP,), (2, 3, 4, 6, 8), True, False, 12),
        ((SHADE,), ALL_REPRESENTATIONS, (2, 3, 4, 6, 8), False, True, 12),
        ((NAME, SHADE), ALL_REPRESENTATIONS, (2, 4), False, True, 6),
        ((SHARE, DRAW_SHARES), (GRID,), (5, 7), True, False, 12),
    ],
)
def test_questions_meet_the_rules(
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    denominators: Sequence[int],
    multiple_choice: bool,
    distinct_answers: bool,
    count: int,
) -> None:
    """
    Over 30 sheets, every question has a fraction up to 1 over a denominator asked for, its
    picture or story gives its answer, and its choices are four with one correct, the answer,
    whose value no other option has. With distinct answers, no two written answers are the same
    and no picture's value is any other answer's.
    """
    broken = []
    for _ in range(30):
        questions = generate_naming_fractions_questions(
            count,
            question_types,
            representations,
            denominators,
            multiple_choice=multiple_choice,
            distinct_answers=distinct_answers,
        )
        for question in questions:
            broken += _broken_rules(question, denominators, multiple_choice)
        written = [q.data.answer for q in questions if not isinstance(q.data, ShadeQuestionData)]
        pictures = [
            q.data.fraction.value for q in questions if isinstance(q.data, ShadeQuestionData)
        ]
        values = Counter([answer.value for answer in written] + pictures)
        clash = len(set(written)) < len(written) or any(values[value] > 1 for value in pictures)
        if distinct_answers and clash:
            broken.append(f"answers repeat on a tiles sheet: {written}, {pictures}")
    assert broken == []


@pytest.mark.parametrize(
    ("question_types", "representations", "denominators", "expected"),
    [
        (ALL_TYPES, ALL_REPRESENTATIONS, (2, 3, 4, 6, 8), 23),  # every fraction as written
        ((SHADE,), ALL_REPRESENTATIONS, (2, 3, 4, 6, 8), 12),  # their values
        ((SHARE,), ALL_REPRESENTATIONS, (2, 3, 4, 6, 8), 18),  # every one below 1
        ((DRAW_SHARES,), ALL_REPRESENTATIONS, (2, 3, 4, 6, 8), 18),
        ((NAME, SHADE), ALL_REPRESENTATIONS, (2, 4), 6),
        ((SHADE,), ALL_REPRESENTATIONS, (2, 4), 4),
        ((SHADE, SHARE), ALL_REPRESENTATIONS, (2, 3), 4),  # 1/2, 1/3, 2/3 and a picture of 1
        ((SHADE,), ALL_REPRESENTATIONS, (5, 7), 11),  # 5/5 and 7/7 are both 1
        ((SHADE,), (GRID,), (2, 3), 0),  # no grid of 2 or 3 parts
        ((SHADE,), ALL_REPRESENTATIONS, (13,), 0),  # too many parts for a tiles bank
        ((DRAW_SHARES,), (GROUP,), (2, 3, 4), 0),  # a group isn't cut
    ],
)
def test_count_possible_answers(
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    denominators: Sequence[int],
    expected: int,
) -> None:
    assert count_possible_answers(question_types, representations, denominators) == expected


@pytest.mark.parametrize(
    ("question_types", "representations", "denominators", "distinct_answers", "expected"),
    [
        (ALL_TYPES, ALL_REPRESENTATIONS, (2, 3, 4, 6, 8), False, []),
        (ALL_TYPES, (GROUP,), (2, 3, 4, 6, 8), False, [DRAW_SHARES]),
        (ALL_TYPES, ALL_REPRESENTATIONS, (11,), False, [SHARE, DRAW_SHARES]),
        (ALL_TYPES, (GRID,), (5, 7), False, [NAME, SHADE]),
        (ALL_TYPES, ALL_REPRESENTATIONS, (50,), False, [NAME, SHADE, DRAW_SHARES]),
        ((SHADE,), (STRIP,), (13,), False, []),
        ((SHADE,), (STRIP,), (13,), True, [SHADE]),  # too many parts for a tiles bank
        ((SHARE,), (STRIP,), (50,), False, [SHARE]),  # a banner of 50 can't be drawn
    ],
)
def test_unaskable_types(
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    denominators: Sequence[int],
    distinct_answers: bool,
    expected: list[QuestionType],
) -> None:
    assert (
        unaskable_types(question_types, representations, denominators, distinct_answers) == expected
    )


@pytest.mark.parametrize(
    (
        "count",
        "question_types",
        "representations",
        "multiple_choice",
        "distinct_answers",
        "message",
    ),
    [
        (
            2,
            (),
            ALL_REPRESENTATIONS,
            False,
            False,
            "A question type, a representation, a denominator and a style are needed.",
        ),
        (
            2,
            ALL_TYPES,
            ALL_REPRESENTATIONS,
            True,
            True,
            "Multiple-choice questions have no answers to keep distinct.",
        ),
        (
            2,
            (NAME, DRAW_SHARES),
            (GROUP,),
            False,
            False,
            "No question of type draw_shares fits these settings.",
        ),
        (5, (SHADE,), ALL_REPRESENTATIONS, False, True, "At most 4 different answers, not 5."),
    ],
)
def test_generate_naming_fractions_questions_errors(
    count: int,
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    multiple_choice: bool,
    distinct_answers: bool,
    message: str,
) -> None:
    with pytest.raises(ValueError) as error:
        generate_naming_fractions_questions(
            count,
            question_types,
            representations,
            (2, 4),
            multiple_choice=multiple_choice,
            distinct_answers=distinct_answers,
        )
    assert str(error.value) == message
