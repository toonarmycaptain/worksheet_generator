"""
Tests for generating order of operations questions: the rules every question keeps, over many
real draws, as written, as multiple choice and on a self-check tiles sheet, and the requests the
generator refuses.
"""

from collections import Counter

import pytest

from core.arithmetic_expressions.data import Calculation, Expression, Number
from core.arithmetic_expressions.evaluation import allowed_paths, at, calculate, value
from core.arithmetic_expressions.mistakes import Mistake, mistaken_values
from core.arithmetic_expressions.random_expressions import (
    ExpressionLimits,
    NumberKind,
    numbers_in,
    written_levels,
)
from core.arithmetic_expressions.representation import is_grouped
from core.order_of_operations.data import (
    TILE_TYPES,
    FindErrorQuestionData,
    FirstChoice,
    FirstOperationQuestionData,
    FirstResultQuestionData,
    HasValueQuestionData,
    Improper,
    NextStepQuestionData,
    Order,
    OrderOfOperationsQuestion,
    Pair,
    ParenthesesQuestionData,
    QuestionType,
    SheetSettings,
    StepBlankQuestionData,
    Timing,
    ValueCountQuestionData,
    ValueQuestionData,
)
from core.order_of_operations.generator import (
    generate_order_of_operations_questions,
    tile_answers_limit,
)
from core.order_of_operations.representation import tile_answer
from core.question import FreeResponse, MultipleChoice

DRAWS = 60  # questions of each type in each case
SETTINGS = [
    SheetSettings(),
    SheetSettings(levels=(0, 1, 2), numbers=(NumberKind.DECIMAL,)),
    SheetSettings(numbers=(NumberKind.FRACTION,)),
    SheetSettings(levels=(0,), largest_number=10, largest_multiplier=2),
]
# Each type's data, as written or lettered, and in its tiles form
DATA_TYPES = {
    QuestionType.VALUE: (ValueQuestionData, ValueQuestionData),
    QuestionType.NEXT_STEP: (NextStepQuestionData, StepBlankQuestionData),
    QuestionType.HAS_VALUE: (HasValueQuestionData, ValueCountQuestionData),
    QuestionType.FIRST_OPERATION: (FirstOperationQuestionData, FirstResultQuestionData),
    QuestionType.PARENTHESES: (ParenthesesQuestionData, None),
    QuestionType.FIND_ERROR: (FindErrorQuestionData, None),
}


def _options(each: OrderOfOperationsQuestion) -> tuple[list[object], list[object]]:
    """Return a question's lettered choices and its correct ones, or none if it's written."""
    if not isinstance(each.response, MultipleChoice):
        return [], []
    options = list(each.response.options)
    return options, [options[index] for index in sorted(each.response.correct_indexes)]


def _first_pair(expression: Expression) -> Pair:
    """Return the only operation that may be worked first in ``expression``, as a pair."""
    (path,) = allowed_paths(expression)
    calculation = at(expression, path)
    assert isinstance(calculation, Calculation)
    assert isinstance(calculation.left, Number) and isinstance(calculation.right, Number)
    return Pair(calculation.left.value, calculation.operation, calculation.right.value)


def _only_group(expression: Expression) -> Pair:
    """Return the only group in ``expression``, two numbers, as a pair."""
    groups = [part for part in _parts(expression) if is_grouped(part)]
    (group,) = groups
    assert isinstance(group, Calculation)
    assert isinstance(group.left, Number) and isinstance(group.right, Number)
    return Pair(group.left.value, group.operation, group.right.value)


def _parts(expression: Expression) -> list[Expression]:
    """Return every part of ``expression``, itself included."""
    if isinstance(expression, Calculation):
        return [expression, *_parts(expression.left), *_parts(expression.right)]
    return [expression]


def _right(each: OrderOfOperationsQuestion) -> bool:
    """
    Return whether a question's answer is the one its expressions give, and its lettered choices
    are right or wrong as marked.
    """
    data = each.data
    options, correct = _options(each)
    match data:
        case ValueQuestionData():
            values = [
                option.value if isinstance(option, Improper) else option for option in options
            ]
            return data.answer == value(data.expression) and (
                not options or (values.count(data.answer), correct) == (1, [data.answer])
            )
        case NextStepQuestionData():
            same = [
                option
                for option in options
                if isinstance(option, Number | Calculation)
                and value(option) == value(data.expression)
            ]
            lines_right = all(value(line) == value(data.expression) for line in data.answer)
            return lines_right and same == correct
        case StepBlankQuestionData():
            part = at(data.step, data.blank)
            return isinstance(part, Number) and (part.value, value(data.step)) == (
                data.answer,
                value(data.expression),
            )
        case HasValueQuestionData():
            having = [each for each in data.expressions if value(each) == data.target]
            chosen = having == [data.answer] if data.has else data.answer not in having
            lacking = len(data.expressions) - len(having)
            return chosen and lacking == (3 if data.has else 1)
        case ValueCountQuestionData():
            return data.answer == sum(value(each) == data.target for each in data.expressions)
        case FirstOperationQuestionData():
            others = [
                option.pair
                for option in options
                if isinstance(option, FirstChoice) and option != data.answer
            ]
            first = _first_pair(data.expression)
            return data.answer.pair == first and first not in others
        case FirstResultQuestionData():
            first = _first_pair(data.expression)
            return (data.pair, data.answer) == (
                first,
                calculate(first.operation, first.left, first.right),
            )
        case ParenthesesQuestionData():
            inside = _only_group(data.expression)
            if isinstance(data.answer, Timing):
                return data.answer == Timing(inside, first=True)
            return isinstance(data.answer, Order) and data.answer.first == inside
        case FindErrorQuestionData():
            values = [value(line) for line in (data.expression, *data.steps)]
            changed = [step for step in range(1, len(values)) if values[step] != values[step - 1]]
            return changed[0] == data.answer.step and isinstance(data.steps[-1], Number)


@pytest.mark.parametrize("settings", SETTINGS)
@pytest.mark.parametrize("multiple_choice", [False, True])
@pytest.mark.parametrize("question_type", list(QuestionType))
def test_every_question_s_answer_is_right(
    question_type: QuestionType, multiple_choice: bool, settings: SheetSettings
) -> None:
    """
    Every question's answer is the one its expressions give, and its lettered choices are right
    or wrong as marked: one value, step, expression, operation or statement right, or two steps
    for select TWO; in a worked simplification, the first change of value is at its error.
    """
    questions = generate_order_of_operations_questions(
        DRAWS, [question_type], settings, multiple_choice=multiple_choice
    )
    assert [each for each in questions if not _right(each)] == []


@pytest.mark.parametrize(
    ("question_type", "expected"),
    [
        (QuestionType.VALUE, {(4, 1)}),
        # one equivalent expression, or two of five
        (QuestionType.NEXT_STEP, {(4, 1), (5, 2)}),
        (QuestionType.HAS_VALUE, {(4, 1)}),
        (QuestionType.FIRST_OPERATION, {(4, 1)}),
        (QuestionType.PARENTHESES, {(4, 1)}),
        (QuestionType.FIND_ERROR, {(4, 1)}),
    ],
)
def test_lettered_choices(question_type: QuestionType, expected: set[tuple[int, int]]) -> None:
    """Each lettered question has its number of different choices, and of correct ones."""
    questions = generate_order_of_operations_questions(DRAWS, [question_type], multiple_choice=True)
    shapes = set()
    for each in questions:
        options, correct = _options(each)
        shapes.add((len(set(options)), len(correct)))
    assert shapes == expected


def test_written_questions_have_no_choices() -> None:
    """Without multiple choice, every question is written, each of its type's written form."""
    questions = generate_order_of_operations_questions(12, list(QuestionType))
    assert Counter(
        (type(each.data), isinstance(each.response, FreeResponse)) for each in questions
    ) == {(written, True): 2 for written, _ in DATA_TYPES.values()}


@pytest.mark.parametrize("settings", SETTINGS)
def test_a_tiles_sheet_asks_tiles_forms_with_different_answers(settings: SheetSettings) -> None:
    """
    On a tiles sheet, the 12 questions are tiles forms, shared evenly among the types, written,
    and no two answers are the same.
    """
    questions = generate_order_of_operations_questions(
        12, list(TILE_TYPES), settings, distinct_answers=True
    )
    answers = {tile_answer(each.data) for each in questions}
    forms = Counter(type(each.data) for each in questions)
    assert (len(answers), forms) == (
        12,
        {DATA_TYPES[each][1]: 3 for each in TILE_TYPES},
    )


def test_how_many_have_the_value_alone_counts_0_to_4() -> None:
    """Alone on a tiles sheet, "How many have the value?" asks for each count once."""
    questions = generate_order_of_operations_questions(
        5, [QuestionType.HAS_VALUE], distinct_answers=True
    )
    assert sorted(tile_answer(each.data) for each in questions) == ["0", "1", "2", "3", "4"]


@pytest.mark.parametrize("multiple_choice", [False, True])
def test_wrong_expressions_reach_the_value_by_a_mistake(multiple_choice: bool) -> None:
    """
    Each expression without the value comes to it with its groups ignored, or worked left to
    right with its groups ignored.
    """
    questions = generate_order_of_operations_questions(
        DRAWS, [QuestionType.HAS_VALUE], multiple_choice=multiple_choice
    )
    misled = [
        target in mistaken_values(each, Mistake.GROUPS_IGNORED)
        or target in mistaken_values(each, Mistake.GROUPS_IGNORED_LEFT_TO_RIGHT)
        for question in questions
        if isinstance(question.data, HasValueQuestionData)
        for target in [question.data.target]
        for each in question.data.expressions
        if value(each) != target
    ]
    assert all(misled)


@pytest.mark.parametrize("settings", SETTINGS)
def test_expressions_keep_the_settings(settings: SheetSettings) -> None:
    """
    Each value question's expression nests its groups as deep as one of the levels ticked, and
    no number written in it is larger than the largest number.
    """
    questions = generate_order_of_operations_questions(DRAWS, [QuestionType.VALUE], settings)
    limits = ExpressionLimits(0, range(1, 6))
    kept = []
    for each in questions:
        assert isinstance(each.data, ValueQuestionData)
        numbers = [number.value for _, number in numbers_in(each.data.expression)]
        level = written_levels(each.data.expression, limits)
        kept.append(level in settings.levels and max(numbers) <= settings.largest_number)
    assert all(kept)


def test_every_step_can_hold_the_error() -> None:
    """Over many draws, each step of three or four, the last included, holds the error."""
    questions = generate_order_of_operations_questions(200, [QuestionType.FIND_ERROR])
    places = {
        (len(each.data.steps), each.data.answer.step)
        for each in questions
        if isinstance(each.data, FindErrorQuestionData)
    }
    assert places == {(3, 1), (3, 2), (3, 3), (4, 1), (4, 2), (4, 3), (4, 4)}


def test_a_sheet_repeats_no_question() -> None:
    """No two questions on a sheet are the same."""
    questions = generate_order_of_operations_questions(20, list(QuestionType))
    assert len({each.data for each in questions}) == 20


@pytest.mark.parametrize(
    ("question_types", "expected"),
    [
        ([QuestionType.HAS_VALUE], 5),
        ([QuestionType.HAS_VALUE, QuestionType.VALUE], None),
        (list(TILE_TYPES), None),
        # a type with no tiles form adds nothing
        ([QuestionType.HAS_VALUE, QuestionType.FIND_ERROR], 5),
    ],
)
def test_tile_answers_limit(question_types: list[QuestionType], expected: int | None) -> None:
    """Only "How many have the value?" alone limits a tiles sheet, to its counts 0 to 4."""
    assert tile_answers_limit(question_types) == expected


@pytest.mark.parametrize(
    ("question_types", "settings", "multiple_choice", "distinct_answers", "count", "message"),
    [
        ([], SheetSettings(), False, False, 1, "At least one question type is needed."),
        (
            [QuestionType.VALUE],
            SheetSettings(levels=()),
            False,
            False,
            1,
            "At least one level of grouping and one kind of number are needed.",
        ),
        (
            [QuestionType.VALUE],
            SheetSettings(),
            True,
            True,
            1,
            "Multiple-choice questions have no answers to keep distinct.",
        ),
        (
            [QuestionType.VALUE, QuestionType.FIND_ERROR],
            SheetSettings(),
            False,
            True,
            1,
            "These question types have no self-check tiles form: find_error.",
        ),
        (
            [QuestionType.HAS_VALUE],
            SheetSettings(),
            False,
            True,
            6,
            "Cannot make 6 questions with different answers: only 5 possible.",
        ),
    ],
)
def test_refused_requests(
    question_types: list[QuestionType],
    settings: SheetSettings,
    multiple_choice: bool,
    distinct_answers: bool,
    count: int,
    message: str,
) -> None:
    """A request the generator can't make is refused, saying why."""
    with pytest.raises(ValueError) as refused:
        generate_order_of_operations_questions(
            count,
            question_types,
            settings,
            multiple_choice=multiple_choice,
            distinct_answers=distinct_answers,
        )
    assert str(refused.value) == message
