"""
Helpers shared by the tests, so no test module imports from another.

- ``randint_returns`` and the other fakes: ``random`` made predictable, one function at a time
- the ``render_*`` functions: questions built by hand, and each worksheet rendered from them to
  PDF bytes
- ``pdf_text``: a PDF's drawing commands as readable text, so a test can compare and diff
  what the pages draw
- ``GOLDENS``, ``read_sections`` and ``write_section``: the golden files of expected text, a
  section per case
- ``refused``: Ninja's JSON error for an option the endpoint does not allow
"""

import base64
import random
import re
import zlib
from collections.abc import Callable, Sequence
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from core.base_ten_blocks import BlocksQuestionData
from core.basic_operations.data import BasicOperationQuestionData, MissingNumberQuestionData
from core.basic_operations.representation import Representation
from core.placevalue.data import PlaceValueQuestionData
from core.question import FreeResponse, Question, QuestionData, multiple_choice
from core.self_check_tiles import TileQuestion
from render.pdf.base_ten_blocks_worksheet import render_base_ten_blocks_worksheet
from render.pdf.basic_operations_worksheet import (
    render_basic_operations_worksheet,
    render_missing_number_worksheet,
)
from render.pdf.page import Header
from render.pdf.place_value_worksheet import render_place_value_worksheet
from render.pdf.self_check_tiles_worksheet import render_self_check_tiles_worksheet
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


def read_sections(path: Path) -> dict[str, str]:
    """The expected text of each case, by case name. Empty if the file does not exist yet."""
    if not path.exists():
        return {}
    text = path.read_text()
    names = SECTION.findall(text)
    bodies = SECTION.split(text)[2::2]  # split() alternates: before, name, body, name, body...
    return {name: body.strip("\n") for name, body in zip(names, bodies, strict=True)}


def write_section(path: Path, name: str, text: str) -> None:
    """Write ``text`` as the section ``name`` of a golden file, keeping the other sections."""
    sections = read_sections(path) | {name: text}
    path.write_text("".join(f"=== {case} ===\n{body}\n\n" for case, body in sections.items()))


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
    questions: list[BasicOperationQuestionData],
    representation: Representation,
    hints: bool,
    black_and_white: bool,
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
    name_line: bool = True,
) -> bytes:
    """Render the word problems sheet, each question free response, with no wrong answers."""
    out = BytesIO()
    render_word_problems_worksheet(
        questions=[Question(data, FreeResponse()) for data in questions],
        path=out,
        header=Header(title=title, label=label, name_line=name_line),
        answer_key=answer_key,
        representation=representation,
        hints=hints,
        slot_of=slot_of,
        black_and_white=black_and_white,
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
