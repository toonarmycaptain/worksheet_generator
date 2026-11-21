"""
Tests for the prime and composite PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the
test case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_prime_composite_worksheet``.

The PDF tests use the names in ``tests.data``, standing in for the bank, and replace these
functions:

- ``random.choice``, ``random.sample`` and ``random.randint`` return the picks, samples and
  numbers listed in the case, as ``test_generator`` in ``test_core/test_prime_composite``
  describes, and raise ``ValueError`` for one not among its call's items.
- ``random.shuffle`` reverses the list, so the question types are dealt from the last ticked,
  and a multiple-choice question's correct option is last.
- ``conventional_slot_of``, which gives the slots of the simple tile pattern, returns the slots
  of a real case.
"""

from typing import Any

import pytest
from django.test import Client

from core.prime_composite.data import (
    CountQuestionData,
    EachNumberQuestionData,
    FactorPairQuestionData,
)
from core.prime_composite.factors import Primality
from core.question import FreeResponse, MultipleChoice, Question
from tests.data import NAMES, REAL_CASE_SLOTS
from tests.helpers import (
    choice_returns,
    conventional_slot_of_returns,
    pdf_text,
    randint_returns,
    refused,
    render_prime_composite,
    reverse_shuffle,
    sample_returns,
)

PRIME, COMPOSITE, NEITHER = Primality


@pytest.mark.parametrize(
    ("url", "chosen", "sampled", "drawn", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults, with 1 problem: it takes the first ticked type, factor pairs, written,
            # with a largest number of 100
            "/api/worksheets/prime_composite.pdf?problems=1&sheet=1ab2c3",
            [1, 132, (6, 22), True, "Ana"],
            [[(11, 12)], [(3, 44)]],
            [],
            200,
            None,
            {
                "questions": [
                    Question(
                        FactorPairQuestionData(
                            132, ((4, 33), (6, 22)), "Ana", ((3, 44), (2, 66), (11, 12), (6, 22))
                        ),
                        FreeResponse(),
                    )
                ],
                "slot_of": None,
                "answer_key": False,
                "title": "Prime and Composite Numbers",
                "label": "Sheet A",
                "name_line": False,
            },
            "prime_composite-sheet-a.pdf",
        ),
        (
            # every option for multiple choice: the largest number caps the list's first number
            "/api/worksheets/prime_composite.pdf?question_types=count&largest_number=60"
            "&multiple_choice=true&problems=1&answer_key=true&name_line=true&title=Primes"
            "&label=Week+3&sheet=1ab2c3",
            [COMPOSITE, 1],
            [],
            [51],
            200,
            None,
            {
                "questions": [
                    Question(
                        CountQuestionData((51, 52, 53, 54, 55), COMPOSITE, 4),
                        MultipleChoice((3, 2, 1, 4), frozenset({3})),
                    )
                ],
                "slot_of": None,
                "answer_key": True,
                "title": "Primes",
                "label": "Week 3",
                "name_line": True,
            },
            "prime_composite-week-3.pdf",
        ),
        (
            # tiles: counting forms with different answers, and the simple pattern's slots
            "/api/worksheets/prime_composite.pdf?question_types=count&question_types=each_number"
            "&largest_number=20&self_check_tiles=true&problems=2&sheet=1ab2c3",
            [
                "PPCPPP",
                (PRIME, PRIME, COMPOSITE, PRIME, PRIME, PRIME),
                "4",
                CountQuestionData((8, 9, 10, 11, 12), COMPOSITE, 4),
            ],
            [[3, 5, 7, 11, 13], [9]],
            [],
            200,
            None,
            {
                "questions": [
                    Question(
                        EachNumberQuestionData(
                            (3, 5, 9, 7, 11, 13), (PRIME, PRIME, COMPOSITE, PRIME, PRIME, PRIME)
                        ),
                        FreeResponse(),
                    ),
                    Question(CountQuestionData((8, 9, 10, 11, 12), COMPOSITE, 4), FreeResponse()),
                ],
                "slot_of": REAL_CASE_SLOTS[:2],
                "answer_key": False,
                "title": "Prime and Composite Numbers",
                "label": "Sheet A",
                "name_line": False,
            },
            "prime_composite-sheet-a.pdf",
        ),
        (
            "/api/worksheets/prime_composite.pdf?self_check_tiles=true&multiple_choice=true",
            [],
            [],
            [],
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            # every type is ticked by default; those whose answer is printed in them have no
            # tiles form, so the page greys them out
            "/api/worksheets/prime_composite.pdf?self_check_tiles=true",
            [],
            [],
            [],
            422,
            refused(
                "question_types: Choose the two primes or composites, Whose number is prime or "
                "composite, Who is correct? and List the factors, then decide can't be asked with "
                "self-check tiles"
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/prime_composite.pdf?question_types=count&self_check_tiles=true"
            "&problems=13",
            [],
            [],
            [],
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        (
            # counts of 5 to 10 numbers up to 20 are 1 to 7
            "/api/worksheets/prime_composite.pdf?question_types=count&largest_number=20"
            "&self_check_tiles=true&problems=8",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 7 without repeated answers for that choice of question types "
                "and largest number. Lower problems to 7, or raise the largest number to 27."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/prime_composite.pdf?largest_number=19",
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "largest_number"],
                        "msg": "Input should be greater than or equal to 20",
                        "ctx": {"ge": 20},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/prime_composite.pdf?question_types=all",
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        # the list's first entry
                        "loc": ["query", "options", "question_types", 0],
                        "msg": "Input should be 'factor_pairs', 'count', 'choose_two', 'between', "
                        "'whose_number', 'who_is_correct', 'each_number' or 'list_factors'",
                        "ctx": {
                            "expected": "'factor_pairs', 'count', 'choose_two', 'between', "
                            "'whose_number', 'who_is_correct', 'each_number' or 'list_factors'"
                        },
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_prime_composite_pdf(
    url: str,
    chosen: list[Any],
    sampled: list[list[Any]],
    drawn: list[int],
    status: int,
    expected_json: dict[str, Any] | None,
    pdf_data: dict[str, Any] | None,
    filename: str | None,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A request receives the PDF for its options, or the error identifying the invalid option.

    - A rejected request is compared with Ninja's JSON error, and has no PDF headers.
    - A PDF is compared on its filename, its cache header and the text the renderer draws for
      ``pdf_data``.
    """
    monkeypatch.setattr("core.prime_composite.generator.NAMES", NAMES)
    choice_returns(monkeypatch, chosen)
    sample_returns(monkeypatch, sampled)
    randint_returns(monkeypatch, drawn)
    reverse_shuffle(monkeypatch)
    conventional_slot_of_returns(monkeypatch, REAL_CASE_SLOTS)

    response = client.get(url)

    assert response.status_code == status
    assert response.get("Content-Disposition") == (
        f'inline; filename="{filename}"' if not expected_json else None
    )
    assert response.get("Cache-Control") == ("public, max-age=86400" if not expected_json else None)
    if expected_json:
        assert response.json() == expected_json
    else:
        assert pdf_text(response.content) == pdf_text(
            render_prime_composite(
                questions=pdf_data["questions"],
                slot_of=pdf_data["slot_of"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
            )
        )
