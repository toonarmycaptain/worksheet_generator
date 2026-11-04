"""
Tests for the place-value worksheet PDFs, rendered from hand-built questions.

The question generator is not used. Questions are built by hand, and ``reverse_shuffle``
fixes a multiple-choice question's option order by reversing the options, so the correct answer
is always last.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/place_value_worksheet_pdf_expecteds.txt``. The text includes every question's wording,
the number in its given form, the answer lines or options, the answer key and the page breaks.
To regenerate sections after an intended change, uncomment the ``write_section`` lines in
``test_pdf_draws_the_expected_text`` and run it (``-k`` selects cases).
"""

import pytest

from core.placevalue.data import PlaceValueQuestionData
from tests.data import EXPANDED, EXPANDED_NOTATION, STANDARD, UNIT, WORD
from tests.helpers import GOLDENS, pdf_text, read_sections, render_place_value, reverse_shuffle

# (question data, its wrong answers): none for a written question, which has an answer line

# Each form shown once, with the longest number the forms write among them.
EACH_FORM_SHOWN = [
    (PlaceValueQuestionData(35043, STANDARD, EXPANDED), ()),
    (PlaceValueQuestionData(54321, EXPANDED, STANDARD), ()),
    (PlaceValueQuestionData(50421, UNIT, WORD), ()),
    (PlaceValueQuestionData(999_999, EXPANDED_NOTATION, UNIT), ()),
    (PlaceValueQuestionData(40014, WORD, EXPANDED_NOTATION), ()),
]

# Each form asked for once, so the answer key writes each one.
EACH_FORM_ASKED = [
    (PlaceValueQuestionData(10000, WORD, STANDARD), ()),
    (PlaceValueQuestionData(50421, STANDARD, EXPANDED), ()),
    (PlaceValueQuestionData(11111, STANDARD, UNIT), ()),
    (PlaceValueQuestionData(999_999, STANDARD, EXPANDED_NOTATION), ()),
    (PlaceValueQuestionData(101_101, STANDARD, WORD), ()),
]

# The default 8 fill the first page, so the ninth starts a second.
NINE_QUESTIONS = [
    (PlaceValueQuestionData(number * 1111, STANDARD, EXPANDED), ()) for number in range(1, 10)
]

# Each form asked for once with three wrong answers, so the choices and the key's letters show
# every form. Four fill a page, so the fifth starts a second.
CHOICE_OF_EACH_FORM = [
    (PlaceValueQuestionData(10000, WORD, STANDARD), (20000, 30000, 40000)),
    (PlaceValueQuestionData(50421, STANDARD, EXPANDED), (50412, 54021, 5421)),
    (PlaceValueQuestionData(11111, STANDARD, UNIT), (11110, 10111, 1111)),
    (PlaceValueQuestionData(999_999, STANDARD, EXPANDED_NOTATION), (99999, 909_999, 999_990)),
    (PlaceValueQuestionData(101_101, STANDARD, WORD), (110_101, 101_011, 11101)),
]


EXPECTED = GOLDENS / "place_value_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "cases", "answer_key", "title", "label"),
    [
        ("each_form_shown", EACH_FORM_SHOWN, False, "Place Value", "Sheet A"),
        ("each_form_asked_answer_key", EACH_FORM_ASKED, True, "Place Value", "Sheet A"),
        ("nine_questions_answer_key", NINE_QUESTIONS, True, "Place Value", "Sheet A"),
        ("other_title_and_label", EACH_FORM_SHOWN, False, "Number Forms", "Day 2"),
        ("choice_of_each_form_answer_key", CHOICE_OF_EACH_FORM, True, "Place Value", "Sheet A"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    cases: list[tuple[PlaceValueQuestionData, tuple[int, ...]]],
    answer_key: bool,
    title: str,
    label: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The decoded PDF matches this case's section of ``place_value_worksheet_pdf_expecteds.txt``.

    One comparison covers the instructions, the numbers in their given forms, the answer lines
    or lettered options, the answer key's forms and letters, the page breaks, and the title and
    label.
    """
    reverse_shuffle(monkeypatch)

    actual = pdf_text(render_place_value(cases, answer_key, title, label))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
