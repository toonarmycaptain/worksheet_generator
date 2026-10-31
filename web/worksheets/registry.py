"""The worksheet kinds the site serves, and how to render each one.

Each kind pairs an options schema, validated from the query string, with an adapter
that does what that script's ``main()`` does but renders into a buffer instead of a
file. Option names match the script's CLI flags (``--no-regroup`` -> ``no_regroup``).
Booleans all default to False, so an unticked HTML checkbox (sent as nothing) means
the default.

Temporary: the phase 5 CLI and shared core replace these adapters.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from typing import Annotated, Any, BinaryIO, Literal, Self

from ninja import Field, Schema
from pydantic import model_validator

from core.arithmetic import Operation
from core.arithmetic_generator import generate_arithmetic_questions, possible_answers
from core.self_check_tiles import SLOTS, random_slot_of
from render.pdf.arithmetic_worksheet import OPERATION_NAMES, render_arithmetic_worksheet
from render.pdf.self_check_tiles_worksheet import render_self_check_tiles_worksheet
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
MAX_PROBLEMS = 20

Title = Annotated[str, Field(min_length=1, max_length=80)]
Label = Annotated[str, Field(max_length=40)]
Problems = Annotated[int, Field(ge=1, le=MAX_PROBLEMS)]
ListStyle = Literal["mix", "grid", "commas"]


class Options(Schema):
    """Options every legacy kind takes. No seed means the endpoint picks a random one."""

    seed: int | None = Field(None, ge=0, le=MAX_SEED)


class ArithmeticOptions(Schema):
    """Options of a kind built on the core. It takes no seed: every sheet is new."""

    title: Title = OPERATION_NAMES[Operation.ADD]  # the operation's name, whichever it is
    label: Label = "Sheet A"
    problems: Problems = 8
    operation: Literal["add", "subtract", "multiply"] = Field("add", title="Operation")
    max_number: int = Field(10, ge=1, le=24, title="Largest number")
    answer_key: bool = Field(False, title="Add an answer key page")
    self_check_tiles: bool = Field(False, title="Self-check tile answers")

    @model_validator(mode="after")
    def _title_follows_the_operation(self) -> Self:
        # The default is the name of the default operation. A request that names another
        # operation and no title gets that operation's name.
        if "title" not in self.model_fields_set:
            self.title = OPERATION_NAMES[Operation(self.operation)]
        return self

    @model_validator(mode="after")
    def _enough_different_questions(self) -> Self:
        if self.self_check_tiles:
            # Question n uses tile n, so there are at most 12, and each needs its own answer.
            if self.problems > SLOTS:
                raise ValueError(
                    f"problems: self-check tiles has {SLOTS} tiles, so at most {SLOTS}"
                )
            answers = possible_answers(Operation(self.operation), high=self.max_number)
            if self.problems > len(answers):
                raise ValueError(
                    "problems: too many for that largest number, which allows no repeated answers"
                )
        else:
            # Operands run from 0 to max_number and a flipped pair counts as a repeat.
            values = self.max_number + 1
            if self.problems > values * (values + 1) // 2:
                raise ValueError(
                    "problems: too many for that largest number, which allows no repeats"
                )
        return self


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
    answer_key: bool = Field(False, title="Add an answer key page")


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


def _arithmetic(o: ArithmeticOptions, out: BinaryIO) -> None:
    operation = Operation(o.operation)
    if o.self_check_tiles:
        # The answer bank replaces the choices, so there are no wrong answers.
        questions = generate_arithmetic_questions(
            o.problems, operation, high=o.max_number, wrong_answer_count=0, distinct_answers=True
        )
        render_self_check_tiles_worksheet(
            [question.data for question in questions],
            random_slot_of(o.problems),
            out,
            o.title,
            o.label,
            o.answer_key,
        )
    else:
        questions = generate_arithmetic_questions(o.problems, operation, high=o.max_number)
        render_arithmetic_worksheet(questions, out, o.title, o.label, o.answer_key)


def _block(o: BlockOptions, seed: int, out: BinaryIO) -> None:
    problems = block.build_problems(random.Random(seed), o.problems)
    block.render(problems, out, o.title, o.label, "Texas TEKS 2.2(A), 3.4(A)", seed)


def _word(o: WordOptions, seed: int, out: BinaryIO) -> None:
    problems = word.build_problems(random.Random(seed), o.problems)
    word.render(problems, out, o.title, o.label, "Texas TEKS 3.4(A)", seed)


def _strip(o: StripOptions, seed: int, out: BinaryIO) -> None:
    problems = wp_common.build_problems(random.Random(seed), o.problems, hundreds_cap=9)
    strip.render(problems, out, o.title, o.label, "Texas TEKS 3.5(A)", seed, o.answer_key)


def _number_line(o: NumberLineOptions, seed: int, out: BinaryIO) -> None:
    problems = wp_common.build_problems(random.Random(seed), o.problems, hundreds_cap=9)
    number_line.render(problems, out, o.title, o.label, "Texas TEKS 3.4(A), 3.5(A)", seed)


def _number_line_mc(o: NumberLineMCOptions, seed: int, out: BinaryIO) -> None:
    problems = wp_common.build_problems(
        random.Random(seed), o.problems, hundreds_cap=9, add_sorted=True
    )
    number_line_mc.render(problems, out, o.title, o.label, "Texas TEKS 3.4(A), 3.5(A)", seed)


def _multiplication_mc(o: MultiplicationMCOptions, seed: int, out: BinaryIO) -> None:
    problems = multiplication_mc.build_problems(
        random.Random(seed), o.problems, o.max_factor, o.max_product
    )
    multiplication_mc.render(
        problems, out, o.title, o.label, "Texas TEKS 3.4(K)", seed, not o.no_jump_labels
    )


def _data_graph(o: DataGraphOptions, seed: int, out: BinaryIO) -> None:
    problems = data_graph.build_problems(random.Random(seed), o.problems, o.list_style)
    data_graph.render(problems, out, o.title, o.label, "Texas TEKS 3.8(A), 3.8(B)", seed)


def _data_graph_mc(o: DataGraphMCOptions, seed: int, out: BinaryIO) -> None:
    problems = data_graph_mc.build_problems(random.Random(seed), o.problems, o.list_style)
    data_graph_mc.render(problems, out, o.title, o.label, "Texas TEKS 3.8(A)", seed)


def _worksheet(o: WorksheetOptions, seed: int, out: BinaryIO) -> None:
    problems = worksheet.build_problems(
        random.Random(seed), o.represent, o.add, o.sub, regroup=not o.no_regroup
    )
    worksheet.render(
        problems=problems,
        path=out,
        title=o.title,
        subtitle="Represent, add, and subtract numbers within 1,000 using base-ten blocks.",
        teks="Texas TEKS 2.2(A), 2.4(C)",
        seed=seed,
        col=worksheet.BW if o.bw else worksheet.COLOR,
    )


@dataclass(frozen=True)
class Kind[O: Options]:
    options: type[O]
    draw: Callable[[O, int, BinaryIO], None]

    def render(self, options: O, seed: int) -> bytes:
        """The PDF for these options and seed, as bytes."""
        out = BytesIO()
        self.draw(options, seed, out)
        return out.getvalue()


@dataclass(frozen=True)
class CoreKind[O: Schema]:
    """A kind built on the core. Unlike ``Kind`` it has no seed."""

    options: type[O]
    draw: Callable[[O, BinaryIO], None]

    def render(self, options: O) -> bytes:
        """The PDF for these options, as bytes."""
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
    "arithmetic": CoreKind(ArithmeticOptions, _arithmetic),
}
