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
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from io import BytesIO
from typing import Annotated, Any, BinaryIO, Literal, Self, get_args

from ninja import Field, Schema
from pydantic import JsonValue, model_validator

from core.arithmetic_expressions.random_expressions import NumberKind
from core.base_ten_blocks import (
    BLOCKS_QUESTION_NAMES,
    DEFAULT_SMALLEST_BLOCKS_NUMBER,
    LARGEST_BLOCKS_NUMBER,
    LARGEST_BLOCKS_OPERAND,
    BlocksQuestionType,
    count_possible_blocks_questions,
    generate_blocks_questions,
)
from core.basic_operations.data import Operation, TwoStepShape, Unknown
from core.basic_operations.generator import (
    DEFAULT_LARGEST_DIVIDEND,
    DEFAULT_LARGEST_DIVISOR,
    DEFAULT_LARGEST_OPERAND,
    LARGEST_WORD_PROBLEM_NUMBER,
    MAXIMUM_OPERAND,
    MULTIPLICATION_MODELS_DEFAULT_LARGEST_PRODUCT,
    MULTIPLICATION_MODELS_LARGEST_FACTOR,
    MULTIPLICATION_MODELS_LARGEST_PRODUCT,
    SMALLEST_WORD_PROBLEM_NUMBER,
    STRIP_CHOICE_LARGEST_GROUPS,
    STRIP_CHOICE_LARGEST_NUMBER,
    WORD_PROBLEM_GROUPS,
    count_possible_equation_choice_problems,
    count_possible_missing_number_questions,
    count_possible_multiplication_model_problems,
    count_possible_number_line_choice_problems,
    count_possible_sheet_questions,
    count_possible_strip_choice_problems,
    count_possible_two_step_problems,
    count_possible_word_problems,
    generate_basic_operation_questions,
    generate_equation_choice_problems,
    generate_missing_number_questions,
    generate_multiplication_model_problems,
    generate_number_line_choice_problems,
    generate_strip_choice_problems,
    generate_two_step_problems,
    generate_two_step_strip_choice_problems,
    generate_word_problems,
    two_step_shapes,
)
from core.basic_operations.multiplication_models import MULTIPLICATION_MODELS_NAME
from core.basic_operations.regrouping import REGROUPING_NAMES, Regrouping
from core.basic_operations.representation import (
    CHOICE_NAMES,
    OPERATION_NAMES,
    REPRESENTATION_NAMES,
    REPRESENTATION_OPERATIONS,
    STRIP_CHOICE_NAME,
    STRIP_TWO_STEP_SHAPES,
    TWO_STEP_REPRESENTATIONS,
    Prompt,
    Representation,
    StripChoiceQuestion,
    TwoStepStripChoiceQuestion,
    WordProblemQuestion,
    basic_operation_tile_question,
    missing_number_tile_question,
    operations_name,
    word_problems_title,
)
from core.discrete_data.data import DataDisplay, DiscreteDataPart
from core.discrete_data.generator import (
    TILE_PARTS,
    available_parts,
    generate_discrete_data_problems,
    most_tile_problems,
)
from core.input_output_tables.data import Blanks, ChoiceType
from core.input_output_tables.generator import (
    count_possible_answers,
    generate_input_output_table_questions,
)
from core.input_output_tables.representation import (
    BLANKS_NAMES,
    CHOICE_TYPE_NAMES,
    INPUT_OUTPUT_TABLES_NAME,
)
from core.line_equations.data import (
    EQUATION_FORMS,
    EQUATION_GIVENS,
    GRAPHING_ASKED,
    GRAPHING_GIVENS,
    LineFeature,
    LineForm,
    Relation,
)
from core.line_equations.generator import (
    DEFAULT_LARGEST_DENOMINATOR,
    can_ask,
    can_graph,
    can_write,
    count_possible_equations,
    count_possible_graphs,
    count_possible_lines,
    generate_equation_questions,
    generate_graphing_questions,
    generate_line_questions,
)
from core.line_equations.representation import (
    EQUATION_GIVEN_NAMES,
    FEATURE_NAMES,
    GRAPHING_ASKED_NAMES,
    GRAPHING_LINEAR_EQUATIONS_NAME,
    NUMBER_STYLE_NAMES,
    SLOPE_AND_INTERCEPTS_NAME,
    WRITING_LINEAR_EQUATIONS_NAME,
)
from core.line_equations.representation import (
    FORM_NAMES as LINE_FORM_NAMES,
)
from core.order_of_operations.data import TILE_TYPES as ORDER_OF_OPERATIONS_TILE_TYPES
from core.order_of_operations.data import GroupSymbols, SheetSettings
from core.order_of_operations.data import QuestionType as OrderOfOperationsType
from core.order_of_operations.generator import (
    generate_order_of_operations_questions,
    tile_answers_limit,
)
from core.order_of_operations.representation import (
    GROUP_SYMBOLS_NAMES,
    LEVEL_NAMES,
    NUMBER_KIND_NAMES,
    ORDER_OF_OPERATIONS_NAME,
)
from core.order_of_operations.representation import (
    QUESTION_TYPE_NAMES as ORDER_OF_OPERATIONS_TYPE_NAMES,
)
from core.placevalue.data import PlaceValueForm
from core.placevalue.generator import (
    DEFAULT_LARGEST_NUMBER,
    DEFAULT_SMALLEST_NUMBER,
    generate_place_value_questions,
)
from core.placevalue.representation import (
    FORM_NAMES,
    LARGEST_NUMBER,
    WRITTEN_FORMS,
    place_value_tile_question,
)
from core.prime_composite.data import TILE_TYPES, QuestionType
from core.prime_composite.generator import (
    LARGEST_NUMBER as PRIME_COMPOSITE_LARGEST_NUMBER,
)
from core.prime_composite.generator import (
    count_possible_answers as count_possible_prime_composite_answers,
)
from core.prime_composite.generator import generate_prime_composite_questions
from core.prime_composite.representation import PRIME_COMPOSITE_NAME, QUESTION_TYPE_NAMES
from core.self_check_tiles import SLOTS, TileQuestion, conventional_slot_of, random_slot_of
from core.written_numbers import NumberStyle
from core.wrong_answers import WRONG_ANSWER_COUNT
from render.pdf.base_ten_blocks_worksheet import render_base_ten_blocks_worksheet
from render.pdf.basic_operations_worksheet import (
    render_basic_operations_worksheet,
    render_missing_number_worksheet,
)
from render.pdf.data_displays import NumberListStyle
from render.pdf.data_graphs_worksheet import render_data_graphs_worksheet
from render.pdf.input_output_tables_worksheet import render_input_output_tables_worksheet
from render.pdf.line_equations_worksheet import render_line_equations_worksheet
from render.pdf.multiplication_models_worksheet import render_multiplication_models_worksheet
from render.pdf.order_of_operations_worksheet import render_order_of_operations_worksheet
from render.pdf.page import Header
from render.pdf.place_value_worksheet import render_place_value_worksheet
from render.pdf.prime_composite_worksheet import render_prime_composite_worksheet
from render.pdf.self_check_tiles_worksheet import render_self_check_tiles_worksheet
from render.pdf.strip_choice_worksheet import render_strip_choice_worksheet
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
# A written PlaceValueForm value: one of the forms mixed can pick
WrittenFormChoice = Literal["standard", "expanded", "unit", "expanded_notation", "word"]
# A written form, or mixed, where each question's form is one of those ticked for it
FormChoice = Literal[WrittenFormChoice, "mixed"]
# Operations checkbox labels: each operation's sheet title
OPERATION_LABELS: dict[str, JsonValue] = {
    operation.value: name for operation, name in OPERATION_NAMES.items()
}
# A checkbox for each operation; each kind sets which are ticked
Operations = Annotated[
    list[OperationChoice],
    Field(min_length=1, title="Operations", json_schema_extra={"labels": OPERATION_LABELS}),
]
# A word-problem sheet's largest number, at least the smallest sum; each kind sets its default
WordProblemLargestNumber = Annotated[
    int,
    Field(
        ge=2 * SMALLEST_WORD_PROBLEM_NUMBER, le=LARGEST_WORD_PROBLEM_NUMBER, title="Largest number"
    ),
]
# From and To dropdown labels: each form's name, plus mixed
FORM_CHOICE_LABELS: dict[str, JsonValue] = {
    **{form.value: name for form, name in FORM_NAMES.items()},
    "mixed": "mixed",
}
# Representation dropdown labels: each representation's name
REPRESENTATION_LABELS: dict[str, JsonValue] = {
    representation.value: name for representation, name in REPRESENTATION_NAMES.items()
}
StepsChoice = Literal["one", "two"]
STEPS_LABELS: dict[str, JsonValue] = {"one": "One step", "two": "Two steps"}
ResponseChoice = Literal["free_response", "multiple_choice"]
RESPONSE_LABELS: dict[str, JsonValue] = {
    "free_response": "Free response",
    "multiple_choice": "Multiple choice",
}
PromptChoice = Literal["word_problem", "equation", "both"]  # a Prompt value
# Show radio labels
PROMPT_LABELS: dict[str, JsonValue] = {
    Prompt.WORD_PROBLEM.value: "Word problem",
    Prompt.EQUATION.value: "Equation",
    Prompt.BOTH.value: "Both",
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
NumberListStyleChoice = Literal["grid", "commas"]  # a NumberListStyle value
# A list style, or mix, where each list's style is drawn at random
MixedListStyleChoice = Literal[NumberListStyleChoice, "mix"]
NUMBER_LIST_STYLE_LABELS: dict[str, JsonValue] = {"grid": "Grid", "commas": "Commas", "mix": "Mix"}
# a SHEET_DISPLAYS value
DataDisplayChoice = Literal["table", "tally_table", "pictograph", "bar_graph", "dot_plot", "list"]
DATA_DISPLAY_LABELS: dict[str, JsonValue] = {
    "table": "Frequency table",
    "tally_table": "Tally table",
    "pictograph": "Pictograph",
    "bar_graph": "Bar graph",
    "dot_plot": "Dot plot",
    "list": "List of numbers",
}
DataPartChoice = Literal[  # a DiscreteDataPart value
    "another_display", "read_counts", "find_error", "doesnt_match", "one_step", "two_step"
]
DATA_PART_LABELS: dict[str, JsonValue] = {
    "another_display": "Show the data another way",
    "read_counts": "Read the counts",
    "find_error": "Find the error",
    "doesnt_match": "Which one doesn't match",
    "one_step": "One-step word problem",
    "two_step": "Two-step word problem",
}
BlanksChoice = Literal["inputs", "outputs", "inputs_and_outputs"]  # a Blanks value
# Missing table values radio button labels: each choice's name
BLANKS_LABELS: dict[str, JsonValue] = {blanks.value: name for blanks, name in BLANKS_NAMES.items()}
ChoiceTypeChoice = Literal["table", "sentence", "statement"]  # a ChoiceType value
# Question types checkbox labels: each type's name
CHOICE_TYPE_LABELS: dict[str, JsonValue] = {
    choice_type.value: name for choice_type, name in CHOICE_TYPE_NAMES.items()
}
# a prime and composite QuestionType value
PrimeCompositeTypeChoice = Literal[
    "factor_pairs",
    "count",
    "choose_two",
    "between",
    "whose_number",
    "who_is_correct",
    "each_number",
    "list_factors",
]
# The prime and composite question types checkbox labels: each type's name
PRIME_COMPOSITE_TYPE_LABELS: dict[str, JsonValue] = {
    question_type.value: name for question_type, name in QUESTION_TYPE_NAMES.items()
}
SMALLEST_PRIME_COMPOSITE_LARGEST = 20  # keeps a range of primes with odd composites to choose
LARGEST_PRIME_COMPOSITE_LARGEST = 1_000
# an order of operations QuestionType value
OrderOfOperationsTypeChoice = Literal[
    "value", "next_step", "has_value", "first_operation", "parentheses", "find_error"
]
# The order of operations question types checkbox labels: each type's name
ORDER_OF_OPERATIONS_TYPE_LABELS: dict[str, JsonValue] = {
    question_type.value: name for question_type, name in ORDER_OF_OPERATIONS_TYPE_NAMES.items()
}
GroupingChoice = Literal["none", "one", "two"]  # how deeply an expression's groups nest
GROUPING_LEVELS = {"none": 0, "one": 1, "two": 2}
# Grouping checkbox labels: each level's name, with what it looks like
GROUPING_LABELS: dict[str, JsonValue] = {
    choice: LEVEL_NAMES[level] for choice, level in GROUPING_LEVELS.items()
}
GroupSymbolsChoice = Literal["brackets", "parentheses", "mixed"]  # a GroupSymbols value
# Groups inside groups radio button labels: each way of writing them, as it looks
GROUP_SYMBOLS_LABELS: dict[str, JsonValue] = {
    symbols.value: name for symbols, name in GROUP_SYMBOLS_NAMES.items()
}
NumberKindChoice = Literal["whole", "decimal", "fraction"]  # a NumberKind value
# Numbers checkbox labels: each kind's name
NUMBER_KIND_LABELS: dict[str, JsonValue] = {
    kind.value: name for kind, name in NUMBER_KIND_NAMES.items()
}
# a LineForm value
LineFormChoice = Literal[
    "slope_intercept",
    "standard",
    "point_slope",
    "point_and_slope",
    "two_points",
    "vertical",
    "horizontal",
    "table",
    "graph",
]
# Lines given as checkbox labels: each form's name, with what it looks like
LINE_FORM_LABELS: dict[str, JsonValue] = {
    form.value: name for form, name in LINE_FORM_NAMES.items()
}
LineFeatureChoice = Literal[
    "slope", "rate_of_change", "y_intercept", "x_intercept", "zero", "slope_and_y_intercept"
]
# Questions ask for checkbox labels: each feature's name
LINE_FEATURE_LABELS: dict[str, JsonValue] = {
    feature.value: name for feature, name in FEATURE_NAMES.items()
}
InterceptAnswerChoice = Literal["number", "point"]
# Intercepts as checkbox labels: each shows what the answer looks like
INTERCEPT_ANSWER_LABELS: dict[str, JsonValue] = {
    "number": "Numbers (2)",
    "point": "Ordered pairs ((0, 2))",
}
LineNumberStyleChoice = Literal["fraction", "decimal"]  # a NumberStyle value lines are written in
LINE_NUMBER_STYLE_LABELS: dict[str, JsonValue] = {
    style.value: NUMBER_STYLE_NAMES[style] for style in (NumberStyle.FRACTION, NumberStyle.DECIMAL)
}
# a LineForm or Relation value a line's equation is written from
EquationGivenChoice = Literal[
    "slope_intercept",
    "standard",
    "point_slope",
    "point_and_slope",
    "two_points",
    "table",
    "graph",
    "parallel",
    "perpendicular",
]
# Lines given as checkbox labels, on the writing equations sheet: each form's name, with what it
# looks like, or each relation's
EQUATION_GIVEN_LABELS: dict[str, JsonValue] = {
    given.value: name for given, name in EQUATION_GIVEN_NAMES.items()
}
# a LineForm value an equation is written in
EquationFormChoice = Literal["slope_intercept", "standard", "point_slope", "vertical", "horizontal"]
# Write equations in checkbox labels: each form's name, with what it looks like
EQUATION_FORM_LABELS: dict[str, JsonValue] = {
    form.value: LINE_FORM_NAMES[form] for form in EQUATION_FORMS
}
# a LineForm value a line is graphed or tabled from
GraphingGivenChoice = Literal[
    "slope_intercept",
    "standard",
    "point_slope",
    "slope_and_intercept",
    "intercepts",
    "point_and_slope",
    "two_points",
    "vertical",
    "horizontal",
    "graph",
]
# Lines given as checkbox labels, on the graphing sheet: each form's name
GRAPHING_GIVEN_LABELS: dict[str, JsonValue] = {
    form.value: LINE_FORM_NAMES[form] for form in GRAPHING_GIVENS
}
GraphingAskedChoice = Literal["graph", "table"]  # a LineForm value graphing lines asks for
GRAPHING_ASKED_LABELS: dict[str, JsonValue] = {
    form.value: name for form, name in GRAPHING_ASKED_NAMES.items()
}
SMALLEST_LARGEST_COORDINATE = 5  # STAAR's smallest grids run to 4, for graphing a line
SHEET_LARGEST_COORDINATE = 12  # the line sheets' default, so grids run from -12 to 12
LARGEST_LARGEST_COORDINATE = 60  # the generator lists each slope's y-intercepts, so stays quick
LARGEST_LARGEST_DENOMINATOR = 20
# The options both line sheets share
LargestCoordinate = Annotated[
    int,
    Field(
        ge=SMALLEST_LARGEST_COORDINATE,
        le=LARGEST_LARGEST_COORDINATE,
        title="Largest number in a point",
        description="Every point shown, and where each line crosses the axes, uses numbers from "
        "minus to plus this.",
    ),
]
LargestDenominator = Annotated[
    int,
    Field(
        ge=1,
        le=LARGEST_LARGEST_DENOMINATOR,
        title="Largest denominator",
        description="Of the slopes and intercepts: 1 makes them all whole numbers.",
    ),
]
WholeIntercepts = Annotated[bool, Field(title="Whole-number intercepts only")]
# The page shows this only while Two points is ticked (see builder.html).
BlankGrids = Annotated[
    bool,
    Field(
        title="Blank grid beside two points",
        description="About half the questions given two points have an empty coordinate grid "
        "beside them to work on.",
    ),
]
LineNumberStyles = Annotated[
    list[LineNumberStyleChoice],
    Field(
        min_length=1,
        title="Numbers that aren't whole",
        json_schema_extra={"labels": LINE_NUMBER_STYLE_LABELS},
    ),
]
LineMultipleChoice = Annotated[
    bool,
    Field(
        title="Multiple choice",
        description=f"Lists {WRONG_ANSWER_COUNT + 1} choices under each line instead of an "
        "answer line: the wrong ones are common mistakes, such as the reciprocal of the slope.",
    ),
]
GraphingMultipleChoice = Annotated[
    bool,
    Field(
        title="Multiple choice",
        description=f"Shows {WRONG_ANSWER_COUNT + 1} graphs or tables to choose from instead of a "
        "blank grid or table.",
    ),
]
# The page shows this only while x = a or y = b is ticked (see builder.html).
Statements = Annotated[
    bool,
    Field(
        title="Also ask for the slope or direction",
        description="About half the vertical and horizontal lines also ask for the slope, or "
        "whether the line is parallel or perpendicular to the x-axis.",
    ),
]
AnswerKey = Annotated[bool, Field(title="Add an answer key page")]
NameDateLine = Annotated[bool, Field(title="Add Name/Date blanks")]
SelfCheckTiles = Annotated[
    bool,
    Field(
        title="Self-check tile answers",
        description="Swaps the answer lines or choices for an answer bank and a picture to match "
        f"against the flipped case. That sets the questions to {SLOTS}, one for each tile: ask "
        "for fewer, such as 2 or 4, and the other tiles go unused.",
    ),
]
# simple: a conventional picture; complex: tiles in arbitrary slots. The page shows it under the
# tiles box.
TilePattern = Annotated[
    Literal["simple", "complex"],
    Field(title="Pattern", json_schema_extra={"input": "radio", "under": "self_check_tiles"}),
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


def _two_steps_can_be_made(
    operations: Sequence[Operation], shapes: Collection[TwoStepShape] | None
) -> None:
    """
    Raise ``ValueError`` if no shape of two-step problem among ``shapes``, or among all if
    ``None``, has both its operations in ``operations``. Every shape a strip diagram shows adds or
    subtracts. Every operation has a shape of its own, such as multiplying twice, so among all
    shapes there is always one.
    """
    if not two_step_shapes(operations, shapes):
        raise ValueError("operations: two steps need addition or subtraction")


def _too_many_problems(
    possible: int,
    repeats: str,
    limits: str,
    raises: Mapping[str, int | None],
    unticks: Sequence[str] = (),
) -> ValueError:
    """
    Return the error for requesting more problems than the limits allow, with suggested fixes.

    ``possible`` is how many problems ``limits`` allow without ``repeats``. ``raises`` maps each
    limit, named as in the message, to the smallest value that would allow the requested
    problems, or to ``None`` when raising that limit alone cannot. ``unticks`` names, by their
    labels, the ticked choices whose unticking together would allow them. When no problem is
    possible, lowering the number of problems can't help, so it isn't suggested.
    """
    fixes = [f"lower problems to {possible}"] if possible else []
    fixes += [f"untick {_listed(unticks)}"] if unticks else []
    fixes += [
        f"raise the {limit} to {value:,}" for limit, value in raises.items() if value is not None
    ]
    if possible:
        message = f"problems: at most {possible} without {repeats} for that {limits}."
    else:
        message = f"problems: none possible for that {limits}."
    if fixes:
        advice = ", or ".join(fixes)
        message += f" {advice[0].upper()}{advice[1:]}."
    return ValueError(message)


def _listed(names: Sequence[str]) -> str:
    """Return ``names`` as a list in a sentence: "A", "A and B", "A, B and C"."""
    return " and ".join(filter(None, (", ".join(names[:-1]), names[-1])))


def _boxes_to_untick[T](
    ticked: Sequence[T],
    askable: Callable[[Sequence[T]], bool],
    count: Callable[[Sequence[T]], int],
    problems: int,
) -> list[T]:
    """
    Return the ``ticked`` choices that on their own allow fewer than ``problems``, when unticking
    them all leaves choices that ``askable`` says can make a question and that ``count`` says
    allow ``problems``. Otherwise return none, since unticking them wouldn't help.
    """
    holding_back = [choice for choice in ticked if askable([choice]) and count([choice]) < problems]
    rest = [choice for choice in ticked if choice not in holding_back]
    if holding_back and askable(rest) and count(rest) >= problems:
        return holding_back
    return []


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
    operations: Operations = Field(["add"])
    # Division alone: any value but answer produces fill-in equations, such as □ ÷ 4 = 7
    missing_number: Literal["answer", "dividend", "divisor", "mixed"] = Field(
        "answer",
        title="Missing number",
        description="Can leave out the dividend or the divisor instead of the answer, as a "
        "square to write it in.",
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
        "standard",
        title="From",
        json_schema_extra={"labels": FORM_CHOICE_LABELS},
    )
    asked: FormChoice = Field(
        "expanded", title="To", json_schema_extra={"labels": FORM_CHOICE_LABELS}
    )
    # The forms mixed picks from, every one ticked to start with. Each list is used only while
    # its dropdown is on mixed, and the page shows it under the dropdown only then (see
    # builder.html).
    given_mix: list[WrittenFormChoice] = Field(
        list(get_args(WrittenFormChoice)),
        min_length=1,
        title="Question forms",
        json_schema_extra={"labels": FORM_CHOICE_LABELS, "under": "given"},
    )
    asked_mix: list[WrittenFormChoice] = Field(
        list(get_args(WrittenFormChoice)),
        min_length=1,
        title="Answer forms",
        json_schema_extra={"labels": FORM_CHOICE_LABELS, "under": "asked"},
    )
    min_number: int = Field(
        DEFAULT_SMALLEST_NUMBER, ge=1, le=LARGEST_NUMBER, title="Smallest number"
    )
    max_number: int = Field(DEFAULT_LARGEST_NUMBER, ge=1, le=LARGEST_NUMBER, title="Largest number")
    answer_key: AnswerKey = False
    multiple_choice: bool = Field(
        False,
        title="Multiple choice",
        description=f"Lists {WRONG_ANSWER_COUNT + 1} choices under each number instead of an "
        "answer line: the wrong ones are random numbers from the range.",
    )
    # Tiles replace the answer lines with an answer bank page.
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @model_validator(mode="after")
    def _tiles_are_available(self) -> Self:
        # Not built for multiple choice: each choice's letter would need coding as a number. The
        # page hides multiple choice while tiles are ticked, and greys out the tiles while it is.
        # Runs first, so a request with both is told so before anything else.
        if self.self_check_tiles and self.multiple_choice:
            raise ValueError("self_check_tiles: not available with multiple choice")
        return self

    @model_validator(mode="after")
    def _a_question_can_be_made(self) -> Self:
        given = _place_value_forms(self.given, self.given_mix)
        asked = _place_value_forms(self.asked, self.asked_mix)
        # one form for both: standard to standard, or mixed with only standard ticked to standard
        if len({*given, *asked}) == 1:
            raise ValueError("asked: must be a different form from given")
        if self.min_number > self.max_number:
            raise ValueError("min_number: must not be more than the largest number")
        possible = self.max_number - self.min_number + 1
        if self.problems > possible:
            needed = self.min_number + self.problems - 1
            raises = {"largest number": needed if needed <= LARGEST_NUMBER else None}
            raise _too_many_problems(possible, "repeats", "range of numbers", raises)
        # The wrong answers come from the same range, and are never the correct one.
        if self.multiple_choice and self.max_number - self.min_number < WRONG_ANSWER_COUNT:
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
    title: Title = word_problems_title(Representation.NONE)
    problems: Problems = 4
    # Each problem's operation is drawn at random from those ticked.
    operations: Operations = Field(["add", "subtract"])
    # Addition and subtraction only: every number in the problem, its answer included. With two
    # steps, which share a number, every number, multiplication's and division's too. It's at
    # least the smallest sum, which leaves room for a subtraction too.
    max_number: WordProblemLargestNumber = LARGEST_WORD_PROBLEM_NUMBER
    representation: Literal["strip", "none", "number_line", "blocks", "equation"] = Field(
        "none", title="Representation", json_schema_extra={"labels": REPRESENTATION_LABELS}
    )
    # Multiple choice is for the representations in CHOICE_NAMES: each problem's is chosen from
    # lettered ones.
    response: ResponseChoice = Field(
        "free_response",
        title="Response",
        json_schema_extra={"input": "radio", "labels": RESPONSE_LABELS},
    )
    # Strip diagrams and text only: with strip diagrams, two steps draw one bar, the whole over
    # its parts.
    steps: StepsChoice = Field(
        "one", title="Steps", json_schema_extra={"input": "radio", "labels": STEPS_LABELS}
    )
    no_hints: bool = Field(False, title="Leave out the hints")  # text only has none
    work_box: bool = Field(False, title="Include working out space")  # text only
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

    @property
    def shapes(self) -> frozenset[TwoStepShape] | None:
        """
        The shapes of two-step problem the representation can show: a strip diagram's five, or
        with text only, all of them.
        """
        if Representation(self.representation) is Representation.STRIP:
            return STRIP_TWO_STEP_SHAPES
        return None

    @property
    def choices(self) -> bool:
        """Whether each problem's representation is chosen from lettered ones."""
        return self.response == "multiple_choice"

    @model_validator(mode="after")
    def _choices_are_available(self) -> Self:
        # The page hides the response radios for a representation without choices. Runs before
        # the title follows the response, which needs a choice title for multiple choice.
        representation = Representation(self.representation)
        if self.choices and representation not in CHOICE_NAMES:
            name = REPRESENTATION_NAMES[representation]
            raise ValueError(f"response: multiple choice not available with {name}")
        return self

    @model_validator(mode="after")
    def _title_follows_the_representation(self) -> Self:
        # The default is the default representation's title. A request that picks another, or
        # multiple choice, and gives no title gets its title.
        if "title" not in self.model_fields_set:
            self.title = word_problems_title(Representation(self.representation), self.choices)
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
    def _two_steps_are_available(self) -> Self:
        # Only strip diagrams and text only show two steps. The page hides the steps for the
        # others.
        representation = Representation(self.representation)
        if self.steps == "two" and representation not in TWO_STEP_REPRESENTATIONS:
            raise ValueError(
                f"steps: two steps not available with {REPRESENTATION_NAMES[representation]}"
            )
        return self

    @model_validator(mode="after")
    def _tiles_are_available(self) -> Self:
        # Not built for multiple choice: each choice's letter would need coding as a number. The
        # page greys each out while the other is picked.
        if self.self_check_tiles and self.choices:
            raise ValueError("self_check_tiles: not available with multiple choice")
        return self

    @model_validator(mode="after")
    def _enough_different_problems(self) -> Self:
        if self.self_check_tiles:
            _at_most_one_question_per_tile(self.problems)
        # Any one operation may be drawn for every problem, and with tiles each tile needs a
        # distinct answer.
        operations = _operations(self.operations)
        if self.steps == "two":
            _two_steps_can_be_made(operations, self.shapes)

        def possible_with(largest: int) -> int:
            if self.steps == "two":
                return count_possible_two_step_problems(
                    operations,
                    distinct_answers=self.self_check_tiles,
                    up_to=self.problems,
                    largest_number=largest,
                    shapes=self.shapes,
                )
            if self.choices and Representation(self.representation) is Representation.NUMBER_LINE:
                return count_possible_number_line_choice_problems(
                    operations, up_to=self.problems, largest_number=largest
                )
            if self.choices:
                return count_possible_equation_choice_problems(
                    operations, up_to=self.problems, largest_number=largest
                )
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
        if self.steps == "one" and {Operation.ADD, Operation.SUBTRACT}.isdisjoint(operations):
            # One-step multiplication and division have no number limits to raise.
            raise _too_many_problems(possible, repeats, "choice of operations", {})
        raise_to = _smallest_raise(
            possible_with, self.problems, self.max_number, LARGEST_WORD_PROBLEM_NUMBER
        )
        if {Operation.ADD, Operation.SUBTRACT}.issuperset(operations):
            limits = "largest number"
        else:
            limits = "choice of operations and largest number"
        raise _too_many_problems(possible, repeats, limits, {"largest number": raise_to})


class StripChoiceOptions(HeaderOptions):
    """
    Options for the kind where each problem's strip diagram is chosen from lettered strips, built
    on the core. There is no seed: every sheet is new.
    """

    title: Title = STRIP_CHOICE_NAME
    problems: Problems = 4
    # Each problem's operation is drawn at random from those ticked.
    operations: Operations = Field(["add", "subtract", "multiply", "divide"])
    # Every number in a problem, its answer included: a multiplication's product and a
    # division's dividend too, unlike on word problems
    max_number: WordProblemLargestNumber = STRIP_CHOICE_LARGEST_NUMBER
    steps: StepsChoice = Field(
        "one", title="Steps", json_schema_extra={"input": "radio", "labels": STEPS_LABELS}
    )
    # Every strip's equal groups: a multiplication's, a division's, and the smaller number of an
    # addition or subtraction, which its wrong choices multiply and divide by
    max_groups: int = Field(
        STRIP_CHOICE_LARGEST_GROUPS,
        ge=WORD_PROBLEM_GROUPS[0],
        le=STRIP_CHOICE_LARGEST_GROUPS,
        title="Largest number of groups",
    )
    prompt: PromptChoice = Field(
        Prompt.WORD_PROBLEM.value,
        title="Show",
        json_schema_extra={"input": "radio", "labels": PROMPT_LABELS},
    )
    answer_key: AnswerKey = False

    @model_validator(mode="after")
    def _enough_different_problems(self) -> Self:
        # Any one operation, or with two steps any one shape, may be drawn for every problem.
        operations = _operations(self.operations)
        two_steps = self.steps == "two"
        if two_steps:
            _two_steps_can_be_made(operations, STRIP_TWO_STEP_SHAPES)

        def possible_with(largest: int, groups: int) -> int:
            if two_steps:
                return count_possible_two_step_problems(
                    operations,
                    up_to=self.problems,
                    largest_number=largest,
                    largest_groups=groups,
                    split_evenly=True,
                    shapes=STRIP_TWO_STEP_SHAPES,
                )
            return count_possible_strip_choice_problems(
                operations, up_to=self.problems, largest_number=largest, largest_groups=groups
            )

        possible = possible_with(self.max_number, self.max_groups)
        if self.problems <= possible:
            return self
        # Every count depends on the largest number. With one step, every operation's but
        # subtraction's depends on the number of groups too, and with two steps, multiplication's
        # and division's.
        limits = ["largest number"]
        if two_steps:
            groups_count = not {Operation.MULTIPLY, Operation.DIVIDE}.isdisjoint(operations)
        else:
            groups_count = not {Operation.SUBTRACT}.issuperset(operations)
        if groups_count:
            limits.append("largest number of groups")
        raises = {
            "largest number": _smallest_raise(
                lambda largest: possible_with(largest, self.max_groups),
                self.problems,
                self.max_number,
                LARGEST_WORD_PROBLEM_NUMBER,
            ),
            "largest number of groups": _smallest_raise(
                lambda groups: possible_with(self.max_number, groups),
                self.problems,
                self.max_groups,
                STRIP_CHOICE_LARGEST_GROUPS,
            ),
        }
        raise _too_many_problems(possible, "repeats", " and ".join(limits), raises)


class MultiplicationModelsOptions(HeaderOptions):
    """
    Options for the kind where three models of each multiplication word problem are chosen from
    six, built on the core. There is no seed: every sheet is new.
    """

    title: Title = MULTIPLICATION_MODELS_NAME
    problems: Problems = 4
    # At least 3 and 6, so there is always a fact other than 2 x 2 to draw from.
    max_factor: int = Field(
        MULTIPLICATION_MODELS_LARGEST_FACTOR,
        ge=3,
        le=MULTIPLICATION_MODELS_LARGEST_FACTOR,
        title="Largest factor",
    )
    max_product: int = Field(
        MULTIPLICATION_MODELS_DEFAULT_LARGEST_PRODUCT,
        ge=6,
        le=MULTIPLICATION_MODELS_LARGEST_PRODUCT,
        title="Largest product",
    )
    no_jump_labels: bool = Field(False, title="Leave the number-line jumps unnumbered")
    answer_key: AnswerKey = False

    @model_validator(mode="after")
    def _enough_different_problems(self) -> Self:
        def possible_with(factor: int, product: int) -> int:
            return count_possible_multiplication_model_problems(
                up_to=self.problems, largest_factor=factor, largest_product=product
            )

        possible = possible_with(self.max_factor, self.max_product)
        if self.problems <= possible:
            return self
        raises = {
            "largest factor": _smallest_raise(
                lambda factor: possible_with(factor, self.max_product),
                self.problems,
                self.max_factor,
                MULTIPLICATION_MODELS_LARGEST_FACTOR,
            ),
            "largest product": _smallest_raise(
                lambda product: possible_with(self.max_factor, product),
                self.problems,
                self.max_product,
                MULTIPLICATION_MODELS_LARGEST_PRODUCT,
            ),
        }
        raise _too_many_problems(possible, "repeats", "largest factor and largest product", raises)


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


class DataGraphsOptions(HeaderOptions):
    """
    Options for the data and graphs kind, built on the core. There is no seed: every sheet is new.
    """

    title: Title = "Data and Graphs — Read, Complete, Solve"
    problems: Problems = 4
    # The data sets are shown in the ticked displays. The page greys out the questions they
    # can't make.
    displays: list[DataDisplayChoice] = Field(
        list(get_args(DataDisplayChoice)),
        min_length=1,
        title="Graphs and tables",
        description="A list of numbers is plotted as a dot plot on a number line.",
        json_schema_extra={"labels": DATA_DISPLAY_LABELS},
    )
    # Each problem asks one of the first four ticked first, dealt in turn, then the word problems.
    questions: list[DataPartChoice] = Field(
        list(get_args(DataPartChoice)),
        min_length=1,
        title="Questions",
        json_schema_extra={"labels": DATA_PART_LABELS},
    )
    list_style: MixedListStyleChoice = Field(
        "grid",
        title="Show lists of numbers as",
        json_schema_extra={"input": "radio", "labels": NUMBER_LIST_STYLE_LABELS},
    )
    multiple_choice: bool = Field(
        False,
        title="Multiple choice",
        description="Lettered choices instead of written answers: the matching graph or table, "
        "list, fix or number. The wrong ones are common mistakes. Which one doesn't match "
        "always has choices, and with self-check tiles, the word problems keep their tiles.",
    )
    answer_key: AnswerKey = False
    # Tiles take the word problems' answers, one tile each, and add an answer bank page. The
    # page greys them out while no word problem is ticked.
    self_check_tiles: bool = Field(
        False,
        title="Self-check tile answers",
        description="Swaps the answer boxes for an answer bank and a picture to match against "
        f"the flipped case. Each word problem takes one of the {SLOTS} tiles, so ticking this "
        f"sets the problems to {SLOTS // len(TILE_PARTS)} with both word problems, or "
        f"{SLOTS} with one.",
    )
    tile_pattern: TilePattern = "simple"

    @model_validator(mode="after")
    def _displays_make_the_questions(self) -> Self:
        # Some questions need displays of more than one kind, or ones whose counts take reading.
        available = available_parts([DataDisplay(display) for display in self.displays])
        missing = [part for part in self.questions if part not in available]
        if missing:
            names = [str(DATA_PART_LABELS[part]) for part in missing]
            raise ValueError(f"questions: those graphs and tables can't make {_listed(names)}")
        return self

    @model_validator(mode="after")
    def _tiles_fit(self) -> Self:
        # Each word problem takes a tile, and question n's tiles follow question n - 1's.
        if self.self_check_tiles:
            per_problem = sum(part in self.questions for part in TILE_PARTS)
            if not per_problem:
                raise ValueError("self_check_tiles: needs a one-step or two-step word problem")
            if self.problems * per_problem > SLOTS:
                raise ValueError(
                    f"problems: self-check tiles has {SLOTS} tiles, one for each word problem, "
                    f"so at most {SLOTS // per_problem}"
                )
            displays = [DataDisplay(display) for display in self.displays]
            parts = [DiscreteDataPart(part) for part in self.questions]
            most = most_tile_problems(displays, parts)
            if most is not None and self.problems > most:
                doesnt_match = DATA_PART_LABELS[DiscreteDataPart.DOESNT_MATCH]
                raise ValueError(
                    f"problems: at most {most} with a different answer on every tile, as "
                    f"{doesnt_match} has few different answers with those graphs and tables. "
                    "Tick more graphs and tables or questions, or untick it"
                )
        return self


class InputOutputTableOptions(HeaderOptions):
    """
    Options for the input-output tables kind, built on the core. There is no seed: every sheet is
    new.
    """

    title: Title = INPUT_OUTPUT_TABLES_NAME
    problems: Problems = 6
    # Each problem's operation is drawn at random from those ticked.
    operations: Operations = Field(["add", "subtract", "multiply", "divide"])
    # Tables to fill in only: multiple choice shows complete tables, so the page hides this
    # while it's ticked.
    blanks: BlanksChoice = Field(
        "inputs_and_outputs",
        title="Missing table values",
        json_schema_extra={"input": "radio", "labels": BLANKS_LABELS},
    )
    multiple_choice: bool = Field(
        False,
        title="Multiple choice",
        description="Instead of tables to fill in, asks the ticked question types.",
    )
    # Multiple choice only, so the page shows these only while it's ticked. The problems are
    # shared evenly among the ticked types, each asked in a mix of STAAR's forms.
    question_types: list[ChoiceTypeChoice] = Field(
        ["table", "sentence", "statement"],
        min_length=1,
        title="Question types",
        json_schema_extra={"labels": CHOICE_TYPE_LABELS},
    )
    answer_key: AnswerKey = False
    # Tiles leave one number out of each table, and add an answer bank page.
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @model_validator(mode="after")
    def _tiles_are_available(self) -> Self:
        # Not built for multiple choice: each choice's letter would need coding as a number. The
        # page hides multiple choice while tiles are ticked, and greys out the tiles while it is.
        # Runs first, so a request with both is told so before anything else.
        if self.self_check_tiles and self.multiple_choice:
            raise ValueError("self_check_tiles: not available with multiple choice")
        return self

    @model_validator(mode="after")
    def _enough_different_answers(self) -> Self:
        # With tiles, each table leaves out one number, and no two tables the same one. Division
        # with outputs only, and multiplication with inputs only, can run short: those numbers
        # are 1 to 10.
        if self.self_check_tiles:
            _at_most_one_question_per_tile(self.problems)
            operations = _operations(self.operations)
            possible = count_possible_answers(operations, Blanks(self.blanks))
            if self.problems > possible:
                limits = "choice of operations and missing table values"
                raise _too_many_problems(possible, "repeated answers", limits, {})
        return self


class PrimeCompositeOptions(HeaderOptions):
    """
    Options for the prime and composite kind, built on the core. There is no seed: every sheet is
    new.
    """

    title: Title = PRIME_COMPOSITE_NAME
    problems: Problems = 10
    # The problems are shared evenly among the ticked types. With tiles, the page greys out the
    # types that have no counting form.
    question_types: list[PrimeCompositeTypeChoice] = Field(
        [question_type.value for question_type in QuestionType],
        min_length=1,
        title="Question types",
        json_schema_extra={"labels": PRIME_COMPOSITE_TYPE_LABELS},
    )
    largest_number: int = Field(
        PRIME_COMPOSITE_LARGEST_NUMBER,
        ge=SMALLEST_PRIME_COMPOSITE_LARGEST,
        le=LARGEST_PRIME_COMPOSITE_LARGEST,
        title="Largest number",
        description="No number to judge prime or composite is larger. A number whose factor "
        "pairs are asked for can be up to twice it.",
    )
    multiple_choice: bool = Field(
        False,
        title="Multiple choice",
        description="Lettered choices instead of answer lines. The wrong ones are common "
        "mistakes, such as 1 or 2 in a factor pair, or an odd composite for a prime.",
    )
    answer_key: AnswerKey = False
    # Tiles ask counting forms of the questions, and add an answer bank page.
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @model_validator(mode="after")
    def _tiles_are_available(self) -> Self:
        # Not built for multiple choice: each choice's letter would need coding as a number. The
        # page hides multiple choice while tiles are ticked, and greys out the tiles while it is.
        # Runs first, so a request with both is told so before anything else.
        if self.self_check_tiles and self.multiple_choice:
            raise ValueError("self_check_tiles: not available with multiple choice")
        return self

    @model_validator(mode="after")
    def _enough_different_answers(self) -> Self:
        # With tiles, a question's answer mustn't be printed in it, or the bank gives it away,
        # and no two answers are the same, which a small largest number can run short of.
        if self.self_check_tiles:
            types = _prime_composite_types(self.question_types)
            without = [QUESTION_TYPE_NAMES[each] for each in types if each not in TILE_TYPES]
            if without:
                raise ValueError(
                    f"question_types: {_listed(without)} can't be asked with self-check tiles"
                )
            _at_most_one_question_per_tile(self.problems)
            possible = count_possible_prime_composite_answers(types, self.largest_number)
            if self.problems > possible:
                raise _too_many_problems(
                    possible,
                    "repeated answers",
                    "choice of question types and largest number",
                    {
                        "largest number": _smallest_raise(
                            lambda largest: count_possible_prime_composite_answers(types, largest),
                            self.problems,
                            self.largest_number,
                            LARGEST_PRIME_COMPOSITE_LARGEST,
                        )
                    },
                )
        return self


def _prime_composite_types(ticked: Sequence[str]) -> list[QuestionType]:
    """Return the ticked question types, each once, in the order of ``QuestionType``."""
    return [question_type for question_type in QuestionType if question_type.value in ticked]


class OrderOfOperationsOptions(HeaderOptions):
    """
    Options for the order of operations kind, built on the core. There is no seed: every sheet
    is new.
    """

    title: Title = ORDER_OF_OPERATIONS_NAME
    problems: Problems = 10
    # The problems are shared evenly among the ticked types. With tiles, the page greys out the
    # types that have no tiles form.
    question_types: list[OrderOfOperationsTypeChoice] = Field(
        [question_type.value for question_type in OrderOfOperationsType],
        min_length=1,
        title="Question types",
        json_schema_extra={"labels": ORDER_OF_OPERATIONS_TYPE_LABELS},
    )
    # Each problem's drawn from those ticked. The parentheses and which-has-the-value questions
    # need a group, so with only No grouping ticked they have one level.
    grouping: list[GroupingChoice] = Field(
        ["one", "two"],
        min_length=1,
        title="Grouping",
        json_schema_extra={"labels": GROUPING_LABELS},
    )
    group_symbols: GroupSymbolsChoice = Field(
        "brackets",
        title="Groups inside groups",
        json_schema_extra={"input": "radio", "labels": GROUP_SYMBOLS_LABELS},
    )
    implied: bool = Field(True, title="Multiplication without a sign: 3(25 + 19)")
    # Fractions are in about 1 problem in 10, decimals in about 1 in 3 of the rest, when whole
    # numbers are ticked too.
    numbers: list[NumberKindChoice] = Field(
        [kind.value for kind in NumberKind],
        min_length=1,
        title="Numbers",
        json_schema_extra={"labels": NUMBER_KIND_LABELS},
    )
    # The label says enough, so the page shows the description only on mouseover.
    largest_number: int = Field(
        50,
        ge=10,
        le=1_000,
        title="Largest number in an expression",
        description="Answers and later steps can be larger: 25(5) \N{MULTIPLICATION SIGN} 12 = "
        "1,500.",
        json_schema_extra={"mouseover": True},
    )
    largest_multiplier: int = Field(
        12,
        ge=2,
        le=99,
        title="Largest multiplier or divisor",
        description="The smaller number in each multiplication, and every divisor, is at most "
        "this.",
        json_schema_extra={"mouseover": True},
    )
    multiple_choice: bool = Field(
        False,
        title="Multiple choice",
        description="Lettered choices instead of answer lines. The wrong ones are common "
        "mistakes, such as working left to right or ignoring the parentheses.",
    )
    answer_key: AnswerKey = False
    # Tiles ask forms of the questions whose answer is a number, and add an answer bank page.
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @model_validator(mode="after")
    def _tiles_are_available(self) -> Self:
        # Not built for multiple choice: each choice's letter would need coding as a number. The
        # page hides multiple choice while tiles are ticked, and greys out the tiles while it is.
        # Runs first, so a request with both is told so before anything else.
        if self.self_check_tiles and self.multiple_choice:
            raise ValueError("self_check_tiles: not available with multiple choice")
        return self

    @model_validator(mode="after")
    def _enough_different_answers(self) -> Self:
        # With tiles, an answer must be a number the question doesn't print, and no two answers
        # are the same: "How many have the value?" alone has only 0 to 4.
        if self.self_check_tiles:
            types = _order_of_operations_types(self.question_types)
            without = [
                ORDER_OF_OPERATIONS_TYPE_NAMES[each]
                for each in types
                if each not in ORDER_OF_OPERATIONS_TILE_TYPES
            ]
            if without:
                raise ValueError(
                    f"question_types: {_listed(without)} can't be asked with self-check tiles"
                )
            _at_most_one_question_per_tile(self.problems)
            limit = tile_answers_limit(types)
            if limit is not None and self.problems > limit:
                raise _too_many_problems(limit, "repeated answers", "choice of question types", {})
        return self

    def settings(self) -> SheetSettings:
        """The sheet settings these options describe, as the generator takes them."""
        return SheetSettings(
            levels=tuple(GROUPING_LEVELS[choice] for choice in self.grouping),
            numbers=tuple(kind for kind in NumberKind if kind.value in self.numbers),
            symbols=GroupSymbols(self.group_symbols),
            implied=self.implied,
            largest_number=self.largest_number,
            largest_multiplier=self.largest_multiplier,
        )


def _order_of_operations_types(ticked: Sequence[str]) -> list[OrderOfOperationsType]:
    """Return the ticked question types, each once, in the order of ``QuestionType``."""
    return [each for each in OrderOfOperationsType if each.value in ticked]


class SlopeAndInterceptsOptions(HeaderOptions):
    """
    Options for the slope and intercepts kind, built on the core. There is no seed: every sheet is
    new.
    """

    title: Title = SLOPE_AND_INTERCEPTS_NAME
    problems: Problems = 6
    # Each problem takes the next pair of a form and a question from a shuffled deck of those
    # that can be asked.
    # Every form starts ticked, x = a and y = b too, which makes them about 1 question in 7.
    given: list[LineFormChoice] = Field(
        [
            "slope_intercept",
            "standard",
            "point_slope",
            "point_and_slope",
            "two_points",
            "vertical",
            "horizontal",
            "table",
            "graph",
        ],
        min_length=1,
        title="Lines given as",
        json_schema_extra={"labels": LINE_FORM_LABELS},
    )
    blank_grids: BlankGrids = True
    asked: list[LineFeatureChoice] = Field(
        ["slope", "rate_of_change", "y_intercept", "x_intercept", "zero", "slope_and_y_intercept"],
        min_length=1,
        title="Questions ask for",
        json_schema_extra={"labels": LINE_FEATURE_LABELS},
    )
    # How an x- or y-intercept is answered, each question's drawn from those ticked. The page
    # shows these only while an intercept is ticked (see builder.html).
    intercept_answers: list[InterceptAnswerChoice] = Field(
        ["number", "point"],
        min_length=1,
        title="Intercepts as",
        json_schema_extra={"labels": INTERCEPT_ANSWER_LABELS},
    )
    largest_coordinate: LargestCoordinate = SHEET_LARGEST_COORDINATE
    largest_denominator: LargestDenominator = DEFAULT_LARGEST_DENOMINATOR
    whole_intercepts: WholeIntercepts = False
    number_styles: LineNumberStyles = Field(["fraction", "decimal"])
    answer_key: AnswerKey = False
    multiple_choice: LineMultipleChoice = False
    # Tiles replace the answer lines with an answer bank page, every answer different.
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @model_validator(mode="after")
    def _tiles_are_available(self) -> Self:
        # Not built for multiple choice: each choice's letter would need coding as a number. The
        # page hides multiple choice while tiles are ticked, and greys out the tiles while it is.
        # Runs first, so a request with both is told so before anything else.
        if self.self_check_tiles and self.multiple_choice:
            raise ValueError("self_check_tiles: not available with multiple choice")
        return self

    @model_validator(mode="after")
    def _a_question_can_be_made(self) -> Self:
        given, asked = _line_forms(self), _line_features(self)
        if not any(can_ask(form, feature) for form in given for feature in asked):
            raise ValueError(
                "asked: none of these fits the lines given. A vertical line has only a slope and "
                "an x-intercept, a horizontal line has no x-intercept or zero, and a point and "
                "the slope give the slope away"
            )
        if self.self_check_tiles:
            _at_most_one_question_per_tile(self.problems)
        # Each form shows the lines its options allow, and no line repeats on a sheet; with
        # tiles, no answer does.
        repeats = "repeated answers" if self.self_check_tiles else "repeats"
        _enough_lines(self, repeats, self._count_lines, self._unticks)
        return self

    def _count_lines(
        self,
        largest_coordinate: int,
        largest_denominator: int,
        forms: Sequence[LineForm] | None = None,
    ) -> int:
        """
        Return how many problems these options allow without repeating a line, up to the number
        asked, or allow with ``forms`` given instead of the ticked ones.
        """
        return count_possible_lines(
            _line_forms(self) if forms is None else forms,
            _line_features(self),
            largest_coordinate=largest_coordinate,
            largest_denominator=largest_denominator,
            whole_intercepts=self.whole_intercepts,
            number_styles=[NumberStyle(style) for style in self.number_styles],
            distinct_answers=self.self_check_tiles,
            limit=self.problems,
        )

    def _unticks(self) -> list[str]:
        """
        Return the labels of the ticked forms, such as x = a with few lines at a small largest
        number, whose unticking would allow the problems, as ``_boxes_to_untick`` finds them.
        """
        features = _line_features(self)
        forms = _boxes_to_untick(
            _line_forms(self),
            lambda given: any(can_ask(form, feature) for form in given for feature in features),
            lambda given: self._count_lines(
                self.largest_coordinate, self.largest_denominator, given
            ),
            self.problems,
        )
        return [LINE_FORM_NAMES[form] for form in forms]


class WritingLinearEquationsOptions(HeaderOptions):
    """
    Options for the writing linear equations kind, built on the core. There is no seed: every
    sheet is new.
    """

    title: Title = WRITING_LINEAR_EQUATIONS_NAME
    problems: Problems = 6
    # Each problem takes the next pair of a given and a form from a shuffled deck of those that
    # can be asked.
    given: list[EquationGivenChoice] = Field(
        [
            "slope_intercept",
            "standard",
            "point_slope",
            "point_and_slope",
            "two_points",
            "table",
            "graph",
            "parallel",
            "perpendicular",
        ],
        min_length=1,
        title="Lines given as",
        json_schema_extra={"labels": EQUATION_GIVEN_LABELS},
    )
    blank_grids: BlankGrids = True
    # Every form starts ticked, x = a and y = b too, which makes them about 1 question in 3: x = a
    # is asked of two points, a point and slope, a graph and both relations, and y = b of those
    # and a table.
    asked: list[EquationFormChoice] = Field(
        ["slope_intercept", "standard", "point_slope", "vertical", "horizontal"],
        min_length=1,
        title="Write equations in",
        json_schema_extra={"labels": EQUATION_FORM_LABELS},
    )
    statements: Statements = True
    largest_coordinate: LargestCoordinate = SHEET_LARGEST_COORDINATE
    largest_denominator: LargestDenominator = DEFAULT_LARGEST_DENOMINATOR
    whole_intercepts: WholeIntercepts = False
    number_styles: LineNumberStyles = Field(["fraction", "decimal"])
    answer_key: AnswerKey = False
    multiple_choice: LineMultipleChoice = False
    # Tiles replace the answer lines with an answer bank page. No line repeats, so no answer
    # does.
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @model_validator(mode="after")
    def _tiles_are_available(self) -> Self:
        # Not built for multiple choice: each choice's letter would need coding as a number. The
        # page hides multiple choice while tiles are ticked, and greys out the tiles while it is.
        # Runs first, so a request with both is told so before anything else.
        if self.self_check_tiles and self.multiple_choice:
            raise ValueError("self_check_tiles: not available with multiple choice")
        return self

    @model_validator(mode="after")
    def _a_question_can_be_made(self) -> Self:
        givens, forms = _equation_givens(self), _equation_forms(self)
        if not any(can_write(given, form) for given in givens for form in forms):
            raise ValueError(
                "asked: none of these can be written from the lines given. An equation isn't "
                "rewritten in its own form, and point-slope form, x = a and y = b need a point "
                "given"
            )
        if self.self_check_tiles:
            _at_most_one_question_per_tile(self.problems)
        _enough_lines(self, "repeats", self._count_lines, self._unticks)
        return self

    def _count_lines(
        self,
        largest_coordinate: int,
        largest_denominator: int,
        givens: Sequence[LineForm | Relation] | None = None,
        forms: Sequence[LineForm] | None = None,
    ) -> int:
        """
        Return how many problems these options allow without repeating a line, up to the number
        asked, or allow with ``givens`` or ``forms`` instead of the ticked ones.
        """
        return count_possible_equations(
            _equation_givens(self) if givens is None else givens,
            _equation_forms(self) if forms is None else forms,
            largest_coordinate=largest_coordinate,
            largest_denominator=largest_denominator,
            whole_intercepts=self.whole_intercepts,
            number_styles=[NumberStyle(style) for style in self.number_styles],
            limit=self.problems,
        )

    def _unticks(self) -> list[str]:
        """
        Return the labels of the ticked forms, such as x = a and y = b with few lines at a small
        largest number, or failing those, of the ticked givens, whose unticking would allow the
        problems, as ``_boxes_to_untick`` finds them.
        """
        givens, forms = _equation_givens(self), _equation_forms(self)
        numbers = self.largest_coordinate, self.largest_denominator
        written = _boxes_to_untick(
            forms,
            lambda asked: any(can_write(given, form) for given in givens for form in asked),
            lambda asked: self._count_lines(*numbers, forms=asked),
            self.problems,
        )
        if written:
            return [LINE_FORM_NAMES[form] for form in written]
        shown = _boxes_to_untick(
            givens,
            lambda given: any(can_write(each, form) for each in given for form in forms),
            lambda given: self._count_lines(*numbers, givens=given),
            self.problems,
        )
        return [EQUATION_GIVEN_NAMES[given] for given in shown]


class GraphingLinearEquationsOptions(HeaderOptions):
    """
    Options for the graphing linear equations kind, built on the core. There is no seed: every
    sheet is new.
    """

    title: Title = GRAPHING_LINEAR_EQUATIONS_NAME
    problems: Problems = 6
    # Each problem takes the next pair of a given and what is asked from a shuffled deck of those
    # that can be asked. Every given starts ticked; a graph is only tabled.
    given: list[GraphingGivenChoice] = Field(
        [
            "slope_intercept",
            "standard",
            "point_slope",
            "slope_and_intercept",
            "intercepts",
            "point_and_slope",
            "two_points",
            "vertical",
            "horizontal",
            "graph",
        ],
        min_length=1,
        title="Lines given as",
        json_schema_extra={"labels": GRAPHING_GIVEN_LABELS},
    )
    asked: list[GraphingAskedChoice] = Field(
        ["graph", "table"],
        min_length=1,
        title="Questions ask to",
        json_schema_extra={"labels": GRAPHING_ASKED_LABELS},
    )
    largest_coordinate: LargestCoordinate = SHEET_LARGEST_COORDINATE
    largest_denominator: LargestDenominator = DEFAULT_LARGEST_DENOMINATOR
    whole_intercepts: WholeIntercepts = False
    number_styles: LineNumberStyles = Field(["fraction", "decimal"])
    answer_key: AnswerKey = False
    multiple_choice: GraphingMultipleChoice = False
    # Tiles replace the blank grids and tables with an answer bank of the graphs and tables. No
    # line repeats, so no answer does.
    self_check_tiles: SelfCheckTiles = False
    tile_pattern: TilePattern = "simple"

    @model_validator(mode="after")
    def _tiles_are_available(self) -> Self:
        # Not built for multiple choice: each choice's letter would need coding as a number. The
        # page hides multiple choice while tiles are ticked, and greys out the tiles while it is.
        # Runs first, so a request with both is told so before anything else.
        if self.self_check_tiles and self.multiple_choice:
            raise ValueError("self_check_tiles: not available with multiple choice")
        return self

    @model_validator(mode="after")
    def _a_question_can_be_made(self) -> Self:
        givens, asked = _graphing_givens(self), _graphing_asked(self)
        if not any(can_graph(given, form) for given in givens for form in asked):
            raise ValueError(
                "asked: none of these fits the lines given. A table is completed from an "
                "equation or a graph, never from x = a, and a graph isn't graphed again"
            )
        if self.self_check_tiles:
            _at_most_one_question_per_tile(self.problems)
        _enough_lines(self, "repeats", self._count_lines, self._unticks)
        return self

    def _count_lines(
        self,
        largest_coordinate: int,
        largest_denominator: int,
        givens: Sequence[LineForm] | None = None,
    ) -> int:
        """
        Return how many problems these options allow without repeating a line, up to the number
        asked, or allow with ``givens`` instead of the ticked ones.
        """
        return count_possible_graphs(
            _graphing_givens(self) if givens is None else givens,
            _graphing_asked(self),
            largest_coordinate=largest_coordinate,
            largest_denominator=largest_denominator,
            whole_intercepts=self.whole_intercepts,
            number_styles=[NumberStyle(style) for style in self.number_styles],
            limit=self.problems,
        )

    def _unticks(self) -> list[str]:
        """
        Return the labels of the ticked givens, such as x = a and y = b with few lines at a small
        largest number, whose unticking would allow the problems, as ``_boxes_to_untick`` finds
        them.
        """
        asked = _graphing_asked(self)
        givens = _boxes_to_untick(
            _graphing_givens(self),
            lambda given: any(can_graph(each, form) for each in given for form in asked),
            lambda given: self._count_lines(
                self.largest_coordinate, self.largest_denominator, given
            ),
            self.problems,
        )
        return [LINE_FORM_NAMES[given] for given in givens]


def _enough_lines(
    options: SlopeAndInterceptsOptions
    | WritingLinearEquationsOptions
    | GraphingLinearEquationsOptions,
    repeats: str,
    count: Callable[[int, int], int],
    unticks: Callable[[], Sequence[str]],
) -> None:
    """
    Raise ``_too_many_problems`` if the line sheet ``options`` ask for more problems than
    ``count`` allows without ``repeats`` at their largest number in a point and largest
    denominator. It suggests the boxes to untick that ``unticks`` names, and the smallest raise
    of each number that would allow the problems.
    """
    possible = count(options.largest_coordinate, options.largest_denominator)
    if options.problems <= possible:
        return
    raises = {
        "largest number in a point": _smallest_raise(
            lambda value: count(value, options.largest_denominator),
            options.problems,
            options.largest_coordinate,
            LARGEST_LARGEST_COORDINATE,
        ),
        "largest denominator": _smallest_raise(
            lambda value: count(options.largest_coordinate, value),
            options.problems,
            options.largest_denominator,
            LARGEST_LARGEST_DENOMINATOR,
        ),
    }
    raise _too_many_problems(possible, repeats, "choice of lines and numbers", raises, unticks())


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
    no_regroup: bool = Field(False, title="Mix in problems without regrouping")
    bw: bool = Field(False, title="Black and white (saves toner)")

    @model_validator(mode="after")
    def _has_problems(self) -> Self:
        if not 1 <= self.represent + self.add + self.sub <= MAX_PROBLEMS:
            raise ValueError(f"represent + add + sub must be 1 to {MAX_PROBLEMS}")
        return self


def _basic_operations(options: BasicOperationOptions, out: BinaryIO) -> None:
    # Division's largest operand is its dividend. Only division uses largest_divisor.
    if options.missing_number != "answer":
        _missing_number(options, Operation.DIVIDE, out)
    elif options.self_check_tiles:
        # The answer bank replaces the options, so there are no wrong answers.
        questions = generate_basic_operation_questions(
            options.problems,
            options.chosen_operations,
            high=options.max_number,
            largest_dividend=options.largest_dividend,
            largest_divisor=options.largest_divisor,
            wrong_answer_count=0,
            distinct_answers=True,
        )
        _render_tiles(
            options, [basic_operation_tile_question(question.data) for question in questions], out
        )
    else:
        questions = generate_basic_operation_questions(
            options.problems,
            options.chosen_operations,
            high=options.max_number,
            largest_dividend=options.largest_dividend,
            largest_divisor=options.largest_divisor,
        )
        render_basic_operations_worksheet(
            questions=questions,
            path=out,
            header=options.header(),
            answer_key=options.answer_key,
        )


def _missing_number(options: BasicOperationOptions, operation: Operation, out: BinaryIO) -> None:
    """Render missing-number equations, as a fill-in sheet or a self-check tiles sheet."""
    questions = generate_missing_number_questions(
        options.problems,
        operation,
        MISSING_NUMBERS[options.missing_number],
        high=options.largest_dividend,
        largest_divisor=options.largest_divisor,
        distinct_answers=options.self_check_tiles,
    )
    if options.self_check_tiles:
        _render_tiles(
            options, [missing_number_tile_question(question.data) for question in questions], out
        )
    else:
        render_missing_number_worksheet(
            questions=questions,
            path=out,
            header=options.header(),
            answer_key=options.answer_key,
        )


def _place_value(options: PlaceValueOptions, out: BinaryIO) -> None:
    questions = generate_place_value_questions(
        options.problems,
        _place_value_forms(options.given, options.given_mix),
        _place_value_forms(options.asked, options.asked_mix),
        low=options.min_number,
        high=options.max_number,
        wrong_answer_count=WRONG_ANSWER_COUNT if options.multiple_choice else 0,
    )
    if options.self_check_tiles:
        _render_tiles(
            options, [place_value_tile_question(question.data) for question in questions], out
        )
    else:
        render_place_value_worksheet(
            questions=questions,
            path=out,
            header=options.header(),
            answer_key=options.answer_key,
        )


def _place_value_forms(choice: FormChoice, mix: list[WrittenFormChoice]) -> list[PlaceValueForm]:
    """
    Return the forms a question may take: the chosen one, or for mixed the ticked ones, each
    once, in the order of ``PlaceValueForm``.
    """
    if choice == "mixed":
        return [form for form in WRITTEN_FORMS if form.value in mix]
    return [PlaceValueForm(choice)]


def _render_tiles(
    options: BasicOperationOptions | PlaceValueOptions,
    questions: Sequence[TileQuestion],
    out: BinaryIO,
) -> None:
    """Render a self-check tiles sheet for ``questions``, with slots for the requested pattern."""
    render_self_check_tiles_worksheet(
        questions=questions,
        slot_of=_tile_slots(options),
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
    )


def _tile_slots(
    options: BasicOperationOptions
    | PlaceValueOptions
    | WordProblemOptions
    | BaseTenBlocksOptions
    | InputOutputTableOptions
    | PrimeCompositeOptions
    | OrderOfOperationsOptions
    | SlopeAndInterceptsOptions
    | WritingLinearEquationsOptions
    | GraphingLinearEquationsOptions
    | DataGraphsOptions,
    tiles: int | None = None,
) -> Sequence[int]:
    """
    Return the slot of each tile's answer, for the requested tile pattern. There is a tile for
    each question, unless ``tiles`` says how many.
    """
    make_slots = conventional_slot_of if options.tile_pattern == "simple" else random_slot_of
    return make_slots(options.problems if tiles is None else tiles)


def _word_problems(options: WordProblemOptions, out: BinaryIO) -> None:
    representation = Representation(options.representation)
    questions: Sequence[WordProblemQuestion]
    if options.choices and representation is Representation.NUMBER_LINE:
        questions = generate_number_line_choice_problems(
            options.problems, _operations(options.operations), largest_number=options.max_number
        )
    elif options.choices:
        questions = generate_equation_choice_problems(
            options.problems, _operations(options.operations), largest_number=options.max_number
        )
    elif options.steps == "two":
        questions = generate_two_step_problems(
            options.problems,
            _operations(options.operations),
            distinct_answers=options.self_check_tiles,
            largest_number=options.max_number,
            shapes=options.shapes,
        )
    else:
        questions = generate_word_problems(
            options.problems,
            _operations(options.operations),
            distinct_answers=options.self_check_tiles,
            # No comparisons on strip or blocks sheets: a strip shows parts making a whole, and
            # blocks show the first number with the second crossed out, taken away.
            comparisons=representation not in (Representation.STRIP, Representation.BLOCKS),
            largest_number=options.max_number,
            largest_operand=options.largest_operand,
        )
    render_word_problems_worksheet(
        questions=questions,
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        representation=representation,
        hints=not options.no_hints,
        slot_of=_tile_slots(options) if options.self_check_tiles else None,
        black_and_white=options.black_and_white,
        work_box=options.work_box,
    )


def _strip_choice(options: StripChoiceOptions, out: BinaryIO) -> None:
    questions: Sequence[StripChoiceQuestion | TwoStepStripChoiceQuestion]
    if options.steps == "two":
        questions = generate_two_step_strip_choice_problems(
            options.problems,
            _operations(options.operations),
            largest_number=options.max_number,
            largest_groups=options.max_groups,
        )
    else:
        questions = generate_strip_choice_problems(
            options.problems,
            _operations(options.operations),
            largest_number=options.max_number,
            largest_groups=options.max_groups,
        )
    render_strip_choice_worksheet(
        questions=questions,
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        prompt=Prompt(options.prompt),
    )


def _multiplication_models(options: MultiplicationModelsOptions, out: BinaryIO) -> None:
    render_multiplication_models_worksheet(
        questions=generate_multiplication_model_problems(
            options.problems, largest_factor=options.max_factor, largest_product=options.max_product
        ),
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        jump_labels=not options.no_jump_labels,
    )


def _base_ten_blocks(options: BaseTenBlocksOptions, out: BinaryIO) -> None:
    render_base_ten_blocks_worksheet(
        questions=generate_blocks_questions(
            options.problems,
            _blocks_question_types(options.questions),
            smallest=options.min_number,
            largest=options.max_number,
            regrouping=Regrouping(options.regrouping),
            distinct_answers=options.self_check_tiles,
        ),
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        slot_of=_tile_slots(options) if options.self_check_tiles else None,
        black_and_white=options.black_and_white,
    )


def _data_graphs(options: DataGraphsOptions, out: BinaryIO) -> None:
    problems = generate_discrete_data_problems(
        options.problems,
        [DataDisplay(display) for display in options.displays],
        [DiscreteDataPart(part) for part in options.questions],
        multiple_choice=options.multiple_choice,
        distinct_answers=options.self_check_tiles,
    )
    tiles = sum(len(problem.word_problems) for problem in problems)
    render_data_graphs_worksheet(
        problems=problems,
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        list_styles=_list_styles(options.list_style, len(problems)),
        slot_of=_tile_slots(options, tiles) if options.self_check_tiles else None,
    )


def _list_styles(choice: MixedListStyleChoice, count: int) -> list[NumberListStyle]:
    """Return each problem's list style: the one chosen, or for mix, one drawn at random."""
    if choice == "mix":
        return [random.choice(list(NumberListStyle)) for _ in range(count)]
    return [NumberListStyle(choice)] * count


def _input_output_tables(options: InputOutputTableOptions, out: BinaryIO) -> None:
    render_input_output_tables_worksheet(
        questions=generate_input_output_table_questions(
            options.problems,
            _operations(options.operations),
            blanks=Blanks(options.blanks),
            choice_types=[
                choice_type
                for choice_type in ChoiceType
                if options.multiple_choice and choice_type.value in options.question_types
            ],
            distinct_answers=options.self_check_tiles,
        ),
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        slot_of=_tile_slots(options) if options.self_check_tiles else None,
    )


def _prime_composite(options: PrimeCompositeOptions, out: BinaryIO) -> None:
    render_prime_composite_worksheet(
        questions=generate_prime_composite_questions(
            options.problems,
            _prime_composite_types(options.question_types),
            largest_number=options.largest_number,
            multiple_choice=options.multiple_choice,
            distinct_answers=options.self_check_tiles,
        ),
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        slot_of=_tile_slots(options) if options.self_check_tiles else None,
    )


def _order_of_operations(options: OrderOfOperationsOptions, out: BinaryIO) -> None:
    render_order_of_operations_worksheet(
        questions=generate_order_of_operations_questions(
            options.problems,
            _order_of_operations_types(options.question_types),
            options.settings(),
            multiple_choice=options.multiple_choice,
            distinct_answers=options.self_check_tiles,
        ),
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        slot_of=_tile_slots(options) if options.self_check_tiles else None,
    )


def _slope_and_intercepts(options: SlopeAndInterceptsOptions, out: BinaryIO) -> None:
    render_line_equations_worksheet(
        questions=generate_line_questions(
            options.problems,
            _line_forms(options),
            _line_features(options),
            largest_coordinate=options.largest_coordinate,
            largest_denominator=options.largest_denominator,
            whole_intercepts=options.whole_intercepts,
            number_styles=[NumberStyle(style) for style in options.number_styles],
            as_point_choices=[answer == "point" for answer in options.intercept_answers],
            wrong_answer_count=WRONG_ANSWER_COUNT if options.multiple_choice else 0,
            distinct_answers=options.self_check_tiles,
            blank_grids=options.blank_grids,
        ),
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        slot_of=_tile_slots(options) if options.self_check_tiles else None,
    )


def _line_forms(options: SlopeAndInterceptsOptions) -> list[LineForm]:
    """Return the ticked forms, each once, in the order of ``LineForm``."""
    return [form for form in LineForm if form.value in options.given]


def _line_features(options: SlopeAndInterceptsOptions) -> list[LineFeature]:
    """Return the ticked features, each once, in the order of ``LineFeature``."""
    return [feature for feature in LineFeature if feature.value in options.asked]


def _writing_linear_equations(options: WritingLinearEquationsOptions, out: BinaryIO) -> None:
    render_line_equations_worksheet(
        questions=generate_equation_questions(
            options.problems,
            _equation_givens(options),
            _equation_forms(options),
            largest_coordinate=options.largest_coordinate,
            largest_denominator=options.largest_denominator,
            whole_intercepts=options.whole_intercepts,
            number_styles=[NumberStyle(style) for style in options.number_styles],
            wrong_answer_count=WRONG_ANSWER_COUNT if options.multiple_choice else 0,
            blank_grids=options.blank_grids,
            statements=options.statements,
        ),
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        slot_of=_tile_slots(options) if options.self_check_tiles else None,
    )


def _graphing_linear_equations(options: GraphingLinearEquationsOptions, out: BinaryIO) -> None:
    render_line_equations_worksheet(
        questions=generate_graphing_questions(
            options.problems,
            _graphing_givens(options),
            _graphing_asked(options),
            largest_coordinate=options.largest_coordinate,
            largest_denominator=options.largest_denominator,
            whole_intercepts=options.whole_intercepts,
            number_styles=[NumberStyle(style) for style in options.number_styles],
            wrong_answer_count=WRONG_ANSWER_COUNT if options.multiple_choice else 0,
            distinct_answers=options.self_check_tiles,
        ),
        path=out,
        header=options.header(),
        answer_key=options.answer_key,
        slot_of=_tile_slots(options) if options.self_check_tiles else None,
    )


def _graphing_givens(options: GraphingLinearEquationsOptions) -> list[LineForm]:
    """Return the ticked givens, each once, in the order of ``GRAPHING_GIVENS``."""
    return [given for given in GRAPHING_GIVENS if given.value in options.given]


def _graphing_asked(options: GraphingLinearEquationsOptions) -> list[LineForm]:
    """Return the ticked asks, each once, in the order of ``GRAPHING_ASKED``."""
    return [form for form in GRAPHING_ASKED if form.value in options.asked]


def _equation_givens(options: WritingLinearEquationsOptions) -> list[LineForm | Relation]:
    """Return the ticked givens, each once, in the order of ``EQUATION_GIVENS``."""
    return [given for given in EQUATION_GIVENS if given.value in options.given]


def _equation_forms(options: WritingLinearEquationsOptions) -> list[LineForm]:
    """Return the ticked forms, each once, in the order of ``EQUATION_FORMS``."""
    return [form for form in EQUATION_FORMS if form.value in options.asked]


def _block(options: BlockOptions, seed: int, out: BinaryIO) -> None:
    problems = block.build_problems(random.Random(seed), options.problems)
    block.render(
        problems=problems,
        path=out,
        title=options.title,
        label=options.label,
        name_line=options.name_line,
        teks="Texas TEKS 2.2(A), 3.4(A)",
        seed=seed,
    )


def _word(options: WordOptions, seed: int, out: BinaryIO) -> None:
    problems = word.build_problems(random.Random(seed), options.problems)
    word.render(
        problems=problems,
        path=out,
        title=options.title,
        label=options.label,
        name_line=options.name_line,
        teks="Texas TEKS 3.4(A)",
        seed=seed,
    )


def _strip(options: StripOptions, seed: int, out: BinaryIO) -> None:
    problems = wp_common.build_problems(random.Random(seed), options.problems, hundreds_cap=9)
    strip.render(
        problems=problems,
        path=out,
        title=options.title,
        label=options.label,
        name_line=options.name_line,
        teks="Texas TEKS 3.5(A)",
        seed=seed,
        answer_key=options.answer_key,
    )


def _number_line(options: NumberLineOptions, seed: int, out: BinaryIO) -> None:
    problems = wp_common.build_problems(random.Random(seed), options.problems, hundreds_cap=9)
    number_line.render(
        problems=problems,
        path=out,
        title=options.title,
        label=options.label,
        name_line=options.name_line,
        teks="Texas TEKS 3.4(A), 3.5(A)",
        seed=seed,
    )


def _number_line_mc(options: NumberLineMCOptions, seed: int, out: BinaryIO) -> None:
    problems = wp_common.build_problems(
        random.Random(seed), options.problems, hundreds_cap=9, add_sorted=True
    )
    number_line_mc.render(
        problems=problems,
        path=out,
        title=options.title,
        label=options.label,
        name_line=options.name_line,
        teks="Texas TEKS 3.4(A), 3.5(A)",
        seed=seed,
    )


def _multiplication_mc(options: MultiplicationMCOptions, seed: int, out: BinaryIO) -> None:
    problems = multiplication_mc.build_problems(
        random.Random(seed), options.problems, options.max_factor, options.max_product
    )
    multiplication_mc.render(
        problems=problems,
        path=out,
        title=options.title,
        label=options.label,
        name_line=options.name_line,
        teks="Texas TEKS 3.4(K)",
        seed=seed,
        jump_labels=not options.no_jump_labels,
    )


def _data_graph(options: DataGraphOptions, seed: int, out: BinaryIO) -> None:
    problems = data_graph.build_problems(random.Random(seed), options.problems, options.list_style)
    data_graph.render(
        problems=problems,
        path=out,
        title=options.title,
        label=options.label,
        name_line=options.name_line,
        teks="Texas TEKS 3.8(A), 3.8(B)",
        seed=seed,
    )


def _data_graph_mc(options: DataGraphMCOptions, seed: int, out: BinaryIO) -> None:
    problems = data_graph_mc.build_problems(
        random.Random(seed), options.problems, options.list_style
    )
    data_graph_mc.render(
        problems=problems,
        path=out,
        title=options.title,
        label=options.label,
        name_line=options.name_line,
        teks="Texas TEKS 3.8(A)",
        seed=seed,
    )


def _worksheet(options: WorksheetOptions, seed: int, out: BinaryIO) -> None:
    problems = worksheet.build_problems(
        random.Random(seed),
        options.represent,
        options.add,
        options.sub,
        regroup=not options.no_regroup,
    )
    worksheet.render(
        problems=problems,
        path=out,
        title=options.title,
        subtitle="Represent, add, and subtract numbers within 1,000 using base-ten blocks.",
        name_line=options.name_line,
        teks="Texas TEKS 2.2(A), 2.4(C)",
        seed=seed,
        col=worksheet.BW if options.bw else worksheet.COLOR,
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
    "strip_choice": CoreKind(StripChoiceOptions, _strip_choice),
    "base_ten_blocks": CoreKind(BaseTenBlocksOptions, _base_ten_blocks),
    "multiplication_models": CoreKind(MultiplicationModelsOptions, _multiplication_models),
    "data_graphs": CoreKind(DataGraphsOptions, _data_graphs),
    "input_output_tables": CoreKind(InputOutputTableOptions, _input_output_tables),
    "prime_composite": CoreKind(PrimeCompositeOptions, _prime_composite),
    "order_of_operations": CoreKind(OrderOfOperationsOptions, _order_of_operations),
    "slope_and_intercepts": CoreKind(SlopeAndInterceptsOptions, _slope_and_intercepts),
    "writing_linear_equations": CoreKind(WritingLinearEquationsOptions, _writing_linear_equations),
    "graphing_linear_equations": CoreKind(
        GraphingLinearEquationsOptions, _graphing_linear_equations
    ),
}
