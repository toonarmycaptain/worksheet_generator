"""The arithmetic worksheet endpoint passes its options through to the core and the renderer.

The questions are random, so ``test_the_response`` scripts ``random.randint`` (the operands),
and makes ``random.sample`` take the top of the allowed range of wrong answers, which shows the
operation's and ``max_number``'s limits in the PDF. The whole response, headers and what the
PDF draws as text, must then equal what the renderer makes for those same questions. What the
renderer draws is tested in ``test_arithmetic_worksheet_pdf``.
"""

import random

import pytest
from django.test import Client

from core.arithmetic import ArithmeticQuestionData, Operation
from tests.pdf_text import pdf_text
from tests.test_arithmetic_worksheet_pdf import build, render


@pytest.mark.parametrize(
    ("url", "drawn", "cases", "title", "label", "answer_key", "filename"),
    [
        (
            "/api/worksheets/arithmetic.pdf?operation=add&problems=2",
            [3, 4, 5, 6],
            [
                (ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (18, 19, 20)),
                (ArithmeticQuestionData(Operation.ADD, (5, 6), 11), (18, 19, 20)),
            ],
            "Arithmetic",
            "Sheet A",
            False,
            "arithmetic-sheet-a.pdf",
        ),
        (
            "/api/worksheets/arithmetic.pdf?operation=subtract&problems=2&answer_key=true",
            [7, 3, 9, 2],
            [
                (ArithmeticQuestionData(Operation.SUBTRACT, (7, 3), 4), (8, 9, 10)),
                (ArithmeticQuestionData(Operation.SUBTRACT, (9, 2), 7), (8, 9, 10)),
            ],
            "Arithmetic",
            "Sheet A",
            True,
            "arithmetic-sheet-a.pdf",
        ),
        (
            "/api/worksheets/arithmetic.pdf?operation=multiply&problems=2&title=Tables&label=Day+2",
            [6, 7, 2, 8],
            [
                (ArithmeticQuestionData(Operation.MULTIPLY, (6, 7), 42), (98, 99, 100)),
                (ArithmeticQuestionData(Operation.MULTIPLY, (2, 8), 16), (98, 99, 100)),
            ],
            "Tables",
            "Day 2",
            False,
            "arithmetic-day-2.pdf",
        ),
        (
            # max_number=5 lowers the top of the wrong answers from 20 to 10
            "/api/worksheets/arithmetic.pdf?problems=1&max_number=5",
            [3, 4],
            [(ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (8, 9, 10))],
            "Arithmetic",
            "Sheet A",
            False,
            "arithmetic-sheet-a.pdf",
        ),
        (
            "/api/worksheets/arithmetic.pdf?problems=1&label=",
            [3, 4],
            [(ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (18, 19, 20))],
            "Arithmetic",
            "",
            False,
            "arithmetic.pdf",
        ),
        (
            # 3 problems is all the different pairs that 0 and 1 make, and the top of the wrong
            # answers is raised to 3, the number of wrong answers
            "/api/worksheets/arithmetic.pdf?problems=3&max_number=1",
            [0, 0, 0, 1, 1, 1],
            [
                (ArithmeticQuestionData(Operation.ADD, (0, 0), 0), (1, 2, 3)),
                (ArithmeticQuestionData(Operation.ADD, (0, 1), 1), (0, 2, 3)),
                (ArithmeticQuestionData(Operation.ADD, (1, 1), 2), (0, 1, 3)),
            ],
            "Arithmetic",
            "Sheet A",
            False,
            "arithmetic-sheet-a.pdf",
        ),
    ],
)
def test_the_response(
    url: str,
    drawn: list[int],
    cases: list[tuple[ArithmeticQuestionData, tuple[int, ...]]],
    title: str,
    label: str,
    answer_key: bool,
    filename: str,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The response is the same as the renderer's output for the questions the core drew.

    ``randint`` gives the operands and ``sample`` takes the top of the wrong answers, so the
    PDF also shows the operation's and ``max_number``'s limits. The whole response is compared,
    status, content type, filename, cache header and drawn text, so a URL option that is dropped,
    ignored or sent to the wrong place makes it differ. The cache header is ``no-store``: there
    is no seed, so the same URL must make a new sheet, and Cloudflare caches ``.pdf`` URLs unless
    told not to.
    """
    values = iter(drawn)
    monkeypatch.setattr(random, "randint", lambda low, high: next(values))
    monkeypatch.setattr(random, "sample", lambda population, k: list(population[-k:]))
    monkeypatch.setattr(random, "shuffle", lambda items: items.reverse())

    response = client.get(url)

    assert (
        response.status_code,
        response["Content-Type"],
        response["Content-Disposition"],
        response["Cache-Control"],
        pdf_text(response.content),
    ) == (
        200,
        "application/pdf",
        f'inline; filename="{filename}"',
        "no-store",
        pdf_text(render(build(cases), answer_key, title, label)),
    )


@pytest.mark.parametrize(
    "url",
    [
        "/api/worksheets/arithmetic.pdf?operation=divide",
        "/api/worksheets/arithmetic.pdf?problems=0",
        "/api/worksheets/arithmetic.pdf?problems=21",
        "/api/worksheets/arithmetic.pdf?max_number=0",
        "/api/worksheets/arithmetic.pdf?max_number=25",
        "/api/worksheets/arithmetic.pdf?title=",
        "/api/worksheets/arithmetic.pdf?problems=7&max_number=2",  # 6 different pairs
    ],
)
def test_bad_options_are_rejected(url: str, client: Client) -> None:
    """Values the options do not allow get a 422 and no PDF.

    That is an operation that is not built yet (``divide``), a problem count or largest number
    outside its limits, an empty title, and more problems than there are different pairs.
    """
    assert client.get(url).status_code == 422
