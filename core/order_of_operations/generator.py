"""
Random generation of order of operations questions: STAAR's ways of asking, written or as
multiple choice, and on a self-check tiles sheet, forms whose answer is a number the question
doesn't print. Wrong choices come from the common mistakes in
``core.arithmetic_expressions.mistakes``.
"""

import random
from collections.abc import Callable, Iterable, Sequence
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from itertools import pairwise

from core.arithmetic_expressions.data import (
    Calculation,
    Expression,
    Grouping,
    Number,
    NumberValue,
)
from core.arithmetic_expressions.evaluation import (
    Path,
    allowed_paths,
    at,
    calculate,
    replaced,
    step,
    steps,
    value,
    worked,
)
from core.arithmetic_expressions.mistakes import Mistake, mistaken_steps, mistaken_values
from core.arithmetic_expressions.random_expressions import (
    ExpressionLimits,
    NumberKind,
    combine,
    fill,
    numbers_in,
    random_expression,
    random_shape,
    with_numbers,
    within,
    written_levels,
)
from core.arithmetic_expressions.representation import (
    expression_pieces,
    expression_text,
    is_grouped,
    is_ungrouped,
)
from core.basic_operations.data import Operation
from core.order_of_operations.data import (
    TILE_TYPES,
    ErrorChoice,
    FindErrorQuestionData,
    FirstChoice,
    FirstOperationQuestionData,
    FirstResultQuestionData,
    GroupSymbols,
    HasValueQuestionData,
    Improper,
    NextStepQuestionData,
    Order,
    OrderOfOperationsQuestion,
    Pair,
    ParenthesesQuestionData,
    QuestionType,
    SheetSettings,
    Statement,
    StepBlankQuestionData,
    Then,
    Timing,
    ValueCountQuestionData,
    ValueOption,
    ValueQuestionData,
    Why,
)
from core.order_of_operations.representation import tile_answer
from core.question import FreeResponse, MultipleChoice, Question, multiple_choice

# How many operations an expression has, by how deeply its groups nest, as STAAR's do
OPERATIONS = {0: range(2, 5), 1: range(2, 5), 2: range(3, 6)}
# Four expressions are shown at once, so they're short, as STAAR's are
HAS_VALUE_OPERATIONS = {1: range(2, 4), 2: range(3, 4)}
# Enough for wrong first operations, three or four steps, or two equivalent expressions
LONG_OPERATIONS = range(3, 6)
PARENTHESES_OPERATIONS = range(3, 5)  # one group of two numbers, two operations or more outside
FRACTION_SHARE = 1 / 10  # the chance a problem has a fraction, when other kinds are ticked too
DECIMAL_SHARE = 1 / 3  # the chance a problem has decimals, when whole numbers are ticked too
WRONG_OPTIONS = 3  # beside each correct option
HAS_VALUE_SHOWN = 4  # expressions to choose from, or count
STEP_COUNTS = (3, 4)  # steps in a worked simplification with an error
TOGETHER_SHARE = 1 / 3  # the chance a step works every operation that may be worked next
FINISH_SHARE = 1 / 2  # the chance a step works out a line of two operations at once
RIGHT_STEP_WRONG_REASON_SHARE = 1 / 2  # a wrong choice naming the error's step, with a wrong reason
PAIR_CLAIM_SHARE = 2 / 3  # a wrong reason says a pair should come first, else a pair's value
TRIES = 300  # draws for a question that fits before giving up
DISTINCT_TRIES = 50  # draws for a question that doesn't repeat one already on the sheet
# shapes drawn for an expression with a given value before drawing another value, which may be
# easier to reach
TARGET_TRIES = 30
HAS_VALUE_COUNTS = range(HAS_VALUE_SHOWN + 1)  # how many of the expressions can have the value
HAS_VALUE = QuestionType.HAS_VALUE

# Mistakes a step of working can show with a reason: an operation that should have come first
ORDER_MISTAKES = (
    Mistake.GROUPS_IGNORED_LEFT_TO_RIGHT,
    Mistake.GROUPS_IGNORED,
    Mistake.LEFT_TO_RIGHT,
    Mistake.FIRST_NUMBER_MULTIPLIED,
)
# Slips in a calculation's numbers, whose reason is the calculation's value
SLIPS = (Mistake.DECIMAL_PARTS_LEFT_OUT, Mistake.WHOLE_NUMBER_IN_NUMERATOR)
DEFAULT_SETTINGS = SheetSettings()
_FIRST = (Operation.MULTIPLY, Operation.DIVIDE)
_ADDING = (Operation.ADD, Operation.SUBTRACT)


def generate_order_of_operations_questions(
    count: int,
    question_types: Sequence[QuestionType],
    settings: SheetSettings = DEFAULT_SETTINGS,
    *,
    multiple_choice: bool = False,
    distinct_answers: bool = False,
) -> list[OrderOfOperationsQuestion]:
    """
    Generate ``count`` questions, shared evenly among ``question_types``, then shuffled, with
    expressions within ``settings``. No question repeats one already on the sheet unless the
    settings leave no other.

    Each is written, or with ``multiple_choice``, has lettered choices. With
    ``distinct_answers``, as the self-check tiles case needs, each is written in its tiles form
    (see ``_tile_question``) and no two answers are the same. "How many have the value?" can
    only have 0 to 4, so once those run out its place goes to the next ticked type that has a
    tiles form.

    Raises ``ValueError`` if ``question_types`` or ``settings.levels`` or ``settings.numbers``
    is empty, if both ``multiple_choice`` and ``distinct_answers`` are given, if
    ``distinct_answers`` is given with a type not in ``TILE_TYPES``, or if it asks for more
    questions than ``tile_answers_limit`` allows.
    """
    if not question_types:
        raise ValueError("At least one question type is needed.")
    if not settings.levels or not settings.numbers:
        raise ValueError("At least one level of grouping and one kind of number are needed.")
    if multiple_choice and distinct_answers:
        raise ValueError("Multiple-choice questions have no answers to keep distinct.")
    types = [question_types[index % len(question_types)] for index in range(count)]
    random.shuffle(types)
    draw = _Draw(settings)
    if distinct_answers:
        return _tile_questions(types, question_types, draw, count)
    questions: list[OrderOfOperationsQuestion] = []
    for question_type in types:
        question = _question(question_type, draw, multiple_choice)
        for _ in range(DISTINCT_TRIES):
            if question.data not in (each.data for each in questions):
                break
            question = _question(question_type, draw, multiple_choice)
        questions.append(question)
    return questions


def tile_answers_limit(question_types: Sequence[QuestionType]) -> int | None:
    """
    Return the most questions with different answers the tiles forms of ``question_types`` can
    make, or ``None`` when that's more than any sheet asks: "How many have the value?" alone can
    only have 0 to 4, and every other tiles form gives a number from an expression.
    """
    if set(question_types) & set(TILE_TYPES) == {QuestionType.HAS_VALUE}:
        return len(HAS_VALUE_COUNTS)
    return None


class _Draw:
    """Drawing each problem's level of grouping, kind of number and group symbols from settings."""

    def __init__(self, settings: SheetSettings) -> None:
        self.settings = settings

    def level(self, grouped: bool = False) -> int:
        """
        Return a level of grouping from the settings', each with even chance; with ``grouped``,
        only those with a group, or 1 if there are none.
        """
        levels = [level for level in self.settings.levels if level or not grouped]
        return random.choice(levels or [1])

    def kind(self) -> NumberKind:
        """
        Return a kind of number from the settings': fractions in about ``FRACTION_SHARE`` of
        problems, decimals in about ``DECIMAL_SHARE`` of the rest, when whole numbers are ticked
        too.
        """
        numbers = self.settings.numbers
        others = [kind for kind in numbers if kind is not NumberKind.FRACTION]
        if NumberKind.FRACTION in numbers and (not others or random.random() < FRACTION_SHARE):
            return NumberKind.FRACTION
        if NumberKind.DECIMAL in others and (
            NumberKind.WHOLE not in others or random.random() < DECIMAL_SHARE
        ):
            return NumberKind.DECIMAL
        return NumberKind.WHOLE

    def brackets(self) -> bool:
        """Return whether a problem writes a group with a group inside in brackets."""
        match self.settings.symbols:
            case GroupSymbols.BRACKETS:
                return True
            case GroupSymbols.PARENTHESES:
                return False
            case GroupSymbols.MIXED:
                return random.random() < 1 / 2

    def limits(
        self,
        level: int,
        operations: range,
        kind: NumberKind | None = None,
        sign_before_implied: bool = False,
    ) -> ExpressionLimits:
        """Return an expression's limits: ``level``, ``operations``, and the settings' others."""
        return ExpressionLimits(
            levels=level,
            operations=operations,
            numbers=kind or self.kind(),
            largest_number=self.settings.largest_number,
            largest_multiplier=self.settings.largest_multiplier,
            implied=self.settings.implied,
            sign_before_implied=sign_before_implied,
        )


def _question(question_type: QuestionType, draw: _Draw, choices: bool) -> OrderOfOperationsQuestion:
    """Make a question of ``question_type``, with lettered choices if ``choices`` is set."""
    # drawn once, not per try, so the expressions a rank or step rules out don't skew them
    rank = random.randrange(WRONG_OPTIONS + 1)
    total = random.choice(STEP_COUNTS)
    error = random.randint(1, total)
    makers: dict[QuestionType, Callable[[], OrderOfOperationsQuestion | None]] = {
        QuestionType.VALUE: lambda: _value_question(draw, choices, rank),
        QuestionType.NEXT_STEP: lambda: _next_step_question(draw, choices),
        QuestionType.HAS_VALUE: lambda: _has_value_question(draw, choices),
        QuestionType.FIRST_OPERATION: lambda: _first_operation_question(draw, choices),
        QuestionType.PARENTHESES: lambda: _parentheses_question(draw, choices),
        QuestionType.FIND_ERROR: lambda: _find_error_question(draw, choices, total, error),
    }
    return _first_made(makers[question_type])


def _first_made(make: Callable[[], OrderOfOperationsQuestion | None]) -> OrderOfOperationsQuestion:
    """
    Return the first question ``make`` makes in ``TRIES`` draws; it returns ``None`` when the
    expression it drew can't ask its question. Raises ``ValueError`` if none is made.
    """
    for _ in range(TRIES):
        question = make()
        if question is not None:
            return question
    raise ValueError("No question of this type fits these settings.")


def _value_question(draw: _Draw, choices: bool, rank: int = 0) -> OrderOfOperationsQuestion | None:
    """
    Make a question asking for an expression's value. With ``choices``, the wrong values are
    those the mistakes come to, one from each of three mistakes where they can be, and ``rank``
    of them below the answer, so the answer is as likely to be the smallest choice as the
    largest: most mistakes leave something out, so they'd mostly be smaller. ``None`` if the
    expression's mistakes can't give the answer that rank.
    """
    level = draw.level()
    limits = draw.limits(level, OPERATIONS[level])
    expression = random_expression(limits)
    answer = value(expression)
    data = ValueQuestionData(expression, draw.brackets(), answer)
    if not choices:
        return Question(data, FreeResponse())
    wrong = _wrong_values(expression, answer, limits.numbers)
    below = [each for each in wrong if _option_value(each) < answer][:rank]
    above = [each for each in wrong if _option_value(each) > answer][: WRONG_OPTIONS - rank]
    if len(below) + len(above) < WRONG_OPTIONS:
        return None
    return Question(data, multiple_choice((answer,), (*below, *above)))


def _next_step_question(
    draw: _Draw, choices: bool, two: bool | None = None
) -> OrderOfOperationsQuestion | None:
    """
    Make a question asking for an equivalent expression: with even chance, unless ``two`` says,
    one or two of them.

    One: written, the next step, which may work one operation or all those that may be worked
    next; with ``choices``, either of those against three wrong steps. Two: five expressions to
    circle or choose from, the next step and a later line of the working, and three wrong steps.
    Wrong steps are those the mistakes write from the expression, or from its next step, as
    STAAR's 35 x 8 is from 28 + 7 x 8.
    """
    two = random.random() < 1 / 2 if two is None else two
    level = draw.level()
    limits = draw.limits(level, LONG_OPERATIONS if two else OPERATIONS[level])
    expression = random_expression(limits)
    brackets = draw.brackets()
    accepted = tuple(dict.fromkeys((step(expression), step(expression, together=True))))
    wrong = _wrong_steps(expression, limits, brackets)
    if not two:
        data = NextStepQuestionData(expression, brackets, accepted)
        if not choices:
            return Question(data, FreeResponse())
        if len(wrong) < WRONG_OPTIONS:
            return None
        correct = random.choice(accepted)
        chosen = wrong[:WRONG_OPTIONS]
        # the wrong steps can come from the step after, so they may have fewer operations left;
        # the right one mustn't be the only one with the most
        if _operation_count(correct) > max(_operation_count(each) for each in chosen):
            return None
        return Question(data, multiple_choice((correct,), tuple(chosen)))
    first = random.choice(accepted)
    later = [line for line in steps(first) if isinstance(line, Calculation)]
    if not later or len(wrong) < WRONG_OPTIONS:
        return None
    lines: tuple[Expression, ...] = (first, random.choice(later))
    shown = [*lines, *wrong[:WRONG_OPTIONS]]
    random.shuffle(shown)
    data = NextStepQuestionData(expression, brackets, lines, tuple(shown))
    if not choices:
        return Question(data, FreeResponse())
    indexes = frozenset(index for index, each in enumerate(shown) if each in lines)
    return Question(data, MultipleChoice(tuple(shown), indexes))


def _has_value_question(
    draw: _Draw, choices: bool, count: int | None = None
) -> OrderOfOperationsQuestion | None:
    """
    Make a question about which of four expressions has a value, drawn as some expression's
    value is. With even chance it asks which has it, the others coming to it only by a common
    mistake, or which does NOT, the one coming to it only by a mistake (see ``_misleading``).
    With ``count``, for self-check tiles, it asks how many have it, and ``count`` of them do.
    Each expression has a group, so it has one to mistake.
    """
    level = draw.level(grouped=True)
    limits = draw.limits(level, HAS_VALUE_OPERATIONS[level])
    target = value(random_expression(limits))
    has = random.random() < 1 / 2
    having = count if count is not None else (1 if has else HAS_VALUE_SHOWN - 1)
    try:
        right = [random_expression(limits, target, TARGET_TRIES) for _ in range(having)]
    except ValueError:
        return None
    misleading = [_misleading(limits, target) for _ in range(HAS_VALUE_SHOWN - having)]
    wrong = [each for each in misleading if each is not None]
    shown = [*right, *wrong]
    if len(wrong) < len(misleading) or len(set(shown)) < HAS_VALUE_SHOWN:
        return None
    random.shuffle(shown)
    brackets = draw.brackets()
    if count is not None:
        return Question(
            ValueCountQuestionData(tuple(shown), target, brackets, count), FreeResponse()
        )
    answer = right[0] if has else wrong[0]
    data = HasValueQuestionData(tuple(shown), target, has, brackets, answer)
    if not choices:
        return Question(data, FreeResponse())
    return Question(data, MultipleChoice(tuple(shown), frozenset({shown.index(answer)})))


def _misleading(limits: ExpressionLimits, target: NumberValue) -> Expression | None:
    """
    Return an expression within ``limits`` whose value isn't ``target`` but which comes to it
    with its groups ignored, or with even chance, worked left to right with its groups ignored,
    as STAAR's (36 - 3) x 4 comes to 24 and 100 ÷ (2 ÷ 2) to 25. Its numbers are drawn so the
    expression without its groups has that value, then the groups put back. ``None`` if no
    such expression was found.
    """
    for _ in range(TARGET_TRIES):
        shape = random_shape(limits)
        placeholders = [number for _, number in numbers_in(shape)]
        signs = [(operation, False) for operation, _ in _signs(shape)]
        left_to_right = random.random() < 1 / 2
        flat = (
            _left_to_right(placeholders, signs) if left_to_right else combine(placeholders, signs)
        )
        filled = fill(flat, limits, target)
        if filled is None:
            continue
        candidate = with_numbers(shape, [number.value for _, number in numbers_in(filled)])
        mistake = Mistake.GROUPS_IGNORED_LEFT_TO_RIGHT if left_to_right else Mistake.GROUPS_IGNORED
        if (
            within(candidate, limits)
            and written_levels(candidate, limits) == limits.levels
            and target in mistaken_values(candidate, mistake)
        ):
            return candidate
    return None


def _first_operation_question(
    draw: _Draw, choices: bool, result: bool = False
) -> OrderOfOperationsQuestion | None:
    """
    Make a question asking which operation is performed first, and why, of an expression with
    only one operation that can be first. With ``result``, for self-check tiles, it asks what
    number that operation gives instead.

    The wrong choices, each a pair of numbers written next to each other other than the right
    one, are as STAAR's: the first pair reading left to right, and the first reading right to
    left; a multiplication or division "because multiplication should be performed before
    addition", which ignores the groups; and the misreadings that multiplication comes before
    division, or addition before subtraction, wherever one follows the other.
    """
    level = draw.level()
    expression = random_expression(draw.limits(level, LONG_OPERATIONS))
    paths = allowed_paths(expression)
    if len(paths) != 1:
        return None
    first = _pair_at(expression, paths[0])
    brackets = draw.brackets()
    if result:
        answer = calculate(first.operation, first.left, first.right)
        data = FirstResultQuestionData(expression, brackets, first, answer)
        return Question(data, FreeResponse())
    correct = FirstChoice(first, _why_first(expression, paths[0], brackets))
    data_first = FirstOperationQuestionData(expression, brackets, correct)
    if not choices:
        return Question(data_first, FreeResponse())
    wrong = _wrong_first_choices(expression, correct, brackets)
    if len(wrong) < WRONG_OPTIONS:
        return None
    # a wrong choice with the right choice's reason, where there is one, so the reason alone
    # doesn't pick it out: STAAR's one item has none, and only its right one names parentheses
    alike = [choice for choice in wrong if choice.why is correct.why]
    rest = [choice for choice in wrong if choice.why is not correct.why]
    chosen = random.sample(alike, 1) if alike else []
    chosen += random.sample(rest, min(len(rest), WRONG_OPTIONS - len(chosen)))
    if len(chosen) < WRONG_OPTIONS:
        return None
    return Question(data_first, multiple_choice((correct,), tuple(chosen)))


def _why_first(expression: Expression, path: Path, brackets: bool) -> Why:
    """
    Return why the operation at ``path`` is performed first: it's in a group, whose symbols are
    named; else x and ÷ come before + and - when both are in the expression; else it's the first
    reading left to right.
    """
    for end in range(len(path), -1, -1):
        part = at(expression, path[:end])
        if is_grouped(part):
            if part.grouping is Grouping.BRACKETS and brackets:
                return Why.IN_BRACKETS
            return Why.IN_PARENTHESES
    operations = {operation for operation, _ in _signs(expression)}
    if _pair_at(expression, path).operation in _FIRST and operations & set(_ADDING):
        return Why.MULTIPLYING_FIRST
    return Why.LEFT_TO_RIGHT


def _wrong_first_choices(
    expression: Expression, correct: FirstChoice, brackets: bool
) -> list[FirstChoice]:
    """
    Return the wrong choices ``_first_operation_question`` describes, one per pair, each with a
    reason it has, the right choice's reason first where a pair has it. A pair across a group's
    edge, such as 4 x 72 in 4(72 - 6), is said to be in the group.
    """
    first = correct.pair
    pairs = [pair for pair, _ in _pairs(expression)]
    numbers = numbers_in(expression)
    candidates = [
        FirstChoice(pairs[0], Why.LEFT_TO_RIGHT),
        FirstChoice(pairs[-1], Why.RIGHT_TO_LEFT),
    ]
    for index, (pair, own) in enumerate(_pairs(expression)):
        touched = _touched_group(expression, numbers[index][0], numbers[index + 1][0], brackets)
        if own is None and touched is not None:
            candidates.append(FirstChoice(pair, touched))
    adding = [pair.operation for pair in pairs if pair.operation in _ADDING]
    multiplying = [pair for pair in pairs if pair.operation in _FIRST]
    if adding and multiplying:
        candidates.append(FirstChoice(multiplying[0], Why.BEFORE, adding[0]))
        # the rule, true, of a x or ÷ that isn't first: a group's, or one to its left, is
        candidates += [FirstChoice(pair, Why.MULTIPLYING_FIRST) for pair in multiplying]
    for index, pair in enumerate(pairs):
        earlier = {each.operation for each in pairs[:index]}
        if pair.operation is Operation.MULTIPLY and Operation.DIVIDE in earlier:
            candidates.append(FirstChoice(pair, Why.BEFORE, Operation.DIVIDE))
        if pair.operation is Operation.ADD and Operation.SUBTRACT in earlier:
            candidates.append(FirstChoice(pair, Why.BEFORE, Operation.SUBTRACT))
    random.shuffle(candidates)
    candidates.sort(key=lambda candidate: candidate.why is not correct.why)
    found: dict[Pair, FirstChoice] = {}
    for candidate in candidates:
        if candidate.pair != first and candidate.pair not in found:
            found[candidate.pair] = candidate
    return list(found.values())


def _touched_group(expression: Expression, first: Path, second: Path, brackets: bool) -> Why | None:
    """
    Return the reason naming the group that holds one of the numbers at ``first`` and
    ``second`` but not the other, the innermost such group, or ``None`` if there is none.
    """
    for path, other in ((first, second), (second, first)):
        for end in range(len(path), 0, -1):
            part = at(expression, path[:end])
            if is_grouped(part) and other[:end] != path[:end]:
                if part.grouping is Grouping.BRACKETS and brackets:
                    return Why.IN_BRACKETS
                return Why.IN_PARENTHESES
    return None


def _parentheses_question(draw: _Draw, choices: bool) -> OrderOfOperationsQuestion | None:
    """
    Make a question asking what the parentheses indicate, in an expression whose only group is
    two numbers, next to a number, with two operations or more outside it, and whose value the
    parentheses change, as STAAR's are.

    With even chance, multiple choice asks "What do these parentheses indicate?", answered with
    the group's operation before the one beside it ("Subtract 6 from 72 before multiplying by
    4"), or "Which statement is true?", answered "...indicate that 72 - 6 should be solved
    first". Written, it always asks the first. Wrong choices are STAAR's kinds: an operation
    across the group's edge first ("Multiply 4 by 72 before subtracting 6"), an operation
    outside it first ("Divide 10 by 5 before adding 4", or "...before subtracting 6 from 72"),
    and for the statements, the group last, and other pairs first and last, so no pair is named
    a different number of times from the rest.
    """
    limits = draw.limits(1, PARENTHESES_OPERATIONS)
    expression = random_expression(limits)
    groups = [path for path in _calculation_paths(expression) if is_grouped(at(expression, path))]
    if len(groups) != 1 or not groups[0]:
        return None
    group_path = groups[0]
    group = at(expression, group_path)
    parent = at(expression, group_path[:-1])
    assert isinstance(group, Calculation) and isinstance(parent, Calculation)
    beside = parent.left if group_path[-1] else parent.right
    if not (
        isinstance(group.left, Number)
        and isinstance(group.right, Number)
        and isinstance(beside, Number)
        and _written_parentheses(expression) == 1
        and mistaken_values(expression, Mistake.GROUPS_IGNORED)
    ):
        return None
    inside = Pair(group.left.value, group.operation, group.right.value)
    then = Then(parent.operation, beside.value, result_left=group_path[-1] == 0)
    order = Order(inside, then)
    if not choices:
        return Question(ParenthesesQuestionData(expression, True, order), FreeResponse())
    pairs = _pairs(expression)
    in_group = {(*group_path, 0), (*group_path, 1)}
    numbers = numbers_in(expression)
    across: list[tuple[int, Pair]] = []  # pairs with one number in the group
    outside: list[tuple[int, Pair]] = []  # pairs with neither
    for index, (pair, _) in enumerate(pairs):
        inner = [path in in_group for path in (numbers[index][0], numbers[index + 1][0])]
        if any(inner) and not all(inner):
            across.append((index, pair))
        elif not any(inner):
            outside.append((index, pair))
    answer: Statement
    candidates: list[Statement]
    if random.random() < 1 / 2:
        answer = order
        candidates = [
            _across_first(pair, inside, numbers[index][0] in in_group) for index, pair in across
        ]
        for index, pair in outside:
            candidates.append(Order(pair, _next_operation(pairs, numbers, index)))
            candidates.append(Order(pair, inside))
    else:
        answer = Timing(inside, first=True)
        others = [
            pair
            for _, pair in across + outside
            if pair != inside and _statement_fits(Timing(pair, True), limits.numbers)
        ]
        if not others:
            return None
        # another pair named twice, first and last, as the group's pair is, or the group's pair
        # named once, as another is, so a pair named a different number of times isn't the key
        named_twice = random.choice(others)
        candidates = [Timing(named_twice, first=True), Timing(named_twice, first=False)]
        remaining = [pair for pair in others if pair != named_twice]
        if remaining and random.random() < 1 / 2:
            candidates.append(Timing(random.choice(remaining), first=random.random() < 1 / 2))
        else:
            candidates.append(Timing(inside, first=False))
    wrong = [
        each
        for each in dict.fromkeys(candidates)
        if each != answer and _statement_fits(each, limits.numbers)
    ]
    if len(wrong) < WRONG_OPTIONS:
        return None
    chosen = random.sample(wrong, WRONG_OPTIONS)
    data = ParenthesesQuestionData(expression, True, answer)
    return Question(data, multiple_choice((answer,), tuple(chosen)))


def _across_first(pair: Pair, inside: Pair, group_first: bool) -> Order:
    """
    Return the statement that ``pair``, across the group's edge, comes first, then the group's
    operation with its other number: "Multiply 4 by 72 before subtracting 6" for 4(72 - 6), or
    "Divide 2 by 2 before adding 8" for (8 + 2) ÷ 2. ``group_first`` says the pair's first
    number is the group's.
    """
    if group_first:
        return Order(pair, Then(inside.operation, inside.left, result_left=False))
    return Order(pair, Then(inside.operation, inside.right, result_left=True))


def _next_operation(
    pairs: Sequence[tuple[Pair, Path | None]],
    numbers: Sequence[tuple[Path, Number]],
    index: int,
) -> Then:
    """
    Return the operation written after the pair at ``index``, with its number, as done next
    ("Divide 10 by 5 before adding 4"), or before it if the pair is last.
    """
    if index + 1 < len(pairs):
        return Then(pairs[index + 1][0].operation, numbers[index + 2][1].value, result_left=True)
    return Then(pairs[index - 1][0].operation, numbers[index - 1][1].value, result_left=False)


def _statement_fits(statement: Statement, kind: NumberKind) -> bool:
    """
    Return whether every operation ``statement`` names can be done by a student of its numbers:
    no subtraction below 0, and with whole numbers, no division with a remainder.
    """
    pairs = [statement.pair] if isinstance(statement, Timing) else [statement.first]
    if isinstance(statement, Order) and isinstance(statement.then, Pair):
        pairs.append(statement.then)
    for pair in pairs:
        if pair.operation is Operation.SUBTRACT and pair.left < pair.right:
            return False
        if pair.operation is Operation.DIVIDE:
            quotient = Fraction(pair.left) / Fraction(pair.right)
            if kind is NumberKind.WHOLE and quotient.denominator != 1:
                return False
    return True


def _find_error_question(
    draw: _Draw, choices: bool, total: int, error: int
) -> OrderOfOperationsQuestion | None:
    """
    Make a question showing an expression simplified in ``total`` steps, the one numbered
    ``error`` wrong, and asking in which step the error first appears, and why. The caller draws
    them, so each step is equally likely to hold the error; ``None`` if this expression can't
    have it there. The steps before it are right; the wrong step is a step a mistake writes,
    or for the last, the value a mistake comes to, from two operations or more; the steps after
    it are worked correctly from the wrong line. A step works one operation, every one that may
    be worked next, or a line of two at once. The reason is the operation that should have
    come first, or for a slip in a calculation's numbers, its value.

    Where a x or ÷ comes just before a multiplication without its sign, as in 60 ÷ 6[2 + 8],
    the steps are kept only if the step holding the error is the same read either way.

    Wrong choices (``_wrong_error_choices``) name the other steps, each once before any twice,
    and half the time the error's step, with a wrong reason.
    """
    level = draw.level()
    limits = draw.limits(level, LONG_OPERATIONS, sign_before_implied=draw.settings.implied)
    expression = random_expression(limits)
    made = _wrong_working(expression, limits, total, error)
    if made is None:
        return None
    lines, answer = made
    shown = (expression, *lines)
    if not _same_error_either_way(shown, error):
        return None
    brackets = draw.brackets()
    sign_before_implied = any(
        written_levels(line, replace(limits, sign_before_implied=False)) is None for line in shown
    )
    data = FindErrorQuestionData(expression, lines, brackets, answer, sign_before_implied)
    if not choices:
        return Question(data, FreeResponse())
    wrong = _wrong_error_choices(shown, error, answer, limits.numbers)
    if len(wrong) < WRONG_OPTIONS:
        return None
    return Question(data, multiple_choice((answer,), tuple(wrong)))


def _wrong_working(
    expression: Expression, limits: ExpressionLimits, total: int, error: int
) -> tuple[tuple[Expression, ...], ErrorChoice] | None:
    """
    Return ``total`` lines simplifying ``expression`` with the error in line ``error``, as
    ``_find_error_question`` describes, and the right choice; ``None`` if this expression can't
    have its error there.
    """
    line = expression
    lines: list[Expression] = []
    for _ in range(error - 1):
        if not isinstance(line, Calculation):
            return None
        line = _next_line(line)
        lines.append(line)
    before = line
    if not isinstance(before, Calculation):
        return None
    last = error == total
    if last and _operation_count(before) < 2:
        return None
    candidates: list[tuple[Expression, Mistake]] = []
    for mistake in (*ORDER_MISTAKES, *(() if last else SLIPS)):
        if last:
            found: Iterable[Expression] = (
                Number(each)
                for each in mistaken_values(before, mistake)
                if _fits_value(each, limits)
            )
        else:
            found = (
                each
                for each in mistaken_steps(before, mistake)
                if isinstance(each, Calculation) and _shows(each, limits)
            )
        candidates += [(each, mistake) for each in found]
    if not candidates:
        return None
    wrong, mistake = random.choice(candidates)
    rest = _working_to_number(wrong, total - error)
    if rest is None or not all(_shows(each, limits) for each in rest):
        return None
    lines += [wrong, *rest]
    if mistake in SLIPS:
        slipped = _slipped(before, wrong)
        if slipped is None:
            return None
        return tuple(lines), ErrorChoice(
            error, (slipped,), calculate(slipped.operation, slipped.left, slipped.right)
        )
    pairs = tuple(_pair_at(before, path) for path in allowed_paths(before))
    return tuple(lines), ErrorChoice(error, pairs)


def _next_line(line: Calculation) -> Expression:
    """
    Return the line after ``line`` in a worked simplification: with ``FINISH_SHARE`` chance for
    a line of two operations or fewer, its value; else a step working one operation, or with
    ``TOGETHER_SHARE`` chance, every operation that may be worked next.
    """
    if _operation_count(line) <= 2 and random.random() < FINISH_SHARE:
        return Number(value(line))
    return step(line, together=random.random() < TOGETHER_SHARE)


def _working_to_number(start: Expression, count: int) -> tuple[Expression, ...] | None:
    """Return ``count`` lines working ``start`` correctly to a number, ``None`` if none is found."""
    for _ in range(TRIES // 10):
        lines: list[Expression] = []
        line = start
        while isinstance(line, Calculation) and len(lines) < count:
            line = _next_line(line)
            lines.append(line)
        if len(lines) == count and isinstance(line, Number):
            return tuple(lines)
    return None


def _slipped(before: Expression, wrong: Expression) -> Pair | None:
    """Return the pair worked with a slip from ``before`` to ``wrong``, or ``None`` if none was."""
    for path in allowed_paths(before):
        part = at(wrong, path) if _has_path(wrong, path) else None
        if isinstance(part, Number) and replaced(before, path, part) == wrong:
            return _pair_at(before, path)
    return None


def _same_error_either_way(shown: Sequence[Expression], error: int) -> bool:
    """
    Return whether the first line whose value differs from the line before it is ``error``,
    both read correctly and with each multiplication without its sign misread from left to
    right after a x or ÷, as (60 ÷ 6)[2 + 8]. That reading is a misreading of the notation, not
    a second valid one; the question just mustn't reward or punish it.
    """
    for read in (lambda each: each, _misread):
        try:
            values = [value(read(line)) for line in shown]
        except ZeroDivisionError:
            return False
        changed = [index for index in range(1, len(values)) if values[index] != values[index - 1]]
        if not changed or changed[0] != error:
            return False
    return True


def _misread(expression: Expression) -> Expression:
    """
    Return ``expression`` with each multiplication without its sign just after a x or ÷ read as
    if its sign were there, left to right: 60 ÷ 6[2 + 8] as (60 ÷ 6) x [2 + 8].
    """
    if not isinstance(expression, Calculation):
        return expression
    node = replace(expression, left=_misread(expression.left), right=_misread(expression.right))
    while (
        node.operation in _FIRST
        and not node.implied
        and is_ungrouped(node.right)
        and node.right.implied
    ):
        inner = node.right
        node = Calculation(
            Operation.MULTIPLY,
            Calculation(node.operation, node.left, inner.left),
            inner.right,
            grouping=node.grouping,
        )
    return node


def _wrong_error_choices(
    shown: Sequence[Expression], error: int, answer: ErrorChoice, kind: NumberKind
) -> list[ErrorChoice]:
    """
    Return three wrong choices for a worked simplification ``shown``, the given expression then
    its steps: each names a step with a wrong reason, either a pair of numbers written next to
    each other in the line before it that may not be worked first, as STAAR's "Step 1, because
    60 ÷ 6 should be simplified first" is, or a value that a pair the step works doesn't come
    to. Half the time one names the error's step. Every step can be named, so a step named only
    when it holds the error doesn't give the answer away.
    """
    claims: dict[int, list[ErrorChoice]] = {}
    for number in range(1, len(shown)):
        before = shown[number - 1]
        allowed = set(allowed_paths(before))
        pair_claims = [
            ErrorChoice(number, (pair,)) for pair, path in _pairs(before) if path not in allowed
        ]
        value_claims = [
            ErrorChoice(number, (pair,), wrong_value)
            for pair in (_pair_at(before, path) for path in allowed)
            for wrong_value in _near_misses(calculate(pair.operation, pair.left, pair.right), kind)
        ]
        if pair_claims and (not value_claims or random.random() < PAIR_CLAIM_SHARE):
            claims[number] = pair_claims
        else:
            claims[number] = value_claims
    chosen: list[ErrorChoice] = []
    right_step = [claim for claim in claims.get(error, []) if claim != answer]
    if right_step and random.random() < RIGHT_STEP_WRONG_REASON_SHARE:
        chosen.append(random.choice(right_step))
    # each other step once, in random order, before any twice, so no step stands out
    others = [number for number in claims if number != error]
    random.shuffle(others)
    for number in others * WRONG_OPTIONS:
        unused = [claim for claim in claims[number] if claim not in chosen]
        if len(chosen) < WRONG_OPTIONS and unused:
            chosen.append(random.choice(unused))
    return chosen


def _near_misses(right: NumberValue, kind: NumberKind) -> list[NumberValue]:
    """
    Return values close to ``right`` that a slip would give, above 0: one more or less, and for
    decimals a tenth more or less, or for fractions a whole more or less.
    """
    steps_away: list[NumberValue] = [1, 10]
    if kind is NumberKind.DECIMAL and not isinstance(right, int):
        steps_away = [Decimal("0.1"), 1]
    found = []
    for away in steps_away:
        for near in (
            calculate(Operation.ADD, right, away),
            calculate(Operation.SUBTRACT, right, away),
        ):
            if near > 0:
                found.append(near)
    return found


def _tile_questions(
    types: Sequence[QuestionType],
    question_types: Sequence[QuestionType],
    draw: _Draw,
    count: int,
) -> list[OrderOfOperationsQuestion]:
    """
    Make the questions of a self-check tiles sheet, of ``types`` in order, as
    ``generate_order_of_operations_questions`` describes for ``distinct_answers``.
    """
    not_tiles = [each for each in question_types if each not in TILE_TYPES]
    if not_tiles:
        listed = ", ".join(each.value for each in not_tiles)
        raise ValueError(f"These question types have no self-check tiles form: {listed}.")
    limit = tile_answers_limit(question_types)
    if limit is not None and count > limit:
        raise ValueError(
            f"Cannot make {count} questions with different answers: only {limit} possible."
        )
    used: set[str] = set()
    made: dict[int, OrderOfOperationsQuestion] = {}
    # the counts first, as they can only be 0 to 4, which other answers could take
    for index in sorted(range(len(types)), key=lambda each: types[each] is not HAS_VALUE):
        question_type = types[index]
        counts = [each for each in HAS_VALUE_COUNTS if str(each) not in used]
        if question_type is HAS_VALUE and not counts:
            question_type = next(each for each in question_types if each is not HAS_VALUE)
        for _ in range(TRIES):
            question = _tile_question(question_type, draw, counts)
            answer = tile_answer(question.data)
            if answer not in used:
                used.add(answer)
                made[index] = question
                break
        else:
            raise ValueError("Cannot make questions with different answers for these settings.")
    return [made[index] for index in range(len(types))]


def _tile_question(
    question_type: QuestionType, draw: _Draw, counts: Sequence[int]
) -> OrderOfOperationsQuestion:
    """
    Make a self-check tiles sheet's question of ``question_type``, in a form whose answer is a
    number the question doesn't print: an expression's value; a line of its working with one
    number it worked out left as a box; how many of four expressions have a value, one of
    ``counts``; or what number the first operation gives.
    """
    match question_type:
        case QuestionType.VALUE:
            return _first_made(lambda: _value_question(draw, choices=False))
        case QuestionType.NEXT_STEP:
            return _first_made(lambda: _step_blank_question(draw))
        case QuestionType.HAS_VALUE:
            count = random.choice(counts)
            return _first_made(lambda: _has_value_question(draw, False, count))
        case QuestionType.FIRST_OPERATION:
            return _first_made(lambda: _first_operation_question(draw, False, result=True))
    raise ValueError(f"{question_type.value} has no self-check tiles form.")


def _step_blank_question(draw: _Draw) -> OrderOfOperationsQuestion | None:
    """
    Make a question showing an expression equal to its next step, or the step after, one
    operation at a time, with one of the numbers worked out so far left as a box: "28 + 7 x
    (12 - 4) = 28 + ☐" (56).
    """
    level = draw.level()
    expression = random_expression(draw.limits(level, OPERATIONS[level]))
    line = expression
    results: set[Path] = set()
    lines: list[tuple[Expression, set[Path]]] = []
    while isinstance(line, Calculation) and allowed_paths(line):
        path = allowed_paths(line)[0]
        line = worked(line, path)
        results = {each for each in results if each[: len(path)] != path} | {path}
        if isinstance(line, Calculation):
            lines.append((line, results))
    if not lines:
        return None
    shown, worked_out = random.choice(lines[:2])
    blank = random.choice(sorted(worked_out))
    part = at(shown, blank)
    assert isinstance(part, Number)
    data = StepBlankQuestionData(expression, draw.brackets(), shown, blank, part.value)
    return Question(data, FreeResponse())


def _wrong_values(
    expression: Expression, answer: NumberValue, kind: NumberKind
) -> list[ValueOption]:
    """
    Return the values ``expression``'s mistakes come to, of the answer's kind, in an order that
    takes one from each mistake, the mistakes in random order, before a second from any. A
    whole number added to a fraction's numerator is written improper, as STAAR writes it.
    """
    by_mistake: list[list[ValueOption]] = []
    for mistake in random.sample(list(Mistake), len(Mistake)):
        found: list[ValueOption] = []
        for each in mistaken_values(expression, mistake):
            if not _like_answer(each, kind):
                continue
            if mistake is Mistake.WHOLE_NUMBER_IN_NUMERATOR and isinstance(each, Fraction):
                found.append(Improper(each) if each > 1 else each)
            else:
                found.append(each)
        random.shuffle(found)
        by_mistake.append(found)
    chosen: list[ValueOption] = []
    seen = {answer}
    for index in range(max(map(len, by_mistake), default=0)):
        for found in by_mistake:
            if index < len(found):
                option = found[index]
                number = _option_value(option)
                if number not in seen:
                    seen.add(number)
                    chosen.append(option)
    return chosen


def _option_value(option: ValueOption) -> NumberValue:
    """Return the value a value option stands for."""
    return option.value if isinstance(option, Improper) else option


def _wrong_steps(
    expression: Expression, limits: ExpressionLimits, brackets: bool
) -> list[Expression]:
    """
    Return the steps the mistakes write from ``expression`` and from its next step, each an
    expression that can be written on the sheet and within ``limits``, in an order that takes
    one from each mistake, in random order, before a second from any.
    """
    right = set(steps(expression)) | {step(expression, together=True)}
    by_mistake: list[list[Expression]] = []
    for mistake in random.sample(list(Mistake), len(Mistake)):
        found: list[Expression] = [
            each
            for line in (expression, step(expression))
            if isinstance(line, Calculation)
            for each in mistaken_steps(line, mistake)
            if isinstance(each, Calculation)
            and each not in right
            and _shows(each, limits, brackets)
        ]
        random.shuffle(found)
        by_mistake.append(found)
    chosen: list[Expression] = []
    for index in range(max(map(len, by_mistake), default=0)):
        for found in by_mistake:
            if index < len(found) and found[index] not in chosen:
                chosen.append(found[index])
    return chosen


def _shows(expression: Expression, limits: ExpressionLimits, brackets: bool = True) -> bool:
    """Return whether ``expression`` can be written on the sheet and its working fits ``limits``."""
    try:
        expression_pieces(
            expression, brackets=brackets, sign_before_implied=limits.sign_before_implied
        )
    except ValueError:
        return False
    return within(expression, limits)


def _fits_value(number: NumberValue, limits: ExpressionLimits) -> bool:
    """Return whether ``number`` can be a line of working within ``limits``."""
    return within(Number(number), limits) and number <= limits.largest_value


def _like_answer(number: NumberValue, kind: NumberKind) -> bool:
    """
    Return whether ``number`` is a believable wrong value for an expression of ``kind``: above
    0, and whole for whole numbers, with at most two decimal places for decimals, or not a
    decimal for fractions. A decimal among whole answers would be wrong on sight.
    """
    if number <= 0:
        return False
    match kind:
        case NumberKind.WHOLE:
            return isinstance(number, int)
        case NumberKind.DECIMAL:
            return not isinstance(number, Fraction) and (Fraction(number) * 100).denominator == 1
        case NumberKind.FRACTION:
            return not isinstance(number, Decimal)


def _pairs(expression: Expression) -> list[tuple[Pair, Path | None]]:
    """
    Return each two numbers written next to each other in ``expression``, with the operation
    between them, as a pair, in order: with the path of the calculation it is, or ``None`` for
    one across a group's edge, such as 2 + 4 in 6[(1 x 2) + (4 x 2)].
    """
    numbers = numbers_in(expression)
    found: list[tuple[Pair, Path | None]] = []
    for ((left_path, left), (right_path, right)), (operation, common) in zip(
        pairwise(numbers), _signs(expression), strict=True
    ):
        own = left_path == (*common, 0) and right_path == (*common, 1)
        found.append((Pair(left.value, operation, right.value), common if own else None))
    return found


def _signs(expression: Expression) -> list[tuple[Operation, Path]]:
    """
    Return the operation between each two numbers written next to each other in
    ``expression``, with the path of the calculation it belongs to.
    """
    found: list[tuple[Operation, Path]] = []
    for (left_path, _), (right_path, _) in pairwise(numbers_in(expression)):
        common = 0
        while left_path[common] == right_path[common]:
            common += 1
        path = left_path[:common]
        part = at(expression, path)
        assert isinstance(part, Calculation)
        found.append((part.operation, path))
    return found


def _pair_at(expression: Expression, path: Path) -> Pair:
    """Return the calculation on two numbers at ``path`` as a pair."""
    part = at(expression, path)
    assert isinstance(part, Calculation)
    assert isinstance(part.left, Number) and isinstance(part.right, Number)
    return Pair(part.left.value, part.operation, part.right.value)


def _left_to_right(
    terms: Sequence[Expression], signs: Sequence[tuple[Operation, bool]]
) -> Expression:
    """Return ``terms`` joined by ``signs`` from left to right, whatever their operations."""
    expression = terms[0]
    for (operation, _), term in zip(signs, terms[1:], strict=True):
        expression = Calculation(operation, expression, term)
    return expression


def _calculation_paths(expression: Expression, path: Path = ()) -> list[Path]:
    """Return the paths of ``expression``'s calculations, in the order written."""
    if not isinstance(expression, Calculation):
        return []
    return [
        *_calculation_paths(expression.left, (*path, 0)),
        path,
        *_calculation_paths(expression.right, (*path, 1)),
    ]


def _operation_count(expression: Expression) -> int:
    """Return how many operations ``expression`` has."""
    return len(_calculation_paths(expression))


def _written_parentheses(expression: Expression) -> int:
    """Return how many pairs of grouping symbols ``expression`` is written with."""
    text = expression_text(expression)
    return text.count("(") + text.count("[")


def _has_path(expression: Expression, path: Path) -> bool:
    """Return whether ``expression`` has a part at ``path``."""
    part = expression
    for side in path:
        if not isinstance(part, Calculation):
            return False
        part = part.right if side else part.left
    return True
