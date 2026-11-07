"""
The worksheet kinds the site serves, and how to render each one.

Each kind pairs an options schema, validated from the query string, with an adapter that
renders the PDF into a buffer. A legacy kind's adapter does what its script's ``main()`` does,
and its option names match the script's CLI flags (``--no-regroup`` becomes ``no_regroup``).
Every boolean defaults to False, so an unticked HTML checkbox, which the browser does not
submit, means the default.

Temporary: the phase 5 CLI and the shared core replace these adapters.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from io import BytesIO
from typing import Annotated, Any, BinaryIO, Literal, Self

from ninja import Field, Schema
from pydantic import JsonValue, model_validator

from core.base_ten_blocks import (
    BLOCKS_QUESTION_NAMES,
    DEFAULT_SMALLEST_BLOCKS_NUMBER,
    BlocksQuestionType,
    count_possible_blocks_questions,
    generate_blocks_questions,
)
from core.basic_operations.data import Operation, Unknown
from core.basic_operations.generator import (
    DEFAULT_LARGEST_DIVIDEND,
    DEFAULT_LARGEST_DIVISOR,
    DEFAULT_LARGEST_OPERAND,
    LARGEST_WORD_PROBLEM_NUMBER,
    MAXIMUM_OPERAND,
    SMALLEST_WORD_PROBLEM_NUMBER,
    count_possible_missing_number_questions,
    count_possible_sheet_questions,
    count_possible_word_problems,
    generate_basic_operation_questions,
    generate_missing_number_questions,
    generate_word_problems,
)
from core.basic_operations.regrouping import REGROUPING_NAMES, Regrouping
from core.basic_operations.representation import (
    LARGEST_BLOCKS_OPERAND,
    OPERATION_NAMES,
    REPRESENTATION_NAMES,
    REPRESENTATION_OPERATIONS,
    Representation,
    basic_operation_tile_question,
    missing_number_tile_question,
    operations_name,
    word_problems_title,
)
from core.placevalue.data import PlaceValueForm
from core.placevalue.generator import (
    DEFAULT_LARGEST_NUMBER,
    DEFAULT_SMALLEST_NUMBER,
    generate_place_value_questions,
)
from core.placevalue.representation import (
    FORM_NAMES,
    LARGEST_BLOCKS_NUMBER,
    LARGEST_NUMBER,
    place_value_tile_question,
)
from core.self_check_tiles import SLOTS, TileQuestion, conventional_slot_of, random_slot_of
from core.wrong_answers import WRONG_ANSWER_COUNT
from render.pdf.base_ten_blocks_worksheet import render_base_ten_blocks_worksheet
from render.pdf.basic_operations_worksheet import (
    render_basic_operations_worksheet,
    render_missing_number_worksheet,
)
from render.pdf.page import Header
from render.pdf.place_value_worksheet import render_place_value_worksheet
from render.pdf.self_check_tiles_worksheet import render_self_check_tiles_worksheet
from render.pdf.word_problems_worksheet import render_word_problems_worksheet
from worksheet_generator._imported import generate_block_word_problems as block
from worksheet_generator._imported import generate_data_graph_mc_word_problems as data_graph_mc
from worksheet_generator._imported import generate_data_graph_word_problems as data_graph
from worksheet_generator._imported import (
    generate_multiplication_mc_word_problems as multiplication_mc,
)
from worksheet_generator._imported import generate_number_line_mc_word_problems as number_line_mc
from worksheet_generator._imported import generate_number_line_word_problems as number_line
from worksheet_generator._imported import generate_strip_word_problems as strip
from worksheet_generator._imported import generate_word_problems as word
from worksheet_generator._imported import generate_worksheet as worksheet
from worksheet_generator._imported import wp_common

# Largest integer JavaScript holds exactly, so a seed survives a trip through the browser.
# Seeds are for development and tests; users get no promise that a seed remakes a sheet.
MAX_SEED = 2**53 - 1
MAX_PROBLEMS = 20  # caps the work one request asks of the server; renderers add pages as needed
# A basic operations sheet's missing number -> the operand left out, or None for mixed
MISSING_NUMBERS = {"dividend": Unknown.FIRST, "divisor": Unknown.SECOND, "mixed": None}

Title = Annotated[str, Field(min_length=1, max_length=80)]
Label = Annotated[str, Field(max_length=40)]
Problems = Annotated[int, Field(ge=1, le=MAX_PROBLEMS)]
ListStyle = Literal["mix", "grid", "commas"]
OperationChoice = Literal["add", "subtract", "multiply", "divide"]  # an Operation value
# A PlaceValueForm value, or mixed, where the form is chosen per question.
FormChoice = Literal["standard", "expanded", "unit", "expanded_notation", "word", "mixed"]
# Operations checkbox labels: each operation's sheet title
OPERATION_LABELS: dict[str, JsonValue] = {
    operation.value: name for operation, name in OPERATION_NAMES.items()
}
# From and To dropdown labels: each form's name, plus mixed
FORM_CHOICE_LABELS: dict[str, JsonValue] = {
    **{form.value: name for form, name in FORM_NAMES.items()},
    "mixed": "mixed",
}
# Representation dropdown labels: each representation's name
REPRESENTATION_LABELS: dict[str, JsonValue] = {
    representation.value: name for representation, name in REPRESENTATION_NAMES.items()
}
BlocksQuestionChoice = Literal["write_number", "add", "subtract"]  # a BlocksQuestionType value
# Base-ten blocks questions checkbox labels: each type's name
BLOCKS_QUESTION_LABELS: dict[str, JsonValue] = {
    question_type.value: name for question_type, name in BLOCKS_QUESTION_NAMES.items()
}
RegroupingChoice = Literal["never", "mixed", "always"]  # a Regrouping value
# Regrouping radio button labels: each choice's name
REGROUPING_LABELS: dict[str, JsonValue] = {
    regrouping.value: name for regrouping, name in REGROUPING_NAMES.items()
}
AnswerKey = Annotated[bool, Field(title="Add an answer key page")]
NameDateLine = Annotated[bool, Field(title="Add Name/Date blanks")]
SelfCheckTiles = Annotated[bool, Field(title="Self-check tile answers")]
# simple: a conventional picture; complex: tiles in arbitrary slots
TilePattern = Annotated[
    Literal["simple", "complex"], Field(title="Pattern", json_schema_extra={"input": "radio"})
]


def _at_most_one_question_per_tile(problems: int) -> None:
    """Raise ``ValueError`` if ``problems`` exceeds the tile count, since question n uses tile n."""
    if problems > SLOTS:
        raise ValueError(f"problems: self-check tiles has {SLOTS} tiles, so at most {SLOTS}")


def _smallest_raise(count: Callable[[int], int], needed: int, current: int, top: int) -> int | None:
    """
    Return the smallest limit above ``current``, up to ``top``, that allows ``needed`` questions.

    ``count`` gives the number of possible questions at a value of one limit. Every such count
    is non-decreasing in its limit, so a binary search finds the value in a few evaluations.
    Returns ``None`` if even ``top`` falls short.
    """
    if current >= top or count(top) < needed:
        return None
    low, high = current + 1, top
    while low < high:
        middle = (low + high) // 2
        if count(middle) >= needed:
            high = middle
        else:
            low = middle + 1
    return low


def _operations(ticked: Sequence[str]) -> list[Operation]:
    """Return the ticked operations, each once, in the order of ``Operation``."""
    return [operation for operation in Operation if operation.value in ticked]


def _too_many_problems(
    possible: int, repeats: str, limits: str, raises: Mapping[str, int | None]
) -> ValueError:
    """
    Return the error for requesting more problems than the limits allow, with suggested fixes.

    ``possible`` is how many problems ``limits`` allow without ``repeats``. ``raises`` maps each
    limit, named as in the message, to the smallest value that would allow the requested
    problems, or to ``None`` when raising that limit alone cannot.
    """
    fixes = [f"Lower problems to {possible}"]
    fixes += [
        f"raise the {limit} to {value:,}" for limit, value in raises.items() if value is not None
    ]
    return ValueError(
        f"problems: at most {possible} without {repeats} for that {limits}. {', or '.join(fixes)}."
    )


class Options(Schema):
    """Options common to every legacy kind. Without a seed, the endpoint picks a random one."""

    seed: int | None = Field(None, ge=0, le=MAX_SEED)
    name_line: NameDateLine = False


class HeaderOptions(Schema):
    """Options for the page header and footer of every core kind. Each kind sets its title."""

    title: Title
    label: Label = "Sheet A"
    name_line: NameDateLine = False

    def header(self) -> Header:
        """The page header these options describe, as the renderers take it."""
        return Header(title=self.title, label=self.label, name_line=self.name_line)


class BasicOperationOptions(HeaderOptions):
    """
    Options for the basic operations kind, built on the core. There is no seed: every sheet is new.
    """

    title: Title = OPERATION_NAMES[Operation.ADD]  # the chosen operations' name by default
    problems: Problems = 8
    # Each question's operation is drawn at random from those ticked, or with tiles, dealt out
    # evenly among them.
    operations: list[OperationChoice] = Field(
        ["add"], min_length=1, title="Operations", json_schema_extra={"labels": OPERATION_LABELS}
    )
    # Division alone: any value but answer produces fill-in equations, such as □ ÷ 4 = 7
    missing_number: Literal["answer", "dividend", "divisor", "mixed"] = Field(
        "answer", title="Missing number"
    )
    max_number: int = Field(
        DEFAULT_LARGEST_OPERAND, ge=1, le=MAXIMUM_OPERAND, title="Largest number"
    )
    # Division's limits, used instead of max_number; the quotient follows from them.
    largest_dividend: int = Field(
        DEFAULT_LARGEST_DIVIDEND, ge=1, le=MAXIMUM_OPERAND, title="Largest dividend"
    )
    largest_divisor: int = Field(
        DEFAULT_LARGEST_DIVISOR, ge=1, le=MAXIMUM_OPERAND, title="Largest divisor"
    )
    answer_key: AnswerKey = False
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @property
    def chosen_operations(self) -> list[Operation]:
        """The ticked operations, each once, in the order of ``Operation``."""
        return _operations(self.operations)

    @model_validator(mode="after")
    def _title_follows_the_operations(self) -> Self:
        # The default is the name of the default operation. A request that ticks others and
        # gives no title gets their name.
        if "title" not in self.model_fields_set:
            self.title = operations_name(self.chosen_operations)
        return self

    @model_validator(mode="after")
    def _enough_different_questions(self) -> Self:
        operations = self.chosen_operations
        if self.missing_number != "answer" and operations != [Operation.DIVIDE]:
            if Operation.DIVIDE in operations:
                raise ValueError(
                    "missing_number: only division by itself has a missing dividend or divisor"
                )
            raise ValueError("missing_number: only division has a missing dividend or divisor")
        if self.self_check_tiles:
            _at_most_one_question_per_tile(self.problems)

        def possible_with(largest: int, dividend: int, divisor: int) -> int:
            if self.missing_number != "answer":
                # No fact family twice (28 ÷ 4 = 7 and 28 ÷ 7 = 4), and with tiles no answer
                # twice.
                return count_possible_missing_number_questions(
                    Operation.DIVIDE,
                    MISSING_NUMBERS[self.missing_number],
                    high=dividend,
                    largest_divisor=divisor,
                    distinct_answers=self.self_check_tiles,
                    up_to=self.problems,
                )
            # A reversed pair counts as a repeat. Without tiles, any one operation may be drawn
            # for every question. With tiles, each tile needs a distinct answer, and the
            # operations are dealt out evenly.
            return count_possible_sheet_questions(
                operations,
                high=largest,
                largest_dividend=dividend,
                largest_divisor=divisor,
                distinct_answers=self.self_check_tiles,
                up_to=self.problems,
            )

        possible = possible_with(self.max_number, self.largest_dividend, self.largest_divisor)
        if self.problems <= possible:
            return self
        division = Operation.DIVIDE in operations
        others = any(operation is not Operation.DIVIDE for operation in operations)
        raises: dict[str, int | None] = {}
        if others:
            raises["largest number"] = _smallest_raise(
                lambda largest: possible_with(largest, self.largest_dividend, self.largest_divisor),
                self.problems,
                self.max_number,
                MAXIMUM_OPERAND,
            )
        if division:
            raises["largest dividend"] = _smallest_raise(
                lambda dividend: possible_with(self.max_number, dividend, self.largest_divisor),
                self.problems,
                self.largest_dividend,
                MAXIMUM_OPERAND,
            )
            raises["largest divisor"] = _smallest_raise(
                lambda divisor: possible_with(self.max_number, self.largest_dividend, divisor),
                self.problems,
                self.largest_divisor,
                MAXIMUM_OPERAND,
            )
        if division and others:
            limits = "largest number, dividend and divisor"
        elif division:
            limits = "largest dividend and divisor"
        else:
            limits = "largest number"
        repeats = "repeated answers" if self.self_check_tiles else "repeats"
        raise _too_many_problems(possible, repeats, limits, raises)


class PlaceValueOptions(HeaderOptions):
    """Options for the place-value kind, built on the core. There is no seed: every sheet is new."""

    title: Title = "Place Value"
    problems: Problems = 8
    given: FormChoice = Field(
        "standard", title="From", json_schema_extra={"labels": FORM_CHOICE_LABELS}
    )
    asked: FormChoice = Field(
        "expanded", title="To", json_schema_extra={"labels": FORM_CHOICE_LABELS}
    )
    min_number: int = Field(
        DEFAULT_SMALLEST_NUMBER, ge=1, le=LARGEST_NUMBER, title="Smallest number"
    )
    max_number: int = Field(DEFAULT_LARGEST_NUMBER, ge=1, le=LARGEST_NUMBER, title="Largest number")
    answer_key: AnswerKey = False
    multiple_choice: bool = Field(False, title="Multiple choice")
    # Tiles replace the answer lines or options, so they take precedence over multiple choice.
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @property
    def shows_choices(self) -> bool:
        """Whether the questions list options: multiple choice is ticked and tiles are not."""
        return self.multiple_choice and not self.self_check_tiles

    @model_validator(mode="after")
    def _a_question_can_be_made(self) -> Self:
        if self.given == self.asked != "mixed":
            raise ValueError("asked: must be a different form from given")
        if self.min_number > self.max_number:
            raise ValueError("min_number: must not be more than the largest number")
        possible = self.max_number - self.min_number + 1
        if self.problems > possible:
            needed = self.min_number + self.problems - 1
            raises = {"largest number": needed if needed <= LARGEST_NUMBER else None}
            raise _too_many_problems(possible, "repeats", "range of numbers", raises)
        # The wrong answers come from the same range, and are never the correct one.
        if self.shows_choices and self.max_number - self.min_number < WRONG_ANSWER_COUNT:
            raise ValueError(
                f"max_number: must be at least {WRONG_ANSWER_COUNT} more than the smallest "
                f"number, for {WRONG_ANSWER_COUNT} wrong answers"
            )
        # The numbers are distinct, so the answers are too.
        if self.self_check_tiles:
            _at_most_one_question_per_tile(self.problems)
        return self


class WordProblemOptions(HeaderOptions):
    """
    Options for the word problems kind, built on the core. There is no seed: every sheet is new.
    """

    # the representation's title by default
    title: Title = word_problems_title(Representation.STRIP)
    problems: Problems = 4
    # Each problem's operation is drawn at random from those ticked.
    operations: list[OperationChoice] = Field(
        ["add", "subtract"],
        min_length=1,
        title="Operations",
        json_schema_extra={"labels": OPERATION_LABELS},
    )
    # Addition and subtraction only: every number in the problem, its answer included. It's at
    # least the smallest sum, which leaves room for a subtraction too.
    max_number: int = Field(
        LARGEST_WORD_PROBLEM_NUMBER,
        ge=2 * SMALLEST_WORD_PROBLEM_NUMBER,
        le=LARGEST_WORD_PROBLEM_NUMBER,
        title="Largest number",
    )
    representation: Literal["strip", "none", "number_line", "blocks"] = Field(
        "strip", title="Representation", json_schema_extra={"labels": REPRESENTATION_LABELS}
    )
    no_hints: bool = Field(False, title="Leave out the hints")  # text only has none
    black_and_white: bool = Field(False, title="Black and white blocks")  # for photocopying
    answer_key: AnswerKey = False
    # Tiles replace the answer lines with an answer bank page.
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @property
    def largest_operand(self) -> int:
        """The largest operand the representation can show: base-ten blocks show at most 599."""
        if Representation(self.representation) is Representation.BLOCKS:
            return LARGEST_BLOCKS_OPERAND
        return LARGEST_WORD_PROBLEM_NUMBER

    @model_validator(mode="after")
    def _title_follows_the_representation(self) -> Self:
        # The default is the default representation's title. A request that picks another and gives
        # no title gets its title.
        if "title" not in self.model_fields_set:
            self.title = word_problems_title(Representation(self.representation))
        return self

    @model_validator(mode="after")
    def _representation_shows_the_operations(self) -> Self:
        representation = Representation(self.representation)
        shown = REPRESENTATION_OPERATIONS[representation]
        if not shown.issuperset(_operations(self.operations)):
            names = operations_name([operation for operation in Operation if operation in shown])
            raise ValueError(
                f"operations: {REPRESENTATION_NAMES[representation]} show only {names.lower()}"
            )
        return self

    @model_validator(mode="after")
    def _enough_different_problems(self) -> Self:
        if self.self_check_tiles:
            _at_most_one_question_per_tile(self.problems)
        # Any one operation may be drawn for every problem, and with tiles each tile needs a
        # distinct answer.
        operations = _operations(self.operations)

        def possible_with(largest: int) -> int:
            return count_possible_word_problems(
                operations,
                distinct_answers=self.self_check_tiles,
                up_to=self.problems,
                largest_number=largest,
                largest_operand=self.largest_operand,
            )

        possible = possible_with(self.max_number)
        if self.problems <= possible:
            return self
        repeats = "repeated answers" if self.self_check_tiles else "repeats"
        if {Operation.ADD, Operation.SUBTRACT}.isdisjoint(operations):
            # Multiplication and division have no number limits to raise.
            raise _too_many_problems(possible, repeats, "choice of operations", {})
        raise_to = _smallest_raise(
            possible_with, self.problems, self.max_number, LARGEST_WORD_PROBLEM_NUMBER
        )
        if {Operation.ADD, Operation.SUBTRACT}.issuperset(operations):
            limits = "largest number"
        else:
            limits = "choice of operations and largest number"
        raise _too_many_problems(possible, repeats, limits, {"largest number": raise_to})


class BaseTenBlocksOptions(HeaderOptions):
    """
    Options for the base-ten blocks kind, built on the core. There is no seed: every sheet is new.
    """

    title: Title = "Base-Ten Blocks"
    problems: Problems = 6
    # The problems are shared evenly among the ticked questions, then shuffled.
    questions: list[BlocksQuestionChoice] = Field(
        ["write_number", "add", "subtract"],
        min_length=1,
        title="Questions",
        json_schema_extra={"labels": BLOCKS_QUESTION_LABELS},
    )
    # Every number on the sheet, answers included. Blocks are drawn for numbers up to
    # LARGEST_BLOCKS_OPERAND, so the smallest can be no more.
    min_number: int = Field(
        DEFAULT_SMALLEST_BLOCKS_NUMBER, ge=1, le=LARGEST_BLOCKS_OPERAND, title="Smallest number"
    )
    max_number: int = Field(
        LARGEST_BLOCKS_NUMBER, ge=1, le=LARGEST_BLOCKS_NUMBER, title="Largest number"
    )
    # Addition and subtraction only
    regrouping: RegroupingChoice = Field(
        "mixed",
        title="Regrouping",
        json_schema_extra={"input": "radio", "labels": REGROUPING_LABELS},
    )
    black_and_white: bool = Field(False, title="Black and white blocks")  # for photocopying
    answer_key: AnswerKey = False
    # Tiles replace the answer boxes with an answer bank page.
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @model_validator(mode="after")
    def _enough_different_questions(self) -> Self:
        if self.self_check_tiles:
            _at_most_one_question_per_tile(self.problems)
        if self.min_number > self.max_number:
            raise ValueError("min_number: must not be more than the largest number")
        # The problems are shared evenly among the types, and with tiles each tile needs a
        # distinct answer.
        types = _blocks_question_types(self.questions)
        regrouping = Regrouping(self.regrouping)

        def possible_with(largest: int, types: Sequence[BlocksQuestionType] = types) -> int:
            return count_possible_blocks_questions(
                types,
                smallest=self.min_number,
                largest=largest,
                regrouping=regrouping,
                distinct_answers=self.self_check_tiles,
                up_to=self.problems,
            )

        possible = possible_with(self.max_number)
        if self.problems <= possible:
            return self
        raise_to = _smallest_raise(
            possible_with, self.problems, self.max_number, LARGEST_BLOCKS_NUMBER
        )
        if possible == 0:
            # Fewer problems can't help: a ticked question can't be made at all.
            stuck = [kind for kind in types if possible_with(self.max_number, [kind]) == 0]
            stuck_names = [BLOCKS_QUESTION_NAMES[kind].lower() for kind in stuck]
            names = " or ".join(stuck_names)
            which = {
                Regrouping.MIXED: "",
                Regrouping.ALWAYS: " that regroup",
                Regrouping.NEVER: " without regrouping",
            }[regrouping]
            fixes = []
            if self.min_number > 1:
                fixes.append("lower the smallest number")
            if raise_to is not None:
                fixes.append(f"raise the largest number to {raise_to:,}")
            if regrouping is not Regrouping.MIXED:
                fixes.append("change the regrouping")
            fixes.append("untick " + " and ".join(stuck_names))
            raise ValueError(
                f"min_number: no {names} questions{which} fit numbers from {self.min_number:,} "
                f"to {self.max_number:,}. {', or '.join(fixes).capitalize()}."
            )
        repeats = "repeated answers" if self.self_check_tiles else "repeats"
        limits = "range of numbers"
        if regrouping is not Regrouping.MIXED and types != [BlocksQuestionType.WRITE_NUMBER]:
            limits += " and regrouping"
        raise _too_many_problems(possible, repeats, limits, {"largest number": raise_to})


def _blocks_question_types(ticked: Sequence[str]) -> list[BlocksQuestionType]:
    """Return the ticked question types, each once, in the order of ``BlocksQuestionType``."""
    return [question_type for question_type in BlocksQuestionType if question_type.value in ticked]


class BlockOptions(Options):
    title: Title = "Base-Ten Block Word Problems"
    label: Label = "Sheet A"
    problems: Problems = 4


class WordOptions(Options):
    title: Title = "Addition & Subtraction Word Problems"
    label: Label = "Sheet A"
    problems: Problems = 6


class StripOptions(Options):
    title: Title = "Word Problems — Strip Diagrams"
    label: Label = "Day 2 · Sheet A"
    problems: Problems = 4
    answer_key: AnswerKey = False


class NumberLineOptions(Options):
    title: Title = "Word Problems — Number Lines"
    label: Label = "Day 3 · Sheet A"
    problems: Problems = 4


class NumberLineMCOptions(Options):
    title: Title = "Word Problems — Number Lines (Multiple Choice)"
    label: Label = "Day 3 · Sheet A"
    problems: Problems = 4


class MultiplicationMCOptions(Options):
    title: Title = "Multiplication Word Problems — Pick the Models"
    label: Label = "Sheet A"
    problems: Problems = 4
    # At least 3 and 6, so there is always a fact other than 2 x 2 to draw from.
    max_factor: int = Field(12, ge=3, le=12, title="Largest factor")
    max_product: int = Field(100, ge=6, le=100, title="Largest product")
    no_jump_labels: bool = Field(False, title="Leave the number-line jumps unnumbered")


class DataGraphOptions(Options):
    title: Title = "Data and Graphs — Read, Complete, Solve"
    label: Label = "Sheet A"
    problems: Problems = 4
    list_style: ListStyle = Field("mix", title="Show lists of numbers as")


class DataGraphMCOptions(Options):
    title: Title = "Data and Graphs — Pick the Matching Graph"
    label: Label = "Sheet A"
    problems: Problems = 4
    list_style: ListStyle = Field("mix", title="Show lists of numbers as")


class WorksheetOptions(Options):
    title: Title = "Base-Ten Blocks: 3-Digit Addition & Subtraction"
    represent: int = Field(2, ge=0, le=MAX_PROBLEMS, title="“Write the number” problems")
    add: int = Field(2, ge=0, le=MAX_PROBLEMS, title="Addition problems")
    sub: int = Field(2, ge=0, le=MAX_PROBLEMS, title="Subtraction problems")
    # Mirrors the legacy --no-regroup, which doesn't avoid regrouping despite its help
    # text: the default makes every problem regroup, and this flag gives a random mix.
    # Kept as-is; an always/mixed/never choice is planned for the shared core.
    no_regroup: bool = Field(False, title="Mix in problems without regrouping")
    bw: bool = Field(False, title="Black and white (saves toner)")

    @model_validator(mode="after")
    def _has_problems(self) -> Self:
        if not 1 <= self.represent + self.add + self.sub <= MAX_PROBLEMS:
            raise ValueError(f"represent + add + sub must be 1 to {MAX_PROBLEMS}")
        return self


def _basic_operations(o: BasicOperationOptions, out: BinaryIO) -> None:
    # Division's largest operand is its dividend. Only division uses largest_divisor.
    if o.missing_number != "answer":
        _missing_number(o, Operation.DIVIDE, out)
    elif o.self_check_tiles:
        # The answer bank replaces the options, so there are no wrong answers.
        questions = generate_basic_operation_questions(
            o.problems,
            o.chosen_operations,
            high=o.max_number,
            largest_dividend=o.largest_dividend,
            largest_divisor=o.largest_divisor,
            wrong_answer_count=0,
            distinct_answers=True,
        )
        _render_tiles(
            o, [basic_operation_tile_question(question.data) for question in questions], out
        )
    else:
        questions = generate_basic_operation_questions(
            o.problems,
            o.chosen_operations,
            high=o.max_number,
            largest_dividend=o.largest_dividend,
            largest_divisor=o.largest_divisor,
        )
        render_basic_operations_worksheet(
            questions=questions,
            path=out,
            header=o.header(),
            answer_key=o.answer_key,
        )


def _missing_number(o: BasicOperationOptions, operation: Operation, out: BinaryIO) -> None:
    """Render missing-number equations, as a fill-in sheet or a self-check tiles sheet."""
    questions = generate_missing_number_questions(
        o.problems,
        operation,
        MISSING_NUMBERS[o.missing_number],
        high=o.largest_dividend,
        largest_divisor=o.largest_divisor,
        distinct_answers=o.self_check_tiles,
    )
    if o.self_check_tiles:
        _render_tiles(
            o, [missing_number_tile_question(question.data) for question in questions], out
        )
    else:
        render_missing_number_worksheet(
            questions=questions,
            path=out,
            header=o.header(),
            answer_key=o.answer_key,
        )


def _place_value(o: PlaceValueOptions, out: BinaryIO) -> None:
    questions = generate_place_value_questions(
        o.problems,
        _form(o.given),
        _form(o.asked),
        low=o.min_number,
        high=o.max_number,
        wrong_answer_count=WRONG_ANSWER_COUNT if o.shows_choices else 0,
    )
    if o.self_check_tiles:
        _render_tiles(o, [place_value_tile_question(question.data) for question in questions], out)
    else:
        render_place_value_worksheet(
            questions=questions,
            path=out,
            header=o.header(),
            answer_key=o.answer_key,
        )


def _form(choice: FormChoice) -> PlaceValueForm | None:
    """Return the chosen form, or ``None`` for mixed, which the core resolves per question."""
    return None if choice == "mixed" else PlaceValueForm(choice)


def _render_tiles(
    o: BasicOperationOptions | PlaceValueOptions, questions: Sequence[TileQuestion], out: BinaryIO
) -> None:
    """Render a self-check tiles sheet for ``questions``, with slots for the requested pattern."""
    render_self_check_tiles_worksheet(
        questions=questions,
        slot_of=_tile_slots(o),
        path=out,
        header=o.header(),
        answer_key=o.answer_key,
    )


def _tile_slots(
    o: BasicOperationOptions | PlaceValueOptions | WordProblemOptions | BaseTenBlocksOptions,
) -> Sequence[int]:
    """Return the slot of each question's answer, for the requested tile pattern."""
    make_slots = conventional_slot_of if o.tile_pattern == "simple" else random_slot_of
    return make_slots(o.problems)


def _word_problems(o: WordProblemOptions, out: BinaryIO) -> None:
    representation = Representation(o.representation)
    render_word_problems_worksheet(
        questions=generate_word_problems(
            o.problems,
            _operations(o.operations),
            distinct_answers=o.self_check_tiles,
            # No comparisons on strip or blocks sheets: a strip shows parts making a whole, and
            # blocks show the first number with the second crossed out, taken away.
            comparisons=representation not in (Representation.STRIP, Representation.BLOCKS),
            largest_number=o.max_number,
            largest_operand=o.largest_operand,
        ),
        path=out,
        header=o.header(),
        answer_key=o.answer_key,
        representation=representation,
        hints=not o.no_hints,
        slot_of=_tile_slots(o) if o.self_check_tiles else None,
        black_and_white=o.black_and_white,
    )


def _base_ten_blocks(o: BaseTenBlocksOptions, out: BinaryIO) -> None:
    render_base_ten_blocks_worksheet(
        questions=generate_blocks_questions(
            o.problems,
            _blocks_question_types(o.questions),
            smallest=o.min_number,
            largest=o.max_number,
            regrouping=Regrouping(o.regrouping),
            distinct_answers=o.self_check_tiles,
        ),
        path=out,
        header=o.header(),
        answer_key=o.answer_key,
        slot_of=_tile_slots(o) if o.self_check_tiles else None,
        black_and_white=o.black_and_white,
    )


def _block(o: BlockOptions, seed: int, out: BinaryIO) -> None:
    problems = block.build_problems(random.Random(seed), o.problems)
    block.render(
        problems=problems,
        path=out,
        title=o.title,
        label=o.label,
        name_line=o.name_line,
        teks="Texas TEKS 2.2(A), 3.4(A)",
        seed=seed,
    )


def _word(o: WordOptions, seed: int, out: BinaryIO) -> None:
    problems = word.build_problems(random.Random(seed), o.problems)
    word.render(
        problems=problems,
        path=out,
        title=o.title,
        label=o.label,
        name_line=o.name_line,
        teks="Texas TEKS 3.4(A)",
        seed=seed,
    )


def _strip(o: StripOptions, seed: int, out: BinaryIO) -> None:
    problems = wp_common.build_problems(random.Random(seed), o.problems, hundreds_cap=9)
    strip.render(
        problems=problems,
        path=out,
        title=o.title,
        label=o.label,
        name_line=o.name_line,
        teks="Texas TEKS 3.5(A)",
        seed=seed,
        answer_key=o.answer_key,
    )


def _number_line(o: NumberLineOptions, seed: int, out: BinaryIO) -> None:
    problems = wp_common.build_problems(random.Random(seed), o.problems, hundreds_cap=9)
    number_line.render(
        problems=problems,
        path=out,
        title=o.title,
        label=o.label,
        name_line=o.name_line,
        teks="Texas TEKS 3.4(A), 3.5(A)",
        seed=seed,
    )


def _number_line_mc(o: NumberLineMCOptions, seed: int, out: BinaryIO) -> None:
    problems = wp_common.build_problems(
        random.Random(seed), o.problems, hundreds_cap=9, add_sorted=True
    )
    number_line_mc.render(
        problems=problems,
        path=out,
        title=o.title,
        label=o.label,
        name_line=o.name_line,
        teks="Texas TEKS 3.4(A), 3.5(A)",
        seed=seed,
    )


def _multiplication_mc(o: MultiplicationMCOptions, seed: int, out: BinaryIO) -> None:
    problems = multiplication_mc.build_problems(
        random.Random(seed), o.problems, o.max_factor, o.max_product
    )
    multiplication_mc.render(
        problems=problems,
        path=out,
        title=o.title,
        label=o.label,
        name_line=o.name_line,
        teks="Texas TEKS 3.4(K)",
        seed=seed,
        jump_labels=not o.no_jump_labels,
    )


def _data_graph(o: DataGraphOptions, seed: int, out: BinaryIO) -> None:
    problems = data_graph.build_problems(random.Random(seed), o.problems, o.list_style)
    data_graph.render(
        problems=problems,
        path=out,
        title=o.title,
        label=o.label,
        name_line=o.name_line,
        teks="Texas TEKS 3.8(A), 3.8(B)",
        seed=seed,
    )


def _data_graph_mc(o: DataGraphMCOptions, seed: int, out: BinaryIO) -> None:
    problems = data_graph_mc.build_problems(random.Random(seed), o.problems, o.list_style)
    data_graph_mc.render(
        problems=problems,
        path=out,
        title=o.title,
        label=o.label,
        name_line=o.name_line,
        teks="Texas TEKS 3.8(A)",
        seed=seed,
    )


def _worksheet(o: WorksheetOptions, seed: int, out: BinaryIO) -> None:
    problems = worksheet.build_problems(
        random.Random(seed), o.represent, o.add, o.sub, regroup=not o.no_regroup
    )
    worksheet.render(
        problems=problems,
        path=out,
        title=o.title,
        subtitle="Represent, add, and subtract numbers within 1,000 using base-ten blocks.",
        name_line=o.name_line,
        teks="Texas TEKS 2.2(A), 2.4(C)",
        seed=seed,
        col=worksheet.BW if o.bw else worksheet.COLOR,
    )


@dataclass(frozen=True)
class Kind[O: Options]:
    options: type[O]
    draw: Callable[[O, int, BinaryIO], None]

    def render(self, options: O, seed: int) -> bytes:
        """Render the PDF for these options and seed, and return its bytes."""
        out = BytesIO()
        self.draw(options, seed, out)
        return out.getvalue()


@dataclass(frozen=True)
class CoreKind[O: Schema]:
    """A kind built on the core. Unlike ``Kind``, it takes no seed."""

    options: type[O]
    draw: Callable[[O, BinaryIO], None]

    def render(self, options: O) -> bytes:
        """Render the PDF for these options, and return its bytes."""
        out = BytesIO()
        self.draw(options, out)
        return out.getvalue()


# The imported scripts, and the only kinds the /legacy page shows.
# kind (used in the URL and the PDF filename) -> how to make it
LEGACY_KINDS: dict[str, Kind[Any]] = {
    "block": Kind(BlockOptions, _block),
    "word": Kind(WordOptions, _word),
    "strip": Kind(StripOptions, _strip),
    "number_line": Kind(NumberLineOptions, _number_line),
    "number_line_mc": Kind(NumberLineMCOptions, _number_line_mc),
    "multiplication_mc": Kind(MultiplicationMCOptions, _multiplication_mc),
    "data_graph": Kind(DataGraphOptions, _data_graph),
    "data_graph_mc": Kind(DataGraphMCOptions, _data_graph_mc),
    "worksheet": Kind(WorksheetOptions, _worksheet),
}

# The kinds built on the core.
CORE_KINDS: dict[str, CoreKind[Any]] = {
    "basic_operations": CoreKind(BasicOperationOptions, _basic_operations),
    "place_value": CoreKind(PlaceValueOptions, _place_value),
    "word_problems": CoreKind(WordProblemOptions, _word_problems),
    "base_ten_blocks": CoreKind(BaseTenBlocksOptions, _base_ten_blocks),
}
