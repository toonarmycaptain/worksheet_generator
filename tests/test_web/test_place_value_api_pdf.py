"""
Tests for the place-value worksheet endpoint: its options reach the core and the renderers intact.

The tests script the first call to ``random.sample``, which draws all of a sheet's numbers at
once, and make later calls take the top of the range for wrong answers, so the PDF shows the
range's limits. ``random.choice`` takes the last form offered, so a mixed form reveals which
forms it was chosen from. The PDF must then match what the renderer draws for the same
questions. Disallowed options get Ninja's JSON error. The renderers' output is tested in
``test_place_value_worksheet`` and ``test_self_check_tiles_worksheet``.
"""

import random
from collections.abc import Sequence
from typing import Any, get_args

import pytest
from django.test import Client
from worksheets.registry import FormChoice

from core.placevalue.data import PlaceValueForm, PlaceValueQuestionData
from core.placevalue.representation import place_value_tile_question
from tests.data import EXPANDED, EXPANDED_NOTATION, REAL_CASE_SLOTS, STANDARD, WORD
from tests.helpers import (
    choose_last,
    conventional_slot_of_returns,
    pdf_text,
    refused,
    render_place_value,
    render_tiles,
    reverse_shuffle,
)


def sample_returns_then_last(monkeypatch: pytest.MonkeyPatch, drawn: list[int]) -> None:
    """
    Make the first ``random.sample`` call return ``drawn``, and later calls the last ``k`` items.

    The first call draws all of a sheet's numbers. The later ones draw wrong answers, which then
    come from the top of the range.
    """
    numbers = [drawn]

    def sample(population: Sequence[int], k: int) -> list[int]:
        if numbers:
            return numbers.pop()
        return list(population[len(population) - k :])

    monkeypatch.setattr(random, "sample", sample)


@pytest.mark.parametrize(
    ("url", "drawn", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults: standard to expanded, written
            "/api/worksheets/place_value.pdf?problems=2&sheet=1ab2c3",
            [35043, 50421],
            200,
            None,
            {
                "cases": [
                    (PlaceValueQuestionData(35043, STANDARD, EXPANDED), ()),
                    (PlaceValueQuestionData(50421, STANDARD, EXPANDED), ()),
                ],
                "title": "Place Value",
                "label": "Sheet A",
                "answer_key": False,
            },
            "place_value-sheet-a.pdf",
        ),
        (
            "/api/worksheets/place_value.pdf?given=word&asked=standard&problems=1&answer_key=true"
            "&title=Number+Forms&label=Day+2&sheet=1ab2c3",
            [54321],
            200,
            None,
            {
                "cases": [(PlaceValueQuestionData(54321, WORD, STANDARD), ())],
                "title": "Number Forms",
                "label": "Day 2",
                "answer_key": True,
            },
            "place_value-day-2.pdf",
        ),
        (
            # both mixed: the last of all five, then the last of the other four
            "/api/worksheets/place_value.pdf?given=mixed&asked=mixed&problems=1&sheet=1ab2c3",
            [35043],
            200,
            None,
            {
                "cases": [(PlaceValueQuestionData(35043, WORD, EXPANDED_NOTATION), ())],
                "title": "Place Value",
                "label": "Sheet A",
                "answer_key": False,
            },
            "place_value-sheet-a.pdf",
        ),
        (
            # mixed from: the last form other than word
            "/api/worksheets/place_value.pdf?given=mixed&asked=word&problems=1&sheet=1ab2c3",
            [35043],
            200,
            None,
            {
                "cases": [(PlaceValueQuestionData(35043, EXPANDED_NOTATION, WORD), ())],
                "title": "Place Value",
                "label": "Sheet A",
                "answer_key": False,
            },
            "place_value-sheet-a.pdf",
        ),
        (
            # multiple choice: three wrong answers from the top of the range
            "/api/worksheets/place_value.pdf?multiple_choice=true&problems=1&answer_key=true"
            "&sheet=1ab2c3",
            [35043],
            200,
            None,
            {
                "cases": [
                    (PlaceValueQuestionData(35043, STANDARD, EXPANDED), (99997, 99998, 99999))
                ],
                "title": "Place Value",
                "label": "Sheet A",
                "answer_key": True,
            },
            "place_value-sheet-a.pdf",
        ),
        (
            # 1 to 4 is the smallest range with 3 wrong answers
            "/api/worksheets/place_value.pdf?multiple_choice=true&min_number=1&max_number=4"
            "&problems=1&sheet=1ab2c3",
            [1],
            200,
            None,
            {
                "cases": [(PlaceValueQuestionData(1, STANDARD, EXPANDED), (2, 3, 4))],
                "title": "Place Value",
                "label": "Sheet A",
                "answer_key": False,
            },
            "place_value-sheet-a.pdf",
        ),
        # Options that are not allowed are refused before anything is drawn, and before the
        # redirect, so these URLs have no token.
        (
            "/api/worksheets/place_value.pdf?given=unit&asked=unit",
            [],
            422,
            refused("asked: must be a different form from given"),
            None,
            None,
        ),
        (
            "/api/worksheets/place_value.pdf?min_number=500&max_number=499",
            [],
            422,
            refused("min_number: must not be more than the largest number"),
            None,
            None,
        ),
        (
            # 1 to 3 is only 3 different numbers
            "/api/worksheets/place_value.pdf?min_number=1&max_number=3&problems=4",
            [],
            422,
            refused(
                "problems: at most 3 without repeats for that range of numbers. Lower problems "
                "to 3, or raise the largest number to 4."
            ),
            None,
            None,
        ),
        (
            # 1 to 3 leaves only 2 wrong answers for a question
            "/api/worksheets/place_value.pdf?multiple_choice=true&min_number=1&max_number=3"
            "&problems=1",
            [],
            422,
            refused(
                "max_number: must be at least 3 more than the smallest number, for 3 wrong answers"
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/place_value.pdf?max_number=1000000",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "max_number"],
                        "msg": "Input should be less than or equal to 999999",
                        "ctx": {"le": 999999},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/place_value.pdf?given=roman",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "given"],
                        "msg": "Input should be 'standard', 'expanded', 'unit', "
                        "'expanded_notation', 'word' or 'mixed'",
                        "ctx": {
                            "expected": "'standard', 'expanded', 'unit', 'expanded_notation', "
                            "'word' or 'mixed'"
                        },
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_place_value_pdf(
    url: str,
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
    sample_returns_then_last(monkeypatch, drawn)
    choose_last(monkeypatch)
    reverse_shuffle(monkeypatch)

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
            render_place_value(
                cases=pdf_data["cases"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
            )
        )


@pytest.mark.parametrize(
    ("url", "drawn", "status", "expected_json", "questions", "slot_of", "answer_key"),
    [
        (
            # simple, the default: the conventional slots
            "/api/worksheets/place_value.pdf?self_check_tiles=true&given=expanded&asked=standard"
            "&problems=2&sheet=1ab2c3",
            [35043, 50421],
            200,
            None,
            [
                PlaceValueQuestionData(35043, EXPANDED, STANDARD),
                PlaceValueQuestionData(50421, EXPANDED, STANDARD),
            ],
            (7, 9),
            False,
        ),
        (
            # complex, with answers in word form
            "/api/worksheets/place_value.pdf?self_check_tiles=true&tile_pattern=complex"
            "&asked=word&problems=2&answer_key=true&sheet=1ab2c3",
            [35043, 50421],
            200,
            None,
            [
                PlaceValueQuestionData(35043, STANDARD, WORD),
                PlaceValueQuestionData(50421, STANDARD, WORD),
            ],
            (11, 10),
            True,
        ),
        (
            # tiles win over multiple choice, so a range too small for wrong answers is fine
            "/api/worksheets/place_value.pdf?self_check_tiles=true&multiple_choice=true"
            "&tile_pattern=complex&min_number=1&max_number=2&problems=2&sheet=1ab2c3",
            [1, 2],
            200,
            None,
            [
                PlaceValueQuestionData(1, STANDARD, EXPANDED),
                PlaceValueQuestionData(2, STANDARD, EXPANDED),
            ],
            (11, 10),
            False,
        ),
        (
            "/api/worksheets/place_value.pdf?self_check_tiles=true&problems=13",
            [],
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
            False,
        ),
    ],
)
def test_place_value_pdf_for_self_check_tiles(
    url: str,
    drawn: list[int],
    status: int,
    expected_json: dict[str, Any] | None,
    questions: list[PlaceValueQuestionData] | None,
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A tiles request receives the tiles PDF for its questions and slots, or its error.

    ``conventional_slot_of`` is replaced so the simple pattern's slots are known, and the
    complex pattern shuffles all twelve slots, which the scripted shuffle reverses.
    """
    sample_returns_then_last(monkeypatch, drawn)
    choose_last(monkeypatch)
    reverse_shuffle(monkeypatch)
    conventional_slot_of_returns(monkeypatch, REAL_CASE_SLOTS)

    response = client.get(url)

    assert response.status_code == status
    if expected_json:
        assert response.json() == expected_json
    else:
        assert pdf_text(response.content) == pdf_text(
            render_tiles(
                questions,
                place_value_tile_question,
                slot_of,
                answer_key,
                "Place Value",
                "Sheet A",
            )
        )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("/api/worksheets/place_value.pdf?problems=1&sheet=1ab2c3", range(1000, 100_000)),
        (
            "/api/worksheets/place_value.pdf?min_number=10&max_number=500&problems=1&sheet=1ab2c3",
            range(10, 501),
        ),
    ],
)
def test_the_numbers_come_from_the_range_asked_for(
    url: str, expected: range, client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The sheet's numbers are sampled from ``min_number`` to ``max_number``."""
    drawn_from: list[Sequence[int]] = []

    def sample(population: Sequence[int], k: int) -> list[int]:
        drawn_from.append(population)
        return list(population[:k])

    monkeypatch.setattr(random, "sample", sample)

    assert client.get(url).status_code == 200
    assert drawn_from[0] == expected


def test_the_form_choices_are_every_form_and_mixed() -> None:
    """
    ``FormChoice`` lists every ``PlaceValueForm`` in order, followed by mixed.

    It is written out by hand, so a form added to ``PlaceValueForm`` must be added to it too.
    """
    assert get_args(FormChoice) == (*(form.value for form in PlaceValueForm), "mixed")
