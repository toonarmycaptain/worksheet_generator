"""
Tests for the fractions on a number line PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the
test case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_fraction_number_lines_worksheet``.

The PDF tests use the names in ``tests.data``, standing in for the bank, and replace these
functions, as ``test_generator`` in ``test_core/test_fraction_number_lines`` describes:

- ``random.choice`` returns the last item: the largest denominator, then the last answer over it
  that isn't a whole, the last pair of distances, story, unit and style.
- ``random.shuffle`` reverses the list, so the question types are dealt from the last ticked,
  and a multiple-choice question's correct option is last.
- ``random.sample`` takes the first items, and ``random.random`` always returns 0.99, so no
  "one time in n" happens.
- ``conventional_slot_of``, which gives the slots of the simple tile pattern, returns the slots
  of a real case.
"""

from typing import Any

import pytest
from django.test import Client

from core.drawn_objects import DrawnObject
from core.fraction_models.number_lines import FractionLine, LengthUnit, LinePicture, LinePoint
from core.fraction_number_lines.data import (
    LESS,
    MORE,
    Compared,
    CompareQuestionData,
    Comparison,
    MarkPointQuestionData,
    NamePointQuestionData,
)
from core.fraction_number_lines.stories import DISTANCE_STORIES
from core.question import FreeResponse, MultipleChoice, Question
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.data import NAMES, REAL_CASE_SLOTS
from tests.helpers import (
    choose_last,
    conventional_slot_of_returns,
    pdf_text,
    random_always_returns,
    refused,
    render_fraction_number_lines,
    reverse_shuffle,
    sample_first,
)

STACKED, SLASH, SLANTED = FractionStyle
BIKE = len(DISTANCE_STORIES) - 1  # the last story: "rode a bike … from home"
THREE_QUARTERS, TWO_QUARTERS = UnreducedFraction(3, 4, SLASH), UnreducedFraction(2, 4, SLASH)


@pytest.mark.parametrize(
    ("url", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults, with 1 problem: it takes the first ticked type, naming the point,
            # with the largest default denominator and the last style
            "/api/worksheets/fraction_number_lines.pdf?problems=1&sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(
                        NamePointQuestionData(
                            FractionLine(8, points=(LinePoint(7),)),
                            UnreducedFraction(7, 8, SLANTED),
                        ),
                        FreeResponse(),
                    )
                ],
                "slot_of": None,
                "answer_key": False,
                "black_and_white": False,
                "title": "Fractions on a Number Line",
                "label": "Sheet A",
                "name_line": False,
            },
            "fraction_number_lines-sheet-a.pdf",
        ),
        (
            # every option for multiple choice: Ana and Ben's bike rides, "more or less"
            "/api/worksheets/fraction_number_lines.pdf?question_types=compare&denominators=4"
            "&fraction_styles=slash&multiple_choice=true&problems=1&answer_key=true"
            "&name_line=true&title=Number+Lines&label=Week+3&sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(
                        CompareQuestionData(
                            BIKE,
                            ("Ana", "Ben"),
                            LengthUnit.KILOMETER,
                            (THREE_QUARTERS, TWO_QUARTERS),
                            Compared.MORE_OR_LESS,
                            FractionLine(
                                4,
                                unit=LengthUnit.KILOMETER,
                                pictures=(LinePicture(0, DrawnObject.HOUSE),),
                            ),
                            MORE,
                        ),
                        MultipleChoice(
                            (
                                Comparison(LESS, THREE_QUARTERS, "<", TWO_QUARTERS),
                                Comparison(LESS, THREE_QUARTERS, ">", TWO_QUARTERS),
                                Comparison(MORE, THREE_QUARTERS, "<", TWO_QUARTERS),
                                Comparison(MORE, THREE_QUARTERS, ">", TWO_QUARTERS),
                            ),
                            frozenset({3}),
                        ),
                    )
                ],
                "slot_of": None,
                "answer_key": True,
                "black_and_white": False,
                "title": "Number Lines",
                "label": "Week 3",
                "name_line": True,
            },
            "fraction_number_lines-week-3.pdf",
        ),
        (
            # tiles: a line to find at 2/2, whose value no written answer has, and the simple
            # pattern's slots; marks grey, for black and white
            "/api/worksheets/fraction_number_lines.pdf?question_types=name&question_types=mark"
            "&denominators=2&self_check_tiles=true&problems=2&black_and_white=true&sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(
                        MarkPointQuestionData(
                            UnreducedFraction(2, 2, SLANTED),
                            FractionLine(2),
                            FractionLine(2, points=(LinePoint(2),)),
                        ),
                        FreeResponse(),
                    ),
                    Question(
                        NamePointQuestionData(
                            FractionLine(2, points=(LinePoint(1),)),
                            UnreducedFraction(1, 2, SLANTED),
                        ),
                        FreeResponse(),
                    ),
                ],
                "slot_of": REAL_CASE_SLOTS[:2],
                "answer_key": False,
                "black_and_white": True,
                "title": "Fractions on a Number Line",
                "label": "Sheet A",
                "name_line": False,
            },
            "fraction_number_lines-sheet-a.pdf",
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?denominators=2-",
            422,
            refused('denominators: "2-" isn\'t a number or a range such as 2-12'),
            None,
            None,
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?denominators=3,6",
            422,
            refused(
                "question_types: Distance stories needs halves, fourths or eighths: add 2, 4 or 8 "
                "to Denominators, or untick Distance stories."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?question_types=compare&denominators=2",
            422,
            refused(
                "question_types: Compare distances needs fourths or eighths, for two points on one "
                "line: add 4 or 8 to Denominators, or untick Compare distances."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?denominators=20",
            422,
            refused(
                "question_types: Name the point needs a denominator from 2 to 12, for its number "
                "line to fit a column: add one to Denominators, or untick Name the point."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?question_types=divide&denominators=13",
            422,
            refused(
                "question_types: Divide the line needs a denominator from 2 to 12: add one to "
                "Denominators, or untick Divide the line."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?question_types=mark&denominators=10"
            "&self_check_tiles=true",
            422,
            refused(
                "question_types: Mark the point needs a denominator from 2 to 8, for its number "
                "line to fit the answer bank: add one to Denominators, untick Self-check tile "
                "answers, or untick Mark the point."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?question_types=divide&self_check_tiles=true",
            422,
            refused(
                "question_types: Divide the line has no single answer for a tile. Tick another "
                "question type, or untick Self-check tile answers."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?question_types=compare&self_check_tiles=true"
            "&problems=1",
            422,
            refused(
                "problems: Compare distances on a tiles sheet needs at least 2 problems, since its "
                "names come in pairs. Raise problems to 2, or tick another question type."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?self_check_tiles=true&multiple_choice=true",
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?self_check_tiles=true&problems=13",
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        (
            # halves, fourths and eighths have 11 distances below 1
            "/api/worksheets/fraction_number_lines.pdf?question_types=distance"
            "&self_check_tiles=true&problems=12",
            422,
            refused(
                "problems: at most 11 without repeated answers for that choice of question types "
                "and denominators. Lower problems to 11."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/fraction_number_lines.pdf?question_types=shade",
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        # the list's first entry
                        "loc": ["query", "options", "question_types", 0],
                        "msg": "Input should be 'name', 'mark', 'distance', 'divide' or 'compare'",
                        "ctx": {"expected": "'name', 'mark', 'distance', 'divide' or 'compare'"},
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_fraction_number_lines_pdf(
    url: str,
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
    monkeypatch.setattr("core.fraction_number_lines.generator.NAMES", NAMES)
    choose_last(monkeypatch)
    reverse_shuffle(monkeypatch)
    sample_first(monkeypatch)
    random_always_returns(monkeypatch, 0.99)
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
            render_fraction_number_lines(
                questions=pdf_data["questions"],
                slot_of=pdf_data["slot_of"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
                black_and_white=pdf_data["black_and_white"],
            )
        )
