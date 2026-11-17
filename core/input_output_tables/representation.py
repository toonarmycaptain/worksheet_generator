"""
What an input-output table question shows: the instructions and questions, the rule, the table's
title and headings, the sentences and statements of a table's rule, and the answer key's entry.
"""

import re
from collections.abc import Sequence

from core.basic_operations.data import Operation
from core.basic_operations.representation import SYMBOLS
from core.input_output_tables.data import (
    Blanks,
    ChoiceType,
    InputOutputQuestionData,
    InputOutputRuleQuestionData,
    InputOutputTableQuestionData,
    Rule,
    RuleForm,
)
from core.self_check_tiles import TileQuestion

INPUT_OUTPUT_TABLES_NAME = "Input-Output Tables"
INSTRUCTION = "Use each rule to fill in the missing numbers in its table."
TILES_INSTRUCTION = "Use each rule to find the missing number in its table."
TABLE_QUESTION = "Which table shows this relationship?"  # after the rule
STATEMENT_QUESTION = "Based on the table, which statement is true?"
# Above a table whose rule completes a sentence: with the operation and number, or the number only
SENTENCE_INSTRUCTION = "Choose the operation and number that complete the sentence."
NUMBER_INSTRUCTION = "Choose the number that completes the sentence."
SENTENCE_BLANK = "______"  # where the chosen words go in the sentence
OPERATION_WORDS = {
    Operation.ADD: "plus",
    Operation.SUBTRACT: "minus",
    Operation.MULTIPLY: "times",
    Operation.DIVIDE: "divided by",
}
BLANKS_NAMES = {
    Blanks.INPUTS: "Inputs",
    Blanks.OUTPUTS: "Outputs",
    Blanks.INPUTS_AND_OUTPUTS: "Inputs and outputs",
}
CHOICE_TYPE_NAMES = {
    ChoiceType.TABLE: "Choose the table that matches a rule",
    ChoiceType.SENTENCE: "Complete a sentence about a table",
    ChoiceType.STATEMENT: "Choose the true statement about a table",
}

# The operations that take a context's smaller quantity to its larger, making the smaller the input
SMALLER_FIRST = frozenset({Operation.ADD, Operation.MULTIPLY})

# A word agreeing with the rule's number, singular first: {n:point|points}
_AGREEING = re.compile(r"\{n:([^|}]*)\|([^}]*)\}")


def rule(data: InputOutputQuestionData) -> str:
    """Return the rule as the context states it, with its number and any name filled in."""
    return _fill(data.context.rule, data.number, data.name)


def table_question(data: InputOutputTableQuestionData) -> str:
    """Return a multiple-choice table's question: the rule, then which table shows it."""
    return f"{rule(data)} {TABLE_QUESTION}"


def table_title(data: InputOutputQuestionData) -> str:
    """Return the title above the table, with any name filled in."""
    return _fill(data.context.title, data.number, data.name)


def headings(data: InputOutputQuestionData) -> tuple[str, str]:
    """
    Return the headings of the inputs and of the outputs: the smaller quantity's first for
    addition and multiplication, and the larger quantity's first for subtraction and division.
    """
    context = data.context
    if data.operation in SMALLER_FIRST:
        return context.smaller, context.larger
    return context.larger, context.smaller


def nouns(data: InputOutputQuestionData) -> tuple[str, str]:
    """
    Return the inputs' and the outputs' nouns, in the order of ``headings``, with any name filled
    in, as in ("the number of packages", "the number of socks").
    """
    context = data.context
    smaller = _fill(context.smaller_noun, data.number, data.name)
    larger = _fill(context.larger_noun, data.number, data.name)
    return (smaller, larger) if data.operation in SMALLER_FIRST else (larger, smaller)


def sentence(data: InputOutputRuleQuestionData) -> tuple[str, str]:
    """
    Return the sentence to complete with the rule's operation and number, as the parts before and
    after them: ("The number of months", "is equal to the number of books Maria reads.").
    """
    input_noun, output_noun = nouns(data)
    return _capitalized(input_noun), f"is equal to {output_noun}."


def sentence_with_blank(data: InputOutputRuleQuestionData, options: Sequence[Rule]) -> str:
    """
    Return the sentence to complete with one of ``options``, with a blank where it goes: the
    rule's operation and number, or when the options share one operation, which the sentence
    states, its number only, as in "The number of cookies minus ______ is equal to the number of
    muffins."
    """
    start, end = sentence(data)
    if _one_operation(options):
        start = f"{start} {OPERATION_WORDS[data.operation]}"
    return f"{start} {SENTENCE_BLANK} {end}"


def sentence_choice(option: Rule, options: Sequence[Rule]) -> str:
    """
    Return how ``option`` completes the sentence: its operation and number, as in "divided by 7",
    or when the options share one operation, its number only.
    """
    operation, number = option
    return str(number) if _one_operation(options) else f"{OPERATION_WORDS[operation]} {number}"


def sentence_instruction(options: Sequence[Rule]) -> str:
    """
    Return the instruction above a sentence to complete: with the operation and number, or when
    the options share one operation, the number only.
    """
    return NUMBER_INSTRUCTION if _one_operation(options) else SENTENCE_INSTRUCTION


def completed_sentence(data: InputOutputRuleQuestionData) -> str:
    """Return the sentence completed with the rule's operation and number."""
    start, end = sentence(data)
    return f"{start} {OPERATION_WORDS[data.operation]} {data.number} {end}"


def statement(data: InputOutputRuleQuestionData, option: Rule) -> str:
    """
    Return the statement that the table follows the rule ``option``, worded as ``data.form``
    asks: the completed sentence, or for ``RuleForm.EXPLAINED``, the context's rule with the
    option's number and the sentence as its reason, as in "There are 8 socks in each package,
    because the number of packages times 8 equals the number of socks."
    """
    operation, number = option
    input_noun, output_noun = nouns(data)
    reason = f"{input_noun} {OPERATION_WORDS[operation]} {number}"
    if data.form is RuleForm.EXPLAINED:
        fact = _fill(data.context.rule, number, data.name).removesuffix(".")
        return f"{fact}, because {reason} equals {output_noun}."
    return f"{_capitalized(reason)} is equal to {output_noun}."


def missing_numbers(data: InputOutputTableQuestionData) -> tuple[int, ...]:
    """Return the numbers left out of the table, in the order of its pairs."""
    return tuple(
        output if index in data.blank_outputs else input_
        for index, (input_, output) in enumerate(data.answer)
        if index in data.blank_inputs or index in data.blank_outputs
    )


def rule_equation(data: InputOutputQuestionData) -> str:
    """
    Return the rule as an equation of the headings, from input to output, with the operation's
    sign from ``SYMBOLS``, as in "Number of Packages x 8 = Number of Socks".
    """
    input_heading, output_heading = headings(data)
    return f"{input_heading} {SYMBOLS[data.operation]} {data.number} = {output_heading}"


def solution(data: InputOutputTableQuestionData) -> str:
    """
    Return the answer key's entry: the rule as an equation, then for a table to complete, on a
    new line, the numbers left out under each heading, in the order of the pairs, as in
    "Number of Packages: 11; Number of Socks: 64, 80".
    """
    input_heading, output_heading = headings(data)
    columns = ((input_heading, 0, data.blank_inputs), (output_heading, 1, data.blank_outputs))
    missing = [
        f"{heading}: {', '.join(str(data.answer[index][column]) for index in indexes)}"
        for heading, column, indexes in columns
        if indexes
    ]
    if not missing:
        return rule_equation(data)
    return f"{rule_equation(data)}\n{'; '.join(missing)}"


def input_output_tile_question(data: InputOutputTableQuestionData) -> TileQuestion:
    """
    Convert a table with one number left out to a ``TileQuestion`` for the self-check tiles
    sheet: the prompt is the rule, the answer is the missing number, and the solution is the
    answer key's entry.

    Raises ``ValueError`` if the table leaves out other than one number.
    """
    missing = missing_numbers(data)
    if len(missing) != 1:
        raise ValueError(f"A tile question needs one number left out, not {len(missing)}.")
    return TileQuestion(prompt=rule(data), answer=str(missing[0]), solution=solution(data))


def _fill(text: str, number: int, name: str | None) -> str:
    """Fill the slots of a context's text: the words agreeing with ``number``, then the rest."""
    agreeing = _AGREEING.sub(lambda match: match[1] if number == 1 else match[2], text)
    return agreeing.format(n=number, name=name)


def _one_operation(options: Sequence[Rule]) -> bool:
    """Return whether the options all have the same operation, so differ only in number."""
    return len({operation for operation, _ in options}) == 1


def _capitalized(text: str) -> str:
    """Return ``text`` with its first letter upper case."""
    return text[:1].upper() + text[1:]
