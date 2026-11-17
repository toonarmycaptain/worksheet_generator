"""
Random generation of input-output table questions: tables to complete, and the multiple-choice
questions STAAR asks about a rule and its table.
"""

import random
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from itertools import combinations, pairwise

from core.basic_operations.data import Operation
from core.input_output_tables.contexts import CONTEXTS, TableContext
from core.input_output_tables.data import (
    Blanks,
    ChoiceType,
    InputOutputQuestion,
    InputOutputRuleQuestionData,
    InputOutputTableQuestionData,
    NumberPairs,
    Rule,
    RuleForm,
)
from core.input_output_tables.representation import SMALLER_FIRST, missing_numbers
from core.names import NAMES
from core.question import FreeResponse, Question, multiple_choice

PAIRS = 4  # the number pairs in a table
BLANK_PAIRS = 3  # the pairs a table to complete leaves a number out of, so one pair stays whole
LARGEST_VALUE = 100  # every number in a table, the wrong tables' included, is from 1 to this
# The relation between a context's quantities for each operation: what makes the larger quantity
# from the smaller, whichever is the input
RELATIONS = {
    Operation.ADD: Operation.ADD,
    Operation.SUBTRACT: Operation.ADD,
    Operation.MULTIPLY: Operation.MULTIPLY,
    Operation.DIVIDE: Operation.MULTIPLY,
}
# The rule's number, for each relation
RULE_NUMBERS = {Operation.ADD: range(1, 21), Operation.MULTIPLY: range(2, 11)}
# A multiplication context's smaller quantities, which keep it within the 10 by 10 facts
MULTIPLICATION_SMALLER = range(1, 11)
WRONG_TABLES = 3  # beside the correct one, in a multiple-choice question
WRONG_NUMBER_REACH = 3  # a wrong rule's number is at most this far from the rule's
WRONG_TABLE_TRIES = 20  # wrong tables tried for a question's numbers before drawing new ones
SHARED_PAIRS = (1, 2)  # how many pairs all four shared-inputs tables agree in, with even chance
# How a question of each type asking for a table's rule shows its rules, each with even chance
RULE_FORMS = {
    ChoiceType.SENTENCE: (RuleForm.SENTENCE,),
    ChoiceType.STATEMENT: (RuleForm.STATEMENT, RuleForm.EXPLAINED),
}
# The patterns of wrong rules, as _wrong_rules describes them, each as likely as it is frequent
# here: one operation with four numbers, the most easily confused, half the time
WRONG_RULE_PATTERNS = ("numbers", "numbers", "other operation", "reverse")

_INVERSES = {
    Operation.ADD: Operation.SUBTRACT,
    Operation.SUBTRACT: Operation.ADD,
    Operation.MULTIPLY: Operation.DIVIDE,
    Operation.DIVIDE: Operation.MULTIPLY,
}
# The operations of the other kind: multiplying and dividing against adding and subtracting
_OTHER_KIND = {
    Operation.ADD: (Operation.MULTIPLY, Operation.DIVIDE),
    Operation.SUBTRACT: (Operation.MULTIPLY, Operation.DIVIDE),
    Operation.MULTIPLY: (Operation.ADD, Operation.SUBTRACT),
    Operation.DIVIDE: (Operation.ADD, Operation.SUBTRACT),
}
_COLUMNS = {Blanks.OUTPUTS: (1,), Blanks.INPUTS: (0,), Blanks.INPUTS_AND_OUTPUTS: (0, 1)}


@dataclass(frozen=True)
class _Plan:
    """
    The choices made once for a question, and kept while new numbers are drawn for it, so that
    drawing again when the numbers leave no room doesn't favour any choice.

    ``choice_type`` is ``None`` for a table to complete. The question's operation is drawn from
    ``operations``. A table to choose shares its inputs among the four tables with
    ``shared_inputs``, and its wrong tables' size is ``wrong_larger`` without it, or ``rank``
    with it, as ``_wrong_tables`` and ``_shared_input_tables`` describe. A question asking for
    the rule shows its rules in ``form``, and its wrong rules follow ``pattern`` with ``rank``
    wrong numbers below the rule's, as ``_wrong_rules`` describes. Fields a question doesn't use
    keep their defaults.
    """

    choice_type: ChoiceType | None
    operations: tuple[Operation, ...]
    shared_inputs: bool = False
    wrong_larger: bool = False
    rank: int = 0
    form: RuleForm = RuleForm.SENTENCE
    pattern: str = "numbers"


def generate_input_output_table_questions(
    count: int,
    operations: Sequence[Operation],
    *,
    blanks: Blanks = Blanks.INPUTS_AND_OUTPUTS,
    choice_types: Sequence[ChoiceType] = (),
    distinct_answers: bool = False,
) -> list[InputOutputQuestion]:
    """
    Generate ``count`` questions, each with its operation drawn at random from ``operations``.

    Each question takes the next context from a shuffled deck of its relation's contexts, so no
    context repeats on a sheet until all of them have been used, and its rule's number at random
    from ``RULE_NUMBERS``. A table has ``PAIRS`` pairs, whose smaller quantities increase with no
    two adjacent gaps equal: with equal gaps, a column could be completed by counting on, without
    the rule. For addition and subtraction, every number is from 1 to ``LARGEST_VALUE``; for
    multiplication and division, the smaller quantities are from 1 to 10.

    Without ``choice_types``, each question is a table to complete, which leaves a number out of
    ``BLANK_PAIRS`` of its pairs, chosen at random: each one's output, its input, or with
    ``Blanks.INPUTS_AND_OUTPUTS`` either, with at least one of each. With ``distinct_answers``,
    as the self-check tiles case needs, each table leaves out one number, and no two tables leave
    out the same number.

    With ``choice_types``, the questions are shared evenly among them, then shuffled:
    - ``ChoiceType.TABLE``: the rule given, its table chosen from lettered tables, with even
      chance in either look, as ``_wrong_tables`` and ``_shared_input_tables`` describe;
    - ``ChoiceType.SENTENCE``: the table given, a sentence completed with its rule, its
      operation and number circled from those of the rules to choose from;
    - ``ChoiceType.STATEMENT``: the table given, the true statement of its rule chosen, with
      even chance plain or with the context's fact and the rule as its reason.
    Both choose among the rule and the wrong rules ``_wrong_rules`` makes, and their tables
    about multiplication or division leave out 1. ``blanks`` doesn't apply.

    Raises ``ValueError`` if ``operations`` is empty, if both ``choice_types`` and
    ``distinct_answers`` are given, or if ``distinct_answers`` asks for more questions than
    ``count_possible_answers`` allows.
    """
    if not operations:
        raise ValueError("At least one operation is needed.")
    if choice_types and distinct_answers:
        raise ValueError("Multiple-choice questions leave out no numbers to keep distinct.")
    if distinct_answers:
        possible = count_possible_answers(operations, blanks)
        if count > possible:
            raise ValueError(
                f"Cannot make {count} tables with different missing numbers: only {possible} "
                "possible."
            )
    types: list[ChoiceType | None] = [None] * count
    if choice_types:
        types = [choice_types[index % len(choice_types)] for index in range(count)]
        random.shuffle(types)
    decks: dict[Operation, list[TableContext]] = {}
    used: set[int] | None = set() if distinct_answers else None
    plan: _Plan | None = None
    questions: list[InputOutputQuestion] = []
    while len(questions) < count:
        if plan is None:
            plan = _plan(types[len(questions)], operations)
        operation = random.choice(plan.operations)
        relation = RELATIONS[operation]
        if not decks.get(relation):
            decks[relation] = list(CONTEXTS[relation])
            random.shuffle(decks[relation])
        question = _question(operation, decks[relation].pop(), blanks, plan, used)
        if question is None:
            continue  # the numbers left no room for the question: draw another
        if used is not None and isinstance(question.data, InputOutputTableQuestionData):
            used.update(missing_numbers(question.data))
        questions.append(question)
        plan = None
    return questions


def count_possible_answers(operations: Sequence[Operation], blanks: Blanks) -> int:
    """
    Return how many different numbers a table's one missing number can be, for tables of
    ``operations`` that leave out ``blanks``: the most questions ``distinct_answers`` allows.
    """
    return len(
        {
            _pair(operation, number, smaller)[column]
            for operation in set(operations)
            for number in RULE_NUMBERS[RELATIONS[operation]]
            for smaller in _smaller_population(RELATIONS[operation], number)
            for column in _COLUMNS[blanks]
        }
    )


def _plan(choice_type: ChoiceType | None, operations: Sequence[Operation]) -> _Plan:
    """
    Make a question's ``_Plan``. The shared-inputs look is chosen only if an operation other than
    division is given, and then the question's operation is drawn from those operations: dividing
    by a nearby number leaves fractions, so division has no shared-inputs tables.
    """
    if choice_type is None:
        return _Plan(None, tuple(operations))
    if choice_type is ChoiceType.TABLE:
        shareable = tuple(
            operation for operation in operations if operation is not Operation.DIVIDE
        )
        shared_inputs = random.choice((False, True)) if shareable else False
        if shared_inputs:
            return _Plan(choice_type, shareable, shared_inputs=True, rank=random.randrange(4))
        return _Plan(choice_type, tuple(operations), wrong_larger=random.choice((True, False)))
    forms = RULE_FORMS[choice_type]
    form = random.choice(forms) if len(forms) > 1 else forms[0]
    pattern = random.choice(WRONG_RULE_PATTERNS)
    # the rule's number's place among the numbers: among four, or among two
    rank = random.randrange(4 if pattern == "numbers" else 2)
    return _Plan(choice_type, tuple(operations), rank=rank, form=form, pattern=pattern)


def _question(
    operation: Operation,
    context: TableContext,
    blanks: Blanks,
    plan: _Plan,
    used: set[int] | None,
) -> InputOutputQuestion | None:
    """
    Make a question about ``context`` whose table follows ``operation``, as ``plan`` and
    ``generate_input_output_table_questions`` describe. With ``used``, the table leaves out one
    number, which is not in ``used``.

    Returns ``None`` if its numbers leave no room for the question: no wrong tables for a table
    to choose, or with ``used``, no number in the table that isn't used already.
    """
    name = random.choice(NAMES) if "{name}" in context.title + context.rule else None
    relation = RELATIONS[operation]
    number = random.choice(RULE_NUMBERS[relation])
    # A table about multiplication whose rule is chosen leaves out 1: its pair would show the
    # rule's number, as 1 and 8 do for times 8, picking out the choices with that number.
    asks_for_rule = plan.choice_type in (ChoiceType.SENTENCE, ChoiceType.STATEMENT)
    without_one = asks_for_rule and relation is Operation.MULTIPLY
    population = _smaller_population(relation, number)[without_one:]
    pairs = tuple(_pair(operation, number, smaller) for smaller in _smaller_quantities(population))
    if plan.choice_type is None:
        cells = _blank_cells(pairs, blanks, used)
        if cells is None:
            return None
        blank_inputs, blank_outputs = cells
        data = InputOutputTableQuestionData(
            context, name, operation, number, pairs, blank_inputs, blank_outputs
        )
        return Question(data, FreeResponse())
    if plan.choice_type is ChoiceType.TABLE:
        if plan.shared_inputs:
            wrong_tables = _shared_input_tables(pairs, operation, number, plan.rank)
        else:
            wrong_tables = _wrong_tables(pairs, operation, number, plan.wrong_larger)
        if wrong_tables is None:
            return None
        table = InputOutputTableQuestionData(context, name, operation, number, pairs)
        return Question(table, multiple_choice((pairs,), wrong_tables))
    wrong_rules = _wrong_rules(operation, number, plan.pattern, plan.rank)
    if wrong_rules is None:
        return None
    rule_data = InputOutputRuleQuestionData(context, name, pairs, (operation, number), plan.form)
    return Question(rule_data, multiple_choice(((operation, number),), wrong_rules))


def _smaller_population(relation: Operation, number: int) -> range:
    """
    Return the smaller quantities a table can have: from ``MULTIPLICATION_SMALLER``, or for
    addition, from 1 to ``LARGEST_VALUE`` less ``number``, so the larger are at most
    ``LARGEST_VALUE``.
    """
    if relation is Operation.MULTIPLY:
        return MULTIPLICATION_SMALLER
    return range(1, LARGEST_VALUE - number + 1)


def _smaller_quantities(population: range) -> list[int]:
    """
    Return ``PAIRS`` smaller quantities from ``population``, in increasing order, with no two
    adjacent gaps between them equal.
    """
    while True:
        smaller = sorted(random.sample(population, PAIRS))
        gaps = [later - earlier for earlier, later in pairwise(smaller)]
        if all(first != second for first, second in pairwise(gaps)):
            return smaller


def _pair(operation: Operation, number: int, smaller: int) -> tuple[int, int]:
    """
    Return the (input, output) pair for a context's smaller quantity, in a table following
    ``operation`` ``number``.
    """
    larger = smaller + number if RELATIONS[operation] is Operation.ADD else smaller * number
    return (smaller, larger) if operation in SMALLER_FIRST else (larger, smaller)


def _blank_cells(
    pairs: NumberPairs, blanks: Blanks, used: set[int] | None
) -> tuple[tuple[int, ...], tuple[int, ...]] | None:
    """
    Return the indexes of the pairs whose inputs, and of those whose outputs, the table leaves
    out, as ``generate_input_output_table_questions`` describes. With ``used``, there is one,
    whose number is not in ``used``, or ``None`` if every number the table could leave out is.
    """
    if used is not None:
        cells = [
            (index, column)
            for index in range(len(pairs))
            for column in _COLUMNS[blanks]
            if pairs[index][column] not in used
        ]
        if not cells:
            return None
        index, column = random.choice(cells)
        return ((index,), ()) if column == 0 else ((), (index,))
    whole = random.randrange(len(pairs))
    indexes = [index for index in range(len(pairs)) if index != whole]
    if blanks is Blanks.OUTPUTS:
        return (), tuple(indexes)
    if blanks is Blanks.INPUTS:
        return tuple(indexes), ()
    inputs = sorted(random.sample(indexes, random.randint(1, BLANK_PAIRS - 1)))
    return tuple(inputs), tuple(index for index in indexes if index not in inputs)


def _wrong_rule_kinds(operation: Operation, number: int) -> tuple[list[Rule], list[Rule]]:
    """
    Return the two kinds of wrong rule STAAR offers: the rule's number with another operation,
    and the rule's operation with a number up to ``WRONG_NUMBER_REACH`` away. A rule whose
    number its operation doesn't take, such as multiplying by 15, is left out. Neither kind is
    ever empty: every operation's inverse takes its number, and every operation takes a number
    one away from any of its own.
    """
    numbers = RULE_NUMBERS[RELATIONS[operation]]
    near = range(number - WRONG_NUMBER_REACH, number + WRONG_NUMBER_REACH + 1)
    other_operations = [
        (other, number)
        for other in Operation
        if other is not operation and number in RULE_NUMBERS[RELATIONS[other]]
    ]
    other_numbers = [
        (operation, nearby) for nearby in near if nearby != number and nearby in numbers
    ]
    return other_operations, other_numbers


def _wrong_tables(
    pairs: NumberPairs, operation: Operation, number: int, larger: bool
) -> tuple[NumberPairs, NumberPairs, NumberPairs] | None:
    """
    Return three wrong tables for a table to choose, or ``None`` if the numbers leave no room for
    them.

    The first is the correct table with its columns swapped, so the numbers of each quantity sit
    under the other's heading: STAAR's released items offer this mistake more than any other. The
    second follows a wrong rule from ``_wrong_rule_kinds``, each kind with even chance, and the
    third is the second swapped. The second table is made as a table of the wrong rule's own
    would be, from smaller quantities of its own.

    Every table thus has a swapped twin, so the numbers alone mustn't give the answer away:
    - no number of the second table's is in the same pair as in the correct table, so no column,
      and no number in the same place, that the most tables share points to the answer;
    - its numbers add up to more than the correct table's with ``larger``, else not, so neither
      do the largest or smallest numbers, as long as the caller sets ``larger`` with even
      chance. A wrong operation would otherwise make one size more often, such as addition's
      numbers, from 1 to 100, against multiplication's.
    It gives up after ``WRONG_TABLE_TRIES``: the smallest tables leave no smaller one.
    """
    total = _total(pairs)
    kinds = _wrong_rule_kinds(operation, number)
    for _ in range(WRONG_TABLE_TRIES):
        wrong_operation, wrong_number = random.choice(random.choice(kinds))
        population = _smaller_population(RELATIONS[wrong_operation], wrong_number)
        wrong = tuple(
            _pair(wrong_operation, wrong_number, smaller)
            for smaller in _smaller_quantities(population)
        )
        if (_total(wrong) > total) == larger and not any(
            set(correct_pair) & set(wrong_pair)
            for correct_pair, wrong_pair in zip(pairs, wrong, strict=True)
        ):
            return _swapped(pairs), wrong, _swapped(wrong)
    return None


def _shared_input_tables(
    pairs: NumberPairs, operation: Operation, number: int, rank: int
) -> tuple[NumberPairs, NumberPairs, NumberPairs] | None:
    """
    Return three wrong tables with the correct table's inputs, as many of STAAR's are, or
    ``None`` if the numbers leave no room for them.

    All four tables agree in the same pairs, as all four of STAAR's socks tables agree in their
    first, so a student who checks only those can't tell them apart. How many pairs, from
    ``SHARED_PAIRS``, and which are chosen at random, so they follow no pattern. In every other
    pair, a wrong table's output follows a wrong rule from ``_wrong_rule_kinds``, as STAAR's
    tables that are right in their first pair go wrong after it. Every output must be a whole
    number from 1 to ``LARGEST_VALUE``, and a wrong table's outputs must increase with its
    inputs, as the correct table's do, so that no table out of order gives itself away. The
    tables agree only where all four do: a wrong table agreeing with the correct one alone, in a
    pair of its own, would make the correct table the one agreeing most with the others. So the
    numbers alone don't give the answer away:
    - in every other pair, the four tables' outputs differ, so no output the most tables share
      points to the answer;
    - ``rank`` of the wrong tables have numbers adding up to less than the correct table's, and
      the rest more. The caller sets ``rank`` from 0 to 3 with even chance, so the correct table
      is as likely to be the smallest as the largest, or either between.
    The candidates are shuffled, and the first three that meet both are taken.
    """
    total = _total(pairs)
    shared = set(random.sample(range(len(pairs)), random.choice(SHARED_PAIRS)))
    other_operations, other_numbers = _wrong_rule_kinds(operation, number)
    candidates = [
        table
        for wrong_operation, wrong_number in other_operations + other_numbers
        if (table := _right_in_pairs(pairs, shared, wrong_operation, wrong_number)) is not None
    ]
    random.shuffle(candidates)
    below = [table for table in candidates if _total(table) < total]
    above = [table for table in candidates if _total(table) > total]
    for smaller in combinations(below, rank):
        for bigger in combinations(above, WRONG_TABLES - rank):
            tables = (pairs, *smaller, *bigger)
            if all(
                len({table[index][1] for table in tables}) == len(tables)
                for index in range(len(pairs))
                if index not in shared
            ):
                first, second, third = (*smaller, *bigger)
                return first, second, third
    return None


def _wrong_rules(
    operation: Operation, number: int, pattern: str, rank: int
) -> tuple[Rule, Rule, Rule] | None:
    """
    Return three wrong rules to choose from beside the rule, in one of STAAR's patterns, or
    ``None`` if the rule's number leaves no room for ``rank`` wrong numbers below it.

    In every pattern, each operation and each number is in as many of the four rules as every
    other, so the rule isn't the one the others have most in common with:
    - ``"numbers"``: the rule's operation with three other numbers (STAAR 2018 Q7), so only the
      number tells them apart, the likeliest mistake;
    - ``"other operation"``: an operation of the other kind, adding or subtracting against
      multiplying or dividing, with the rule's number, and both operations with another number
      (2021 Q13);
    - ``"reverse"``: the same with the inverse operation (2017 Q25, 2019 Q21, 2022 Q9).
    The other numbers are up to ``WRONG_NUMBER_REACH`` from the rule's, among the numbers its
    operation takes, so they are as likely as the rule's to turn up in the table. ``rank`` of
    them are below the rule's number, the rest above, so its place among the numbers, chosen by
    the caller with even chance, doesn't give it away.
    """
    numbers_taken = RULE_NUMBERS[RELATIONS[operation]]
    near = range(number - WRONG_NUMBER_REACH, number + WRONG_NUMBER_REACH + 1)
    below = [other for other in near if other < number and other in numbers_taken]
    above = [other for other in near if other > number and other in numbers_taken]
    count = WRONG_TABLES if pattern == "numbers" else 1
    if len(below) < rank or len(above) < count - rank:
        return None
    numbers = (random.sample(below, rank) if rank else []) + (
        random.sample(above, count - rank) if count > rank else []
    )
    if pattern == "numbers":
        first, second, third = numbers
        return (operation, first), (operation, second), (operation, third)
    reverse = pattern == "reverse"
    other = _INVERSES[operation] if reverse else random.choice(_OTHER_KIND[operation])
    (nearby,) = numbers
    return (other, number), (operation, nearby), (other, nearby)


def _right_in_pairs(
    pairs: NumberPairs, shared: Collection[int], operation: Operation, number: int
) -> NumberPairs | None:
    """
    Return the table with the inputs of ``pairs``, its outputs in the pairs at ``shared`` those
    of ``pairs``, and in every other pair its input ``operation`` ``number``. Returns ``None`` if
    an output isn't a whole number from 1 to ``LARGEST_VALUE``, or the outputs don't increase.
    """
    made: list[tuple[int, int]] = []
    for index, (input_, output) in enumerate(pairs):
        new_output = output if index in shared else _apply(operation, number, input_)
        if new_output is None or (made and new_output <= made[-1][1]):
            return None
        made.append((input_, new_output))
    return tuple(made)


def _apply(operation: Operation, number: int, value: int) -> int | None:
    """
    Return ``value`` ``operation`` ``number``, or ``None`` if that isn't a whole number from 1 to
    ``LARGEST_VALUE``.
    """
    match operation:
        case Operation.ADD:
            result = value + number
        case Operation.SUBTRACT:
            result = value - number
        case Operation.MULTIPLY:
            result = value * number
        case Operation.DIVIDE:
            if value % number:
                return None
            result = value // number
    return result if 1 <= result <= LARGEST_VALUE else None


def _swapped(pairs: NumberPairs) -> NumberPairs:
    """Return the table with its inputs and outputs swapped."""
    return tuple((output, input_) for input_, output in pairs)


def _total(pairs: NumberPairs) -> int:
    """Return the sum of every number in the table."""
    return sum(input_ + output for input_, output in pairs)
