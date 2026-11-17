"""
Tests for what an input-output table question shows: the rule, question and title, the headings,
the sentences and statements of a table's rule, the answer key's entry and the self-check tile
question. Questions are built by hand from the contexts in ``tests.data``.
"""

import pytest

from core.basic_operations.data import Operation
from core.input_output_tables.data import (
    InputOutputRuleQuestionData,
    InputOutputTableQuestionData,
    Rule,
    RuleForm,
)
from core.input_output_tables.representation import (
    completed_sentence,
    headings,
    input_output_tile_question,
    rule,
    rule_equation,
    sentence,
    sentence_choice,
    sentence_instruction,
    sentence_with_blank,
    solution,
    statement,
    table_question,
    table_title,
)
from core.self_check_tiles import TileQuestion
from tests.data import DIVIDED_BY, GIFTS, MINUS, READING, SALE, SOCKS, TIMES

ADD, SUBTRACT, MULTIPLY, DIVIDE = Operation
SENTENCE, PLAIN, EXPLAINED = RuleForm

TIMES_8 = ((4, 32), (7, 56), (9, 72), (10, 80))
TIMES_8_SWAPPED = ((32, 4), (56, 7), (72, 9), (80, 10))


def test_table_question() -> None:
    """A table to choose asks for it after the rule."""
    data = InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8)
    assert table_question(data) == (
        "There are 8 socks in each package. Which table shows this relationship?"
    )


@pytest.mark.parametrize(
    ("data", "parts", "completed"),
    [
        (
            InputOutputRuleQuestionData(
                READING, "Ben", ((2, 10), (3, 15), (5, 25), (6, 30)), (MULTIPLY, 5), SENTENCE
            ),
            ("The number of months", "is equal to the number of books Ben reads."),
            "The number of months times 5 is equal to the number of books Ben reads.",
        ),
        # division takes the larger quantity first
        (
            InputOutputRuleQuestionData(SOCKS, None, TIMES_8_SWAPPED, (DIVIDE, 8), SENTENCE),
            ("The number of socks", "is equal to the number of packages."),
            "The number of socks divided by 8 is equal to the number of packages.",
        ),
    ],
)
def test_sentence(
    data: InputOutputRuleQuestionData, parts: tuple[str, str], completed: str
) -> None:
    """The sentence's parts go before and after the rule's operation and number."""
    assert (sentence(data), completed_sentence(data)) == (parts, completed)


@pytest.mark.parametrize(
    ("data", "options", "expected"),
    [
        # one operation: the sentence states it, and the choices are numbers
        (
            InputOutputRuleQuestionData(SOCKS, None, TIMES_8, (MULTIPLY, 8), SENTENCE),
            ((MULTIPLY, 10), (MULTIPLY, 9), (MULTIPLY, 6), (MULTIPLY, 8)),
            (
                "Choose the number that completes the sentence.",
                "The number of packages times ______ is equal to the number of socks.",
                ["10", "9", "6", "8"],
            ),
        ),
        # two operations: the choices are operations with numbers
        (
            InputOutputRuleQuestionData(SOCKS, None, TIMES_8_SWAPPED, (DIVIDE, 8), SENTENCE),
            ((MULTIPLY, 10), (DIVIDE, 10), (MULTIPLY, 8), (DIVIDE, 8)),
            (
                "Choose the operation and number that complete the sentence.",
                "The number of socks ______ is equal to the number of packages.",
                ["times 10", "divided by 10", "times 8", "divided by 8"],
            ),
        ),
    ],
)
def test_sentence_with_its_choices(
    data: InputOutputRuleQuestionData,
    options: tuple[Rule, ...],
    expected: tuple[str, str, list[str]],
) -> None:
    """A sentence to complete has its instruction, the sentence with a blank, and its choices."""
    assert (
        sentence_instruction(options),
        sentence_with_blank(data, options),
        [sentence_choice(option, options) for option in options],
    ) == expected


@pytest.mark.parametrize(
    ("data", "option", "expected"),
    [
        (
            InputOutputRuleQuestionData(SOCKS, None, TIMES_8, (MULTIPLY, 8), PLAIN),
            (MULTIPLY, 8),
            "The number of packages times 8 is equal to the number of socks.",
        ),
        # a wrong rule's statement, in the order of the table's own headings
        (
            InputOutputRuleQuestionData(SOCKS, None, TIMES_8, (MULTIPLY, 8), PLAIN),
            (DIVIDE, 6),
            "The number of packages divided by 6 is equal to the number of socks.",
        ),
        # explained: the context's rule with the option's number, then the reason
        (
            InputOutputRuleQuestionData(SOCKS, None, TIMES_8_SWAPPED, (DIVIDE, 8), EXPLAINED),
            (DIVIDE, 8),
            "There are 8 socks in each package, because the number of socks divided by 8 "
            "equals the number of packages.",
        ),
        (
            InputOutputRuleQuestionData(
                GIFTS, "Ana", ((6, 5), (4, 3), (8, 7), (9, 8)), (SUBTRACT, 1), EXPLAINED
            ),
            (SUBTRACT, 1),
            "Ana sends 1 free gift with each order, because the number of items sent minus 1 "
            "equals the number of items ordered.",
        ),
        (
            InputOutputRuleQuestionData(
                SALE, None, ((12, 18), (19, 25), (27, 33), (33, 39)), (ADD, 6), EXPLAINED
            ),
            (SUBTRACT, 9),
            "The sale price of each book is $9 less than the regular price, because the sale "
            "price minus 9 equals the regular price.",
        ),
    ],
)
def test_statement(data: InputOutputRuleQuestionData, option: Rule, expected: str) -> None:
    assert statement(data, option) == expected


def test_rule_equation_of_a_question_asking_for_the_rule() -> None:
    """The equation reads the rule from the answer, in the order of the table's headings."""
    data = InputOutputRuleQuestionData(SOCKS, None, TIMES_8_SWAPPED, (DIVIDE, 8), PLAIN)
    assert rule_equation(data) == f"Number of Socks {DIVIDED_BY} 8 = Number of Packages"


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            InputOutputTableQuestionData(SALE, None, ADD, 1, ()),
            ("The sale price of each book is $1 less than the regular price.", "Book Sale"),
        ),
        # a word agreeing with the number, and a name
        (
            InputOutputTableQuestionData(GIFTS, "Ana", ADD, 1, ()),
            ("Ana sends 1 free gift with each order.", "Ana's Orders"),
        ),
        (
            InputOutputTableQuestionData(GIFTS, "Ana", SUBTRACT, 12, ()),
            ("Ana sends 12 free gifts with each order.", "Ana's Orders"),
        ),
        (
            InputOutputTableQuestionData(READING, "Ben", DIVIDE, 5, ()),
            ("Ben reads 5 books every month.", "Ben's Reading"),
        ),
    ],
)
def test_rule_and_title(data: InputOutputTableQuestionData, expected: tuple[str, str]) -> None:
    assert (rule(data), table_title(data)) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, ()),
            ("Number of Packages", "Number of Socks"),
        ),
        (
            InputOutputTableQuestionData(SOCKS, None, DIVIDE, 8, ()),
            ("Number of Socks", "Number of Packages"),
        ),
        (
            InputOutputTableQuestionData(SALE, None, ADD, 6, ()),
            ("Sale Price ($)", "Regular Price ($)"),
        ),
        (
            InputOutputTableQuestionData(SALE, None, SUBTRACT, 6, ()),
            ("Regular Price ($)", "Sale Price ($)"),
        ),
    ],
)
def test_headings_put_the_smaller_quantity_first_for_addition_and_multiplication(
    data: InputOutputTableQuestionData, expected: tuple[str, str]
) -> None:
    assert headings(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            InputOutputTableQuestionData(
                SOCKS, None, MULTIPLY, 8, ((5, 40), (8, 64), (10, 80), (11, 88)), (), (1, 2, 3)
            ),
            f"Number of Packages {TIMES} 8 = Number of Socks\nNumber of Socks: 64, 80, 88",
        ),
        (
            InputOutputTableQuestionData(
                SOCKS, None, DIVIDE, 8, ((40, 5), (64, 8), (80, 10), (88, 11)), (3,), (0, 1)
            ),
            f"Number of Socks {DIVIDED_BY} 8 = Number of Packages\n"
            "Number of Socks: 88; Number of Packages: 5, 8",
        ),
        (
            InputOutputTableQuestionData(
                SALE, None, SUBTRACT, 6, ((18, 12), (25, 19), (33, 27), (39, 33)), (0, 2), (3,)
            ),
            f"Regular Price ($) {MINUS} 6 = Sale Price ($)\n"
            "Regular Price ($): 18, 33; Sale Price ($): 33",
        ),
        (
            InputOutputTableQuestionData(
                SALE, None, ADD, 6, ((12, 18), (19, 25), (27, 33), (33, 39)), (), (0, 1, 2)
            ),
            "Sale Price ($) + 6 = Regular Price ($)\nRegular Price ($): 18, 25, 33",
        ),
        # multiple choice leaves out nothing, so the entry is the rule alone
        (
            InputOutputTableQuestionData(
                SOCKS, None, MULTIPLY, 8, ((5, 40), (8, 64), (10, 80), (11, 88))
            ),
            f"Number of Packages {TIMES} 8 = Number of Socks",
        ),
    ],
)
def test_solution(data: InputOutputTableQuestionData, expected: str) -> None:
    assert solution(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            InputOutputTableQuestionData(
                SOCKS, None, MULTIPLY, 8, ((5, 40), (8, 64), (10, 80), (11, 88)), (), (2,)
            ),
            TileQuestion(
                prompt="There are 8 socks in each package.",
                answer="80",
                solution=f"Number of Packages {TIMES} 8 = Number of Socks\nNumber of Socks: 80",
            ),
        ),
        (
            InputOutputTableQuestionData(
                READING, "Ben", DIVIDE, 5, ((10, 2), (15, 3), (25, 5), (30, 6)), (1,), ()
            ),
            TileQuestion(
                prompt="Ben reads 5 books every month.",
                answer="15",
                solution=f"Books Read {DIVIDED_BY} 5 = Number of Months\nBooks Read: 15",
            ),
        ),
    ],
)
def test_input_output_tile_question(
    data: InputOutputTableQuestionData, expected: TileQuestion
) -> None:
    assert input_output_tile_question(data) == expected


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (
            InputOutputTableQuestionData(
                SOCKS, None, MULTIPLY, 8, ((5, 40), (8, 64), (10, 80), (11, 88)), (), (1, 2, 3)
            ),
            "A tile question needs one number left out, not 3.",
        ),
        (
            InputOutputTableQuestionData(
                SOCKS, None, MULTIPLY, 8, ((5, 40), (8, 64), (10, 80), (11, 88))
            ),
            "A tile question needs one number left out, not 0.",
        ),
    ],
)
def test_input_output_tile_question_errors(
    data: InputOutputTableQuestionData, message: str
) -> None:
    with pytest.raises(ValueError) as error:
        input_output_tile_question(data)
    assert str(error.value) == message
