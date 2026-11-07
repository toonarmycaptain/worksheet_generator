"""
Tests for writing a number in each place-value form, omitting places whose digit is 0, and for
the base-ten blocks that show a number.
"""

import pytest

from core.placevalue.data import PlaceValueForm, PlaceValueQuestionData
from core.placevalue.representation import (
    BaseTenBlocks,
    base_ten_blocks,
    format_number,
    in_asked_form,
    in_given_form,
    place_value_terms,
)
from tests.data import TIMES


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        (35043, (30000, 5000, 40, 3)),
        (54321, (50000, 4000, 300, 20, 1)),
        (50421, (50000, 400, 20, 1)),  # no thousands
        (10000, (10000,)),
        (10001, (10000, 1)),
        (1005, (1000, 5)),
        (7, (7,)),
        (100000, (100000,)),
        (999999, (900000, 90000, 9000, 900, 90, 9)),
    ],
)
def test_terms_are_the_values_of_the_digits_that_are_not_0(
    number: int, expected: tuple[int, ...]
) -> None:
    """The largest place comes first, and a digit of 0 contributes no term."""
    assert place_value_terms(number) == expected


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        (347, BaseTenBlocks(hundreds=3, tens=4, ones=7)),
        # a digit of 0 has no blocks
        (305, BaseTenBlocks(hundreds=3, tens=0, ones=5)),
        (47, BaseTenBlocks(hundreds=0, tens=4, ones=7)),
        (1, BaseTenBlocks(hundreds=0, tens=0, ones=1)),
        (0, BaseTenBlocks(hundreds=0, tens=0, ones=0)),
        (999, BaseTenBlocks(hundreds=9, tens=9, ones=9)),
    ],
)
def test_base_ten_blocks(number: int, expected: BaseTenBlocks) -> None:
    """The fewest blocks: one flat, rod or unit for each unit of each digit."""
    assert base_ten_blocks(number) == expected


@pytest.mark.parametrize(
    ("number", "message"),
    [
        (-1, "Base-ten blocks show numbers from 0 to 999, not -1."),
        (1000, "Base-ten blocks show numbers from 0 to 999, not 1000."),
    ],
)
def test_base_ten_blocks_errors(number: int, message: str) -> None:
    """There is no block for a thousand, so 1,000 raises ``ValueError`` rather than 10 flats."""
    with pytest.raises(ValueError) as error:
        base_ten_blocks(number)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("form", "number", "expected"),
    [
        # standard: commas between the groups of three digits
        (PlaceValueForm.STANDARD, 35043, "35,043"),
        (PlaceValueForm.STANDARD, 1005, "1,005"),
        (PlaceValueForm.STANDARD, 999, "999"),
        (PlaceValueForm.STANDARD, 100000, "100,000"),
        # expanded
        (PlaceValueForm.EXPANDED, 35043, "30,000 + 5,000 + 40 + 3"),
        (PlaceValueForm.EXPANDED, 50421, "50,000 + 400 + 20 + 1"),
        (PlaceValueForm.EXPANDED, 10000, "10,000"),
        (PlaceValueForm.EXPANDED, 7, "7"),
        # unit: a digit of 1 is singular
        (PlaceValueForm.UNIT, 35043, "3 ten thousands 5 thousands 4 tens 3 ones"),
        (PlaceValueForm.UNIT, 54321, "5 ten thousands 4 thousands 3 hundreds 2 tens 1 one"),
        (PlaceValueForm.UNIT, 11111, "1 ten thousand 1 thousand 1 hundred 1 ten 1 one"),
        (PlaceValueForm.UNIT, 100000, "1 hundred thousand"),
        (PlaceValueForm.UNIT, 250000, "2 hundred thousands 5 ten thousands"),
        # expanded notation
        (
            PlaceValueForm.EXPANDED_NOTATION,
            35043,
            f"(3 {TIMES} 10,000) + (5 {TIMES} 1,000) + (4 {TIMES} 10) + (3 {TIMES} 1)",
        ),
        (
            PlaceValueForm.EXPANDED_NOTATION,
            50421,
            f"(5 {TIMES} 10,000) + (4 {TIMES} 100) + (2 {TIMES} 10) + (1 {TIMES} 1)",
        ),
        (PlaceValueForm.EXPANDED_NOTATION, 10000, f"(1 {TIMES} 10,000)"),
        # word: hyphens from twenty-one to ninety-nine, a comma after "thousand", never "and"
        (PlaceValueForm.WORD, 35043, "thirty-five thousand, forty-three"),
        (PlaceValueForm.WORD, 54321, "fifty-four thousand, three hundred twenty-one"),
        (PlaceValueForm.WORD, 50421, "fifty thousand, four hundred twenty-one"),
        (PlaceValueForm.WORD, 10000, "ten thousand"),
        (PlaceValueForm.WORD, 14000, "fourteen thousand"),
        (PlaceValueForm.WORD, 40014, "forty thousand, fourteen"),
        (PlaceValueForm.WORD, 1005, "one thousand, five"),
        (PlaceValueForm.WORD, 20, "twenty"),
        (PlaceValueForm.WORD, 7, "seven"),
        (PlaceValueForm.WORD, 999, "nine hundred ninety-nine"),
        (PlaceValueForm.WORD, 100000, "one hundred thousand"),
        (PlaceValueForm.WORD, 101101, "one hundred one thousand, one hundred one"),
        (
            PlaceValueForm.WORD,
            999999,
            "nine hundred ninety-nine thousand, nine hundred ninety-nine",
        ),
    ],
)
def test_each_form_writes_the_number(form: PlaceValueForm, number: int, expected: str) -> None:
    """Every form but standard omits places whose digit is 0; standard is the number itself."""
    assert format_number(number, form) == expected


def test_a_question_is_shown_in_its_given_form_and_answered_in_its_asked_form() -> None:
    data = PlaceValueQuestionData(35043, PlaceValueForm.WORD, PlaceValueForm.EXPANDED)
    assert (in_given_form(data), in_asked_form(data)) == (
        "thirty-five thousand, forty-three",
        "30,000 + 5,000 + 40 + 3",
    )


@pytest.mark.parametrize(
    ("number", "message"),
    [
        (0, "Place-value forms are written for 1 to 999,999, not 0."),
        (-1, "Place-value forms are written for 1 to 999,999, not -1."),
        (1_000_000, "Place-value forms are written for 1 to 999,999, not 1,000,000."),
    ],
)
def test_place_value_terms_errors(number: int, message: str) -> None:
    """Numbers outside the range raise ``ValueError`` rather than producing incorrect terms."""
    with pytest.raises(ValueError) as error:
        place_value_terms(number)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("number", "form", "message"),
    [
        (0, PlaceValueForm.STANDARD, "Place-value forms are written for 1 to 999,999, not 0."),
        (-1, PlaceValueForm.STANDARD, "Place-value forms are written for 1 to 999,999, not -1."),
        (
            1_000_000,
            PlaceValueForm.STANDARD,
            "Place-value forms are written for 1 to 999,999, not 1,000,000.",
        ),
        # blocks are drawn, so there is no text to write
        (352, PlaceValueForm.BLOCKS, "Base-ten blocks are drawn, not written."),
    ],
)
def test_format_number_errors(number: int, form: PlaceValueForm, message: str) -> None:
    """
    Numbers outside the range raise ``ValueError`` rather than producing an incorrect form, and
    so do base-ten blocks, which are drawn rather than written.
    """
    with pytest.raises(ValueError) as error:
        format_number(number, form)
    assert str(error.value) == message
