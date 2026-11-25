"""
Tests for the naming fractions PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the
test case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_naming_fractions_worksheet``.

The PDF tests use the names in ``tests.data``, standing in for the bank, and replace these
functions, as ``test_generator`` in ``test_core/test_naming_fractions`` describes:

- ``random.choice`` returns the last item: the largest denominator, then the last answer over it
  that isn't a whole, the last way a story can have it, representation, story, object, noun and
  style, and the last place for side-by-side shading to start.
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
from core.fraction_models.area_models import AreaModel, Strip, equal_sizes
from core.fraction_models.object_groups import ObjectGroup
from core.naming_fractions.data import (
    Asked,
    NameQuestionData,
    People,
    ShadeQuestionData,
    ShareQuestionData,
)
from core.question import FreeResponse, MultipleChoice, Question
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.data import NAMES, REAL_CASE_SLOTS
from tests.helpers import (
    choose_last,
    conventional_slot_of_returns,
    pdf_text,
    random_always_returns,
    refused,
    render_naming_fractions,
    reverse_shuffle,
    sample_first,
)

STACKED, SLASH, SLANTED = FractionStyle
BANNER = 1  # a whole story


@pytest.mark.parametrize(
    ("url", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults, with 1 problem: it takes the first ticked type, naming, with the
            # largest default denominator, a group (the last representation) and the last style
            "/api/worksheets/naming_fractions.pdf?problems=1&sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(
                        NameQuestionData(
                            ObjectGroup(DrawnObject.XYLOPHONE, 8, 4, frozenset(range(1, 8))),
                            False,
                            UnreducedFraction(7, 8, SLANTED),
                        ),
                        FreeResponse(),
                    )
                ],
                "slot_of": None,
                "answer_key": False,
                "black_and_white": False,
                "title": "Naming Fractions",
                "label": "Sheet A",
                "name_line": False,
            },
            "naming_fractions-sheet-a.pdf",
        ),
        (
            # every option for multiple choice: strips alone tell the banner story, cut in 4
            "/api/worksheets/naming_fractions.pdf?question_types=share&representations=strip"
            "&denominators=2-4&fraction_styles=slash&multiple_choice=true"
            "&problems=1&answer_key=true&name_line=true&title=Fractions&label=Week+3&sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(
                        ShareQuestionData(
                            BANNER,
                            People(4, ("student", "students")),
                            None,
                            4,
                            Asked.LEFT,
                            1,
                            AreaModel(Strip(equal_sizes(4))),
                            UnreducedFraction(3, 4, SLASH),
                        ),
                        MultipleChoice(
                            (
                                UnreducedFraction(2, 4, SLASH),
                                UnreducedFraction(3, 1, SLASH),
                                UnreducedFraction(1, 4, SLASH),
                                UnreducedFraction(3, 4, SLASH),
                            ),
                            frozenset({3}),
                        ),
                    )
                ],
                "slot_of": None,
                "answer_key": True,
                "black_and_white": False,
                "title": "Fractions",
                "label": "Week 3",
                "name_line": True,
            },
            "naming_fractions-week-3.pdf",
        ),
        (
            # tiles: a picture of 2/2, whose value no written answer has, and the simple
            # pattern's slots; shaded grey, for black and white
            "/api/worksheets/naming_fractions.pdf?question_types=name&question_types=shade"
            "&denominators=2&self_check_tiles=true&problems=2&black_and_white=true&sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(
                        ShadeQuestionData(
                            UnreducedFraction(2, 2, SLANTED),
                            ObjectGroup(DrawnObject.XYLOPHONE, 2, 2),
                            False,
                            ObjectGroup(DrawnObject.XYLOPHONE, 2, 2, frozenset({0, 1})),
                        ),
                        FreeResponse(),
                    ),
                    Question(
                        NameQuestionData(
                            ObjectGroup(DrawnObject.XYLOPHONE, 2, 2, frozenset({1})),
                            False,
                            UnreducedFraction(1, 2, SLANTED),
                        ),
                        FreeResponse(),
                    ),
                ],
                "slot_of": REAL_CASE_SLOTS[:2],
                "answer_key": False,
                "black_and_white": True,
                "title": "Naming Fractions",
                "label": "Sheet A",
                "name_line": False,
            },
            "naming_fractions-sheet-a.pdf",
        ),
        (
            "/api/worksheets/naming_fractions.pdf?denominators=2-",
            422,
            refused('denominators: "2-" isn\'t a number or a range such as 2-12'),
            None,
            None,
        ),
        (
            "/api/worksheets/naming_fractions.pdf?denominators=1%2C000",
            422,
            refused('denominators: "1,000": write numbers without commas, such as 1000'),
            None,
            None,
        ),
        (
            "/api/worksheets/naming_fractions.pdf?question_types=name&representations=grid"
            "&denominators=5,7",
            422,
            refused(
                "question_types: Name the fraction needs a ticked representation that can show "
                "one of the denominators. Change the denominators or representations, or untick "
                "Name the fraction."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/naming_fractions.pdf?question_types=share&denominators=11",
            422,
            refused(
                "question_types: Share equally needs a denominator with a factor from 2 to 8, and "
                "Groups of objects or a representation that can show it. Change the denominators "
                "or representations, or untick Share equally."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/naming_fractions.pdf?question_types=draw_shares&representations=group",
            422,
            refused(
                "question_types: Draw the shares needs a denominator from 2 to 8, and Strips, "
                "Grids, Circles or Other shapes ticked: a group of objects isn't cut. Change "
                "them, or untick Draw the shares."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/naming_fractions.pdf?self_check_tiles=true&multiple_choice=true",
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            "/api/worksheets/naming_fractions.pdf?self_check_tiles=true&problems=13",
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        (
            # halves and fourths have 6 answers as written, a picture of 1 counting once
            "/api/worksheets/naming_fractions.pdf?self_check_tiles=true&problems=12"
            "&denominators=2,4",
            422,
            refused(
                "problems: at most 6 without repeated answers for that choice of question types, "
                "representations and denominators. Lower problems to 6."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/naming_fractions.pdf?fraction_styles=bold",
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        # the list's first entry
                        "loc": ["query", "options", "fraction_styles", 0],
                        "msg": "Input should be 'stacked', 'slash' or 'slanted'",
                        "ctx": {"expected": "'stacked', 'slash' or 'slanted'"},
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_naming_fractions_pdf(
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
    monkeypatch.setattr("core.naming_fractions.generator.NAMES", NAMES)
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
            render_naming_fractions(
                questions=pdf_data["questions"],
                slot_of=pdf_data["slot_of"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
                black_and_white=pdf_data["black_and_white"],
            )
        )
