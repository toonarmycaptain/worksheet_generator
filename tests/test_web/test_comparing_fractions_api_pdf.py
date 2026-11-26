"""
Tests for the comparing fractions PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the
test case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_comparing_fractions_worksheet``.

The PDF tests use the names in ``tests.data``, standing in for the bank, and replace these
functions, as ``test_generator`` in ``test_core/test_comparing_fractions`` describes:

- ``random.choice`` returns the last item: the shared denominator, the last representation that
  fits, the largest denominator and its last set, the pizza story and the last style.
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

from core.comparing_fractions.data import (
    CompareQuestionData,
    GreatestQuestionData,
    LessGreaterForm,
    LessGreaterQuestionData,
    StoryKind,
    WordAsked,
    WordQuestionData,
)
from core.comparing_fractions.stories import WHOLE_STORIES
from core.fraction_models.area_models import AreaModel, Strip, equal_sizes
from core.question import FreeResponse, MultipleChoice, Question
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.data import NAMES, REAL_CASE_SLOTS
from tests.helpers import (
    choose_last,
    conventional_slot_of_returns,
    pdf_text,
    random_always_returns,
    refused,
    render_comparing_fractions,
    reverse_shuffle,
    sample_first,
)

STACKED, SLASH, SLANTED = FractionStyle
PIZZA = len(WHOLE_STORIES) - 1  # the last story


def _f(numerator: int, denominator: int, style: FractionStyle) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator, style)


def _strip(parts: int, shaded: int) -> AreaModel:
    """Return a strip of ``parts`` equal parts, the first ``shaded`` of them shaded."""
    return AreaModel(Strip(equal_sizes(parts)), frozenset(range(shaded)))


def _pizza(names: tuple[str, str], pair: tuple[int, int], answer: str) -> WordQuestionData:
    """Return a story of two pizzas in sixths asking who eats less, unpictured."""
    return WordQuestionData(
        StoryKind.WHOLE,
        PIZZA,
        names,
        (_f(pair[0], 6, SLANTED), _f(pair[1], 6, SLANTED)),
        None,
        None,
        False,
        False,
        WordAsked.WHO,
        None,
        (),
        answer,
    )


@pytest.mark.parametrize(
    ("url", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults, with 1 problem: it takes the first ticked type, compare, with no
            # picture, the last representation, and eighths, in the last style
            "/api/worksheets/comparing_fractions.pdf?problems=1&sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(
                        CompareQuestionData(
                            (_f(8, 8, SLANTED), _f(7, 8, SLANTED)), (), None, False, ">"
                        ),
                        FreeResponse(),
                    )
                ],
                "slot_of": None,
                "answer_key": False,
                "black_and_white": False,
                "title": "Comparing Fractions",
                "label": "Sheet A",
                "name_line": False,
            },
            "comparing_fractions-sheet-a.pdf",
        ),
        (
            # every option for multiple choice: "Which is NOT a way to show a fraction less than
            # 7/8?" on strips, sharing its numerator, 7 of 7 the one that isn't, in grey; with
            # only 7/8 and 7/7 not less, "Which model shows?" can't be asked
            "/api/worksheets/comparing_fractions.pdf?question_types=less_greater"
            "&representations=strip&shared=numerator&denominators=4,8&fraction_styles=slash"
            "&multiple_choice=true&problems=1&answer_key=true&black_and_white=true"
            "&name_line=true&title=Compare&label=Week+3&sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(
                        LessGreaterQuestionData(
                            _f(7, 8, SLASH),
                            False,
                            LessGreaterForm.NOT_A_WAY,
                            _strip(8, 7),
                            _strip(1, 0),
                            (),
                            (_f(7, 7, SLASH),),
                        ),
                        MultipleChoice(
                            (_strip(10, 7), _strip(9, 7), _strip(12, 7), _strip(7, 7)),
                            frozenset({3}),
                        ),
                    )
                ],
                "slot_of": None,
                "answer_key": True,
                "black_and_white": True,
                "title": "Compare",
                "label": "Week 3",
                "name_line": True,
            },
            "comparing_fractions-week-3.pdf",
        ),
        (
            # tiles: a pair of fourths, one answered by each, and a pair of names; the simple
            # pattern's slots
            "/api/worksheets/comparing_fractions.pdf?question_types=compare&question_types=word"
            "&representations=none&shared=denominator&denominators=4,6&self_check_tiles=true"
            "&problems=4&sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(_pizza(("Ben", "Ana"), (4, 6), "Ben"), FreeResponse()),
                    Question(_pizza(("Ana", "Ben"), (5, 6), "Ana"), FreeResponse()),
                    Question(
                        GreatestQuestionData(
                            (_f(3, 4, SLANTED), _f(4, 4, SLANTED)),
                            False,
                            (),
                            None,
                            _f(3, 4, SLANTED),
                        ),
                        FreeResponse(),
                    ),
                    Question(
                        GreatestQuestionData(
                            (_f(3, 4, SLANTED), _f(4, 4, SLANTED)),
                            True,
                            (),
                            None,
                            _f(4, 4, SLANTED),
                        ),
                        FreeResponse(),
                    ),
                ],
                "slot_of": REAL_CASE_SLOTS[:4],
                "answer_key": False,
                "black_and_white": False,
                "title": "Comparing Fractions",
                "label": "Sheet A",
                "name_line": False,
            },
            "comparing_fractions-sheet-a.pdf",
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?denominators=2-",
            422,
            refused('denominators: "2-" isn\'t a number or a range such as 2-12'),
            None,
            None,
        ),
        (
            # a wall shows different denominators only
            "/api/worksheets/comparing_fractions.pdf?question_types=compare&representations=wall"
            "&shared=denominator",
            422,
            refused(
                "question_types: Compare needs a ticked representation that can show two "
                "fractions sharing a ticked numerator or denominator. Change the representations, "
                "denominators or Fractions compared, or untick Compare."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=word&representations=wall",
            422,
            refused(
                "question_types: Word problems needs a story the ticked representations can draw: "
                "tick No picture, or a representation that can show the denominators, or untick "
                "Word problems."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=less_greater"
            "&representations=none&representations=group",
            422,
            refused(
                "question_types: Less or greater than a model needs Strips, Grids, Circles or "
                "Other shapes ticked, with a denominator they can show. Change the representations "
                "or denominators, or untick Less or greater than a model."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=draw&denominators=13-20",
            422,
            refused(
                "question_types: Draw and compare needs Strips, Grids, Circles, Other shapes or "
                "Number lines ticked, with a denominator from 2 to 12. Change them, or untick "
                "Draw and compare."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=greatest&shared=numerator"
            "&denominators=2,3",
            422,
            refused(
                "question_types: Greatest and least needs a ticked representation that can show "
                "three fractions sharing a ticked numerator or denominator. Change the "
                "representations, denominators or Fractions compared, or untick Greatest and "
                "least."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=compare"
            "&question_types=greatest&shared=numerator&denominators=2,3&self_check_tiles=true"
            "&problems=4",
            422,
            refused(
                "question_types: Greatest and least on a tiles sheet with Compare needs three "
                "fractions that share a numerator or a denominator, which a ticked representation "
                "can show. Change the representations, denominators or Fractions compared, or "
                "untick Greatest and least."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=greatest&shared=numerator"
            "&denominators=2,3,4&self_check_tiles=true&problems=4",
            422,
            refused(
                "question_types: Greatest and least on a tiles sheet needs four fractions that "
                "share a numerator or a denominator, which a ticked representation can show. "
                "Change the representations, denominators or Fractions compared, or untick "
                "Greatest and least."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=explain&question_types=draw"
            "&self_check_tiles=true",
            422,
            refused(
                "question_types: Compare and explain and Draw and compare have no single answer "
                "for a tile. Tick another question type, or untick Self-check tile answers."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=explain&self_check_tiles=true",
            422,
            refused(
                "question_types: Compare and explain has no single answer for a tile. Tick "
                "another question type, or untick Self-check tile answers."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?self_check_tiles=true&multiple_choice=true",
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?self_check_tiles=true&problems=13",
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        (
            # halves and thirds sharing a numerator: 1/3 and 1/2, 2/3 and 2/2
            "/api/worksheets/comparing_fractions.pdf?question_types=compare&shared=numerator"
            "&denominators=2,3&self_check_tiles=true&problems=5",
            422,
            refused(
                "problems: at most 4 without repeated answers for that choice of question types, "
                "representations and denominators. Lower problems to 4."
            ),
            None,
            None,
        ),
        (
            # those two pairs can't make three
            "/api/worksheets/comparing_fractions.pdf?question_types=compare&shared=numerator"
            "&denominators=2,3&self_check_tiles=true&problems=3",
            422,
            refused(
                "problems: On a tiles sheet, the fractions come in groups that share a numerator "
                "or a denominator, and this many problems can't be split into them. Change "
                "problems, Denominators or Representations, or tick Word problems."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=greatest&self_check_tiles=true"
            "&problems=3",
            422,
            refused(
                "problems: Greatest and least on a tiles sheet needs at least 4 problems, since "
                "its fractions come in groups of four or more. Raise problems, or tick another "
                "question type."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=word&self_check_tiles=true"
            "&problems=1",
            422,
            refused(
                "problems: Word problems on a tiles sheet needs at least 2 problems, since its "
                "names come in pairs. Raise problems to 2, or tick another question type."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/comparing_fractions.pdf?question_types=shade",
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        # the list's first entry
                        "loc": ["query", "options", "question_types", 0],
                        "msg": "Input should be 'compare', 'explain', 'word', 'less_greater', "
                        "'draw' or 'greatest'",
                        "ctx": {
                            "expected": "'compare', 'explain', 'word', 'less_greater', 'draw' or "
                            "'greatest'"
                        },
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_comparing_fractions_pdf(
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
    monkeypatch.setattr("core.comparing_fractions.generator.NAMES", NAMES)
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
            render_comparing_fractions(
                questions=pdf_data["questions"],
                slot_of=pdf_data["slot_of"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
                black_and_white=pdf_data["black_and_white"],
            )
        )
