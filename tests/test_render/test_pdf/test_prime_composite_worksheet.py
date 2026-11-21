"""
Tests for the prime and composite worksheet PDFs, rendered from hand-built questions.

The question generator is not used: each question is built by hand with its response, most of
them from STAAR's released items.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/prime_composite_worksheet_pdf_expecteds.txt``. The text includes every question, the
lettered choices in a row or one under another, the rows of numbers with their boxes or words,
the answer lines and their labels, the answer bank and pattern, the answer key and the page
breaks. To regenerate sections after an intended change, uncomment the ``write_section`` lines in
``test_pdf_draws_the_expected_text`` and run it (``-k`` selects cases).
"""

from collections.abc import Sequence

import pytest

from core.prime_composite.claims import REASONS
from core.prime_composite.data import (
    ChooseTwoQuestionData,
    Claim,
    CountQuestionData,
    EachNumberQuestionData,
    FactorPairCountQuestionData,
    FactorPairQuestionData,
    ListFactorsQuestionData,
    MissingPrimeQuestionData,
    PrimeCompositeQuestion,
    PrimeCountQuestionData,
    Verdict,
    WhoIsCorrectQuestionData,
    WhoseNumberQuestionData,
)
from core.prime_composite.factors import Primality
from core.question import FreeResponse, MultipleChoice, Question
from tests.data import REAL_CASE_SLOTS
from tests.helpers import GOLDENS, pdf_text, read_sections, render_prime_composite

PRIME, COMPOSITE, NEITHER = Primality
FIRST, SECOND, BOTH, NEITHER_OF_THEM = Verdict
WORDS = (PRIME, COMPOSITE, NEITHER)

ONLY_TWO = REASONS[1]  # "{n} is prime because it has only two factors"
PRODUCT = REASONS[2]  # "{n} is composite because {a} x {b} = {n}"
ALL_EVEN = REASONS[9]  # "2 is composite because all even numbers are composite"
ODD_PRIME = REASONS[14]  # "{n} is prime because it is odd", about a prime: the wrong reason

SETH = FactorPairQuestionData(
    132, ((4, 33), (6, 22)), "Seth", ((6, 22), (11, 12), (3, 44), (2, 66))
)
STUDENTS = WhoseNumberQuestionData(
    30, 40, (("Elly", 35), ("Ulysses", 39), ("Maggie", 37), ("Palmer", 33)), PRIME, "Maggie"
)
BRENDA_AND_CARLA = WhoIsCorrectQuestionData(
    (Claim("Brenda", 2, ONLY_TWO), Claim("Carla", 2, ALL_EVEN)), False, FIRST
)
CY_AND_DOT = WhoIsCorrectQuestionData(
    (Claim("Cy", 37, ODD_PRIME), Claim("Dot", 51, PRODUCT, (3, 17))), True, SECOND
)
ROW = EachNumberQuestionData(
    (1, 9, 17, 21, 2, 57), (NEITHER, COMPOSITE, PRIME, COMPOSITE, PRIME, COMPOSITE)
)

# One of each, written: answer lines, two labelled lines for factors, three to explain, a row of
# numbers to circle two of, and a row with a box under each number. It runs onto a second page.
WRITTEN: list[PrimeCompositeQuestion] = [
    Question(FactorPairQuestionData(184, ((4, 46),)), FreeResponse()),
    Question(SETH, FreeResponse()),
    Question(CountQuestionData((51, 52, 53, 54, 55), COMPOSITE, 4), FreeResponse()),
    Question(ChooseTwoQuestionData((3, 4, 19, 21, 31), COMPOSITE, (4, 21)), FreeResponse()),
    Question(MissingPrimeQuestionData("Jaylen", 30, 50, 43), FreeResponse()),
    Question(STUDENTS, FreeResponse()),
    Question(CY_AND_DOT, FreeResponse()),
    Question(ROW, FreeResponse()),
    Question(ListFactorsQuestionData(51, ((1, 3, 17, 51), COMPOSITE)), FreeResponse()),
]

# One of each, as multiple choice: short choices in a row, statements and long factor lists one
# under another, five numbers to select two from, and the words under each number of a row.
CHOICES: list[PrimeCompositeQuestion] = [
    Question(
        FactorPairQuestionData(184, ((4, 46),)),
        MultipleChoice(((1, 184), (4, 46), (2, 92), (8, 23)), frozenset({1})),
    ),
    Question(SETH, MultipleChoice(SETH.listed, frozenset({0}))),
    Question(
        CountQuestionData((51, 52, 53, 54, 55), COMPOSITE, 4),
        MultipleChoice((4, 1, 2, 3), frozenset({0})),
    ),
    Question(
        ChooseTwoQuestionData((3, 4, 19, 21, 31), COMPOSITE, (4, 21)),
        MultipleChoice((3, 4, 19, 21, 31), frozenset({1, 3})),
    ),
    Question(
        MissingPrimeQuestionData("Jaylen", 30, 50, 43),
        MultipleChoice((49, 39, 43, 33), frozenset({2})),
    ),
    Question(STUDENTS, MultipleChoice(("Elly", "Ulysses", "Maggie", "Palmer"), frozenset({2}))),
    Question(
        BRENDA_AND_CARLA, MultipleChoice((FIRST, SECOND, BOTH, NEITHER_OF_THEM), frozenset({0}))
    ),
    Question(CY_AND_DOT, MultipleChoice((FIRST, SECOND, BOTH, NEITHER_OF_THEM), frozenset({1}))),
    Question(
        ROW,
        (
            MultipleChoice(WORDS, frozenset({2})),
            MultipleChoice(WORDS, frozenset({1})),
            MultipleChoice(WORDS, frozenset({0})),
            MultipleChoice(WORDS, frozenset({1})),
            MultipleChoice(WORDS, frozenset({0})),
            MultipleChoice(WORDS, frozenset({1})),
        ),
    ),
    Question(
        ListFactorsQuestionData(60, ((1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60), COMPOSITE)),
        MultipleChoice(
            (
                ((1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60), PRIME),
                ((1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30), COMPOSITE),
                ((1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60), COMPOSITE),
                ((1, 2, 3, 4, 5, 6, 7, 10, 12, 15, 20, 30, 60), COMPOSITE),
            ),
            frozenset({2}),
        ),
    ),
]

# Twelve counting questions with different answers, as a tiles sheet asks them
TILES: list[PrimeCompositeQuestion] = [
    Question(
        EachNumberQuestionData(
            (21, 31, 87, 29, 73, 41), (COMPOSITE, PRIME, COMPOSITE, PRIME, PRIME, PRIME)
        ),
        FreeResponse(),
    ),
    Question(CountQuestionData((92, 93, 94, 95, 96), PRIME, 0), FreeResponse()),
    Question(
        EachNumberQuestionData(
            (23, 49, 61, 31, 33, 63), (PRIME, COMPOSITE, PRIME, PRIME, COMPOSITE, COMPOSITE)
        ),
        FreeResponse(),
    ),
    Question(PrimeCountQuestionData(20, 70, 11), FreeResponse()),
    Question(CountQuestionData((70, 71, 72, 73, 74), PRIME, 2), FreeResponse()),
    Question(FactorPairCountQuestionData(168, 4), FreeResponse()),
    Question(PrimeCountQuestionData(20, 60, 9), FreeResponse()),
    Question(FactorPairCountQuestionData(180, 5), FreeResponse()),
    Question(
        CountQuestionData((81, 82, 83, 84, 85, 86, 87), COMPOSITE, 6),
        FreeResponse(),
    ),
    Question(FactorPairCountQuestionData(16, 1), FreeResponse()),
    Question(PrimeCountQuestionData(40, 50, 3), FreeResponse()),
    Question(CountQuestionData((4, 5, 6, 7, 8, 9, 10, 11, 12), COMPOSITE, 7), FreeResponse()),
]


EXPECTED = GOLDENS / "prime_composite_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "questions", "slot_of", "answer_key", "title", "label"),
    [
        ("written", WRITTEN, None, False, "Prime and Composite Numbers", "Sheet A"),
        ("written_answer_key", WRITTEN, None, True, "Prime and Composite Numbers", "Sheet A"),
        ("choices_answer_key", CHOICES, None, True, "Prime and Composite Numbers", "Sheet A"),
        (
            "tiles_answer_key",
            TILES,
            REAL_CASE_SLOTS,
            True,
            "Prime and Composite Numbers",
            "Sheet A",
        ),
        ("other_title_and_label", WRITTEN[:2], None, False, "Primes", "Day 2"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: Sequence[PrimeCompositeQuestion],
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of ``prime_composite_worksheet_pdf_expecteds.txt``.

    One comparison covers each problem's question, its lettered choices and their layout, its
    row of numbers with boxes or words, its answer lines, the answer bank and pattern, the
    answer key, the page breaks, and the title and label.
    """
    actual = pdf_text(render_prime_composite(questions, slot_of, answer_key, title, label))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


@pytest.mark.parametrize(
    ("questions", "message"),
    [
        (
            # a question whose answer is printed in it
            [Question(STUDENTS, FreeResponse())],
            "A self-check tiles sheet asks only written counting questions.",
        ),
        (
            # a counting question with choices
            [
                Question(
                    CountQuestionData((51, 52, 53, 54, 55), COMPOSITE, 4),
                    MultipleChoice((4, 1, 2, 3), frozenset({0})),
                )
            ],
            "A self-check tiles sheet asks only written counting questions.",
        ),
    ],
)
def test_render_prime_composite_worksheet_errors(
    questions: Sequence[PrimeCompositeQuestion], message: str
) -> None:
    with pytest.raises(ValueError) as error:
        render_prime_composite(questions, REAL_CASE_SLOTS[:1], False, "Primes", "Sheet A")
    assert str(error.value) == message
