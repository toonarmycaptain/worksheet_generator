"""
Helpers shared by the tests, so no test module imports from another.

- ``randint_returns`` and the other fakes: ``random`` made predictable, one function at a time
- the ``render_*`` functions: questions built by hand, and each worksheet rendered from them to
  PDF bytes
- ``pdf_text``: a PDF's drawing commands as readable text, so a test can compare and diff
  what the pages draw
- ``GOLDENS``, ``read_sections`` and ``write_section``: the golden files of expected text, a
  section per case, with YEAR for the year in the copyright notice
- ``refused``: Ninja's JSON error for an option the endpoint does not allow
"""

import base64
import random
import re
import zlib
from collections.abc import Callable, Sequence
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from core.base_ten_blocks import BlocksQuestionData
from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    TwoStepQuestionData,
)
from core.basic_operations.multiplication_models import MultiplicationModelsQuestion
from core.basic_operations.representation import (
    Prompt,
    Representation,
    StripChoiceQuestion,
    TwoStepStripChoiceQuestion,
    WordProblemQuestion,
    equation_choices,
    number_line_choices,
    stem,
    strip_choices,
    two_step_equation_choices,
    two_step_strip_choices,
)
from core.basic_operations.word_problems import unknown_letter
from core.discrete_data.data import (
    CategoricalDataProblemData,
    DiscreteDataProblem,
    NumericalDataProblemData,
    SummarizeDataQuestionData,
)
from core.input_output_tables.data import (
    InputOutputQuestion,
    InputOutputQuestionData,
    InputOutputRuleQuestionData,
)
from core.line_equations.data import LineAnswer, LineQuestionData, answer_of
from core.order_of_operations.data import OrderOfOperationsQuestion
from core.placevalue.data import PlaceValueQuestionData
from core.prime_composite.data import PrimeCompositeQuestion
from core.question import FreeResponse, Question, QuestionData, multiple_choice
from core.self_check_tiles import TileQuestion
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

GOLDENS = Path(__file__).parent / "goldens"


def randint_returns(monkeypatch: pytest.MonkeyPatch, drawn: list[int]) -> list[tuple[int, int]]:
    """
    Make ``random.randint`` return ``drawn`` in order, and return the bounds of each call.

    A value outside its call's bounds raises ``ValueError``, as the real ``randint`` never
    returns one, so a limit lost on the way to the generator shows up as a failed draw.
    """
    values = iter(drawn)
    bounds: list[tuple[int, int]] = []

    def randint(low: int, high: int) -> int:
        bounds.append((low, high))
        value = next(values)
        if not low <= value <= high:
            raise ValueError(f"{value} is not from {low} to {high}")
        return value

    monkeypatch.setattr(random, "randint", randint)
    return bounds


def randint_returns_low(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, int]]:
    """
    Make ``random.randint`` return ``low``, and return the bounds of each call.

    Only for one question at a time: always drawing ``low`` repeats the same operands, which
    a sheet of several questions would keep rejecting.
    """
    bounds: list[tuple[int, int]] = []

    def randint(low: int, high: int) -> int:
        bounds.append((low, high))
        return low

    monkeypatch.setattr(random, "randint", randint)
    return bounds


def sample_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``random.sample`` take the first ``k`` items, in order."""
    monkeypatch.setattr(random, "sample", lambda population, k: list(population[:k]))


def sample_last(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``random.sample`` take the last ``k`` items, in order: the top of a range."""
    monkeypatch.setattr(
        random, "sample", lambda population, k: list(population[len(population) - k :])
    )


def sample_returns(monkeypatch: pytest.MonkeyPatch, picks: list[list[Any]]) -> list[Sequence[Any]]:
    """
    Make ``random.sample`` return ``picks`` in order, and return the population of each call.

    A pick that is not ``k`` different items of the population raises ``ValueError``, as the
    real ``sample`` never returns one, so a pick also shows that the code offered it.
    """
    values = iter(picks)
    populations: list[Sequence[Any]] = []

    def sample(population: Sequence[Any], k: int) -> list[Any]:
        populations.append(population)
        pick = next(values)
        if len(pick) != k or len(set(pick)) != k or any(item not in population for item in pick):
            raise ValueError(f"{pick} is not {k} picks from {population}")
        return list(pick)

    monkeypatch.setattr(random, "sample", sample)
    return populations


def reverse_shuffle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``random.shuffle`` reverse the list."""
    monkeypatch.setattr(random, "shuffle", lambda items: items.reverse())


def choices_returns(monkeypatch: pytest.MonkeyPatch, picks: list[Any]) -> None:
    """
    Make ``random.choices`` return ``picks``, such as the operation drawn for each question.

    Picks that are not ``k`` items of the population raise ``ValueError``, as the real
    ``choices`` never returns them.
    """

    def choices(population: Sequence[Any], k: int) -> list[Any]:
        if k != len(picks) or any(pick not in population for pick in picks):
            raise ValueError(f"{picks} are not {k} picks from {population}")
        return list(picks)

    monkeypatch.setattr(random, "choices", choices)


def choices_in_turn(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Make ``random.choices`` take the population's items in turn, from the first.

    With one operation, every question gets it; with several, they take turns in order.
    """
    monkeypatch.setattr(
        random,
        "choices",
        lambda population, k: [population[index % len(population)] for index in range(k)],
    )


def choose_last(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``random.choice`` return the last item."""
    monkeypatch.setattr(random, "choice", lambda items: items[-1])


class _Last:
    """The type of ``LAST``."""


LAST = _Last()  # a pick for ``choice_returns``: the last of its call's items


def choice_returns(monkeypatch: pytest.MonkeyPatch, picks: list[Any]) -> list[Sequence[Any]]:
    """
    Make ``random.choice`` return ``picks`` in order, and return the items of each call.

    A pick that is not among its call's items raises ``ValueError``, as the real ``choice`` never
    returns one, so a pick also shows that the code offered it. A pick of ``LAST`` takes its
    call's last item, for a choice among values the code builds itself, such as the sets of wrong
    equations ``two_step_equation_choices`` chooses from.
    """
    values = iter(picks)
    offered: list[Sequence[Any]] = []

    def choice(items: Sequence[Any]) -> Any:
        offered.append(items)
        pick = next(values)
        if pick is LAST:
            return items[-1]
        if pick not in items:
            raise ValueError(f"{pick} is not one of {items}")
        return pick

    monkeypatch.setattr(random, "choice", choice)
    return offered


def choice_indexes(monkeypatch: pytest.MonkeyPatch, indexes: list[int]) -> list[Sequence[Any]]:
    """
    Make ``random.choice`` return the item at each of ``indexes`` in turn, and return the items
    of each call, for choices among values the code builds itself.
    """
    positions = iter(indexes)
    offered: list[Sequence[Any]] = []

    def choice(items: Sequence[Any]) -> Any:
        offered.append(items)
        return items[next(positions)]

    monkeypatch.setattr(random, "choice", choice)
    return offered


def random_returns(monkeypatch: pytest.MonkeyPatch, drawn: list[float]) -> None:
    """Make ``random.random`` return ``drawn`` in order."""
    values = iter(drawn)
    monkeypatch.setattr(random, "random", lambda: next(values))


def randrange_returns(monkeypatch: pytest.MonkeyPatch, drawn: list[int]) -> None:
    """
    Make ``random.randrange(stop)`` return ``drawn`` in order.

    A value outside the range raises ``ValueError``, as the real ``randrange`` never returns one.
    """
    values = iter(drawn)

    def randrange(stop: int) -> int:
        value = next(values)
        if not 0 <= value < stop:
            raise ValueError(f"{value} is not in range({stop})")
        return value

    monkeypatch.setattr(random, "randrange", randrange)


def conventional_slot_of_returns(monkeypatch: pytest.MonkeyPatch, slots: tuple[int, ...]) -> None:
    """
    Make ``conventional_slot_of``, the simple tile pattern's slots, return the first of ``slots``.

    It is replaced in ``worksheets.registry``, where the web code calls it.
    """
    monkeypatch.setattr("worksheets.registry.conventional_slot_of", lambda count: slots[:count])


def pdf_text(pdf: bytes) -> str:
    """The PDF's title, page sizes and each page's drawing commands, as text.

    reportlab writes each page as an ASCII85 and Flate encoded stream. Decoded, a line says
    what is drawn where, such as ``BT 1 0 0 1 54 738 Tm (Basic Operations) Tj T* ET``, so a changed
    title or a moved line is a changed line. Fonts are named, not embedded, in these PDFs.
    """
    title = re.search(rb"/Title \(((?:\\.|[^\\)])*)\)", pdf)
    boxes = re.findall(rb"/MediaBox \[ ([\d. ]+) \]", pdf)
    lines = [
        f"title: {title.group(1).decode('latin-1') if title else ''}",
        "media boxes: " + "; ".join(box.decode("ascii") for box in boxes),
    ]
    for number, raw in enumerate(re.findall(rb"stream\n(.*?)endstream", pdf, re.DOTALL), start=1):
        content = zlib.decompress(base64.a85decode(raw.strip().removesuffix(b"~>")))
        lines.append(f"--- stream {number}")
        lines.append(content.decode("latin-1").strip())
    return "\n".join(lines)


SECTION = re.compile(r"^=== (.+) ===$", re.MULTILINE)


# The golden text files have YEAR for the year in the copyright notice, so they hold every year.
GOLDEN_NOTICE = "YEAR toonarmycaptain.com"


def read_sections(path: Path) -> dict[str, str]:
    """
    The expected text of each case, by case name, with the current year for YEAR in the
    copyright notice. Empty if the file does not exist yet.
    """
    if not path.exists():
        return {}
    text = path.read_text().replace(GOLDEN_NOTICE, f"{date.today().year} toonarmycaptain.com")
    names = SECTION.findall(text)
    bodies = SECTION.split(text)[2::2]  # split() alternates: before, name, body, name, body...
    return {name: body.strip("\n") for name, body in zip(names, bodies, strict=True)}


def write_section(path: Path, name: str, text: str) -> None:
    """
    Write ``text`` as the section ``name`` of a golden file, keeping the other sections, with
    YEAR for the current year in the copyright notice.
    """
    sections = read_sections(path) | {name: text}
    golden = "".join(f"=== {case} ===\n{body}\n\n" for case, body in sections.items())
    path.write_text(golden.replace(f"{date.today().year} toonarmycaptain.com", GOLDEN_NOTICE))


def render_basic_operations(
    cases: list[tuple[BasicOperationQuestionData, tuple[int, ...]]],
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    out = BytesIO()
    render_basic_operations_worksheet(
        questions=[
            Question(data, multiple_choice((data.answer,), wrong_answers))
            for data, wrong_answers in cases
        ],
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
    )
    return out.getvalue()


def render_missing_numbers(
    cases: list[tuple[MissingNumberQuestionData, tuple[int, ...]]],
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    out = BytesIO()
    render_missing_number_worksheet(
        questions=[Question(data, FreeResponse()) for data, _ in cases],
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
    )
    return out.getvalue()


def render_place_value(
    cases: list[tuple[PlaceValueQuestionData, tuple[int, ...]]],
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    out = BytesIO()
    render_place_value_worksheet(
        questions=[
            Question(
                data,
                multiple_choice((data.answer,), wrong_answers) if wrong_answers else FreeResponse(),
            )
            for data, wrong_answers in cases
        ],
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
    )
    return out.getvalue()


def render_tiles[Data: QuestionData[Any]](
    questions: list[Data],
    to_tile: Callable[[Data], TileQuestion],
    slot_of: tuple[int, ...],
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    """Render the self-check tiles sheet, with ``to_tile`` making each question's tile question."""
    out = BytesIO()
    render_self_check_tiles_worksheet(
        questions=[to_tile(data) for data in questions],
        slot_of=slot_of,
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
    )
    return out.getvalue()


def render_word_problems(
    questions: list[BasicOperationQuestionData | TwoStepQuestionData],
    representation: Representation | list[Representation],
    choices: bool | list[bool],
    hints: bool,
    black_and_white: bool,
    work_box: bool,
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    """
    Render the word problems sheet, each question free response, with no wrong answers, or with
    ``choices`` multiple choice, its number lines made by ``number_line_choices`` or its equations
    by ``equation_choices``, or for a two-step question ``two_step_equation_choices`` with its
    wording's letter, either with the operations of the sheet's steps as those ticked. A list of
    representations, or of choices, gives each question its own, as on a mixed sheet.
    """
    out = BytesIO()
    operations = [
        operation
        for operation in Operation
        if any(operation in _operations_of(data) for data in questions)
    ]
    representations = (
        representation if isinstance(representation, list) else [representation] * len(questions)
    )
    chosen = choices if isinstance(choices, list) else [choices] * len(questions)
    made = [
        _word_problem(data, each, choice, operations)
        for data, each, choice in zip(questions, representations, chosen, strict=True)
    ]
    render_word_problems_worksheet(
        questions=made,
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
        representation=representation,
        hints=hints,
        slot_of=slot_of,
        black_and_white=black_and_white,
        work_box=work_box,
    )
    return out.getvalue()


def _operations_of(data: BasicOperationQuestionData | TwoStepQuestionData) -> set[Operation]:
    """Return the operations of the word problem's steps: its two, or its one."""
    if isinstance(data, TwoStepQuestionData):
        return {step.operation for step in data.steps}
    return {data.operation}


def _word_problem(
    data: BasicOperationQuestionData | TwoStepQuestionData,
    representation: Representation,
    choices: bool,
    operations: list[Operation],
) -> WordProblemQuestion:
    """Pair a word problem with its response, as ``render_word_problems`` describes."""
    if not choices:
        return Question(data, FreeResponse())
    if isinstance(data, TwoStepQuestionData):
        return Question(
            data, two_step_equation_choices(data, unknown_letter(stem(data)), operations)
        )
    if representation is Representation.NUMBER_LINE:
        return Question(data, number_line_choices(data))
    return Question(data, equation_choices(data, operations))


def render_strip_choice(
    questions: list[BasicOperationQuestionData | TwoStepQuestionData],
    prompt: Prompt,
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    """
    Render the strip choice sheet, each question's choices made by ``strip_choices``, or for a
    two-step question by ``two_step_strip_choices``.
    """
    out = BytesIO()
    made: list[StripChoiceQuestion | TwoStepStripChoiceQuestion] = [
        Question(data, two_step_strip_choices(data))
        if isinstance(data, TwoStepQuestionData)
        else Question(data, strip_choices(data))
        for data in questions
    ]
    render_strip_choice_worksheet(
        questions=made,
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
        prompt=prompt,
    )
    return out.getvalue()


def render_multiplication_models(
    questions: list[MultiplicationModelsQuestion],
    jump_labels: bool,
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    """
    Render the multiplication models sheet, each question with the models given to choose from.
    """
    out = BytesIO()
    render_multiplication_models_worksheet(
        questions=questions,
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
        jump_labels=jump_labels,
    )
    return out.getvalue()


def render_base_ten_blocks(
    questions: list[BlocksQuestionData],
    slot_of: tuple[int, ...] | None,
    black_and_white: bool,
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    """Render the base-ten blocks sheet, each question free response, with no wrong answers."""
    out = BytesIO()
    render_base_ten_blocks_worksheet(
        questions=[Question(data, FreeResponse()) for data in questions],
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
        slot_of=slot_of,
        black_and_white=black_and_white,
    )
    return out.getvalue()


def discrete_data_problem(
    summarize: SummarizeDataQuestionData,
    one_step: CategoricalDataProblemData | NumericalDataProblemData,
    two_step: CategoricalDataProblemData | NumericalDataProblemData,
) -> DiscreteDataProblem:
    """Make a data set's problem from its three questions' data, each free response."""
    return DiscreteDataProblem(
        dataset=summarize.dataset,
        given=summarize.given,
        summarize=Question(summarize, FreeResponse()),
        one_step=Question(one_step, FreeResponse()),
        two_step=Question(two_step, FreeResponse()),
    )


def render_data_graphs(
    problems: list[DiscreteDataProblem],
    list_styles: Sequence[NumberListStyle],
    answer_key: bool,
    title: str,
    label: str,
    slot_of: Sequence[int] | None = None,
    name_line: bool = True,
) -> bytes:
    """Render the data and graphs sheet, problem i's list in ``list_styles[i]``."""
    out = BytesIO()
    render_data_graphs_worksheet(
        problems=problems,
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
        list_styles=list_styles,
        slot_of=slot_of,
    )
    return out.getvalue()


def render_input_output_tables(
    questions: Sequence[tuple[InputOutputQuestionData, tuple[Any, ...]]],
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    """
    Render the input-output tables sheet. Each question is multiple choice among its answer, a
    table or a rule, and its wrong options; with none, it is free response: a table to complete,
    or a sentence to complete with the rule.
    """
    out = BytesIO()
    render_input_output_tables_worksheet(
        questions=[_input_output_question(data, wrong) for data, wrong in questions],
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
        slot_of=slot_of,
    )
    return out.getvalue()


def _input_output_question(
    data: InputOutputQuestionData, wrong: tuple[Any, ...]
) -> InputOutputQuestion:
    """Pair an input-output question with its response, as ``render_input_output_tables`` says."""
    if isinstance(data, InputOutputRuleQuestionData):
        return Question(data, multiple_choice((data.answer,), wrong) if wrong else FreeResponse())
    return Question(data, multiple_choice((data.answer,), wrong) if wrong else FreeResponse())


def render_line_questions(
    cases: Sequence[tuple[LineQuestionData, tuple[LineAnswer, ...]]],
    answer_key: bool,
    title: str,
    label: str,
    slot_of: tuple[int, ...] | None = None,
    name_line: bool = True,
) -> bytes:
    """
    Render a line sheet: slope and intercepts, or writing linear equations. Each question is
    multiple choice among its answer and its wrong answers; with none, it is free response.
    """
    out = BytesIO()
    render_line_equations_worksheet(
        questions=[
            Question(
                data,
                multiple_choice((answer_of(data),), wrong) if wrong else FreeResponse(),
            )
            for data, wrong in cases
        ],
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
        slot_of=slot_of,
    )
    return out.getvalue()


def render_prime_composite(
    questions: Sequence[PrimeCompositeQuestion],
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    """Render the prime and composite sheet, its questions given with their responses."""
    out = BytesIO()
    render_prime_composite_worksheet(
        questions=questions,
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
        slot_of=slot_of,
    )
    return out.getvalue()


def render_order_of_operations(
    questions: Sequence[OrderOfOperationsQuestion],
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    """Render the order of operations sheet, its questions given with their responses."""
    out = BytesIO()
    render_order_of_operations_worksheet(
        questions=questions,
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
        slot_of=slot_of,
    )
    return out.getvalue()


def refused(message: str) -> dict[str, Any]:
    """Return Ninja's JSON error for an after-validator that raised ``ValueError(message)``."""
    return {
        "detail": [
            {
                "type": "value_error",
                "loc": ["query", "options"],
                "msg": f"Value error, {message}",
                "ctx": {"error": message},
            },
        ],
    }
