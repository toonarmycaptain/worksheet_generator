"""
Formatting of numbers in each place-value form, such as 35,043 as 30,000 + 5,000 + 40 + 3.

Every form except standard form omits places whose digit is 0, so 35,043 has no hundreds term.
Standard form is the number itself, with commas between groups of three digits.
"""

from dataclasses import dataclass
from typing import assert_never

from core.placevalue.data import PlaceValueForm, PlaceValueQuestionData
from core.question import Question
from core.self_check_tiles import TileQuestion

LARGEST_NUMBER = 999_999  # the forms have place names up to the hundred thousands
LARGEST_BLOCKS_NUMBER = 999  # base-ten blocks go up to the hundreds' flats

# What each base-ten block is called, keyed by its value, largest first, as a sheet's key names
# them
BLOCK_NAMES = {100: "flat", 10: "rod", 1: "unit"}

# What each form is called, in a question ("Write in expanded form:") and on the web page
FORM_NAMES = {
    PlaceValueForm.STANDARD: "standard form",
    PlaceValueForm.EXPANDED: "expanded form",
    PlaceValueForm.UNIT: "unit form",
    PlaceValueForm.EXPANDED_NOTATION: "expanded notation",
    PlaceValueForm.WORD: "word form",
}

# The name of each place, from the ones up. More than one adds an "s": "3 ten thousands".
_PLACE_NAMES = ("one", "ten", "hundred", "thousand", "ten thousand", "hundred thousand")

_TIMES = "\N{MULTIPLICATION SIGN}"

_UP_TO_NINETEEN = (
    "",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
)
_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")


def place_value_terms(number: int) -> tuple[int, ...]:
    """
    Return the value of each non-zero digit of ``number``, largest first.

    35,043 gives ``(30000, 5000, 40, 3)``; its hundreds digit is 0, so there is no hundreds term.
    """
    _check_in_range(number)
    return tuple(digit * 10**place for digit, place in _non_zero_digits(number))


@dataclass(frozen=True)
class BaseTenBlocks:
    """A number shown as base-ten blocks: ``hundreds`` flats, ``tens`` rods and ``ones`` units."""

    hundreds: int
    tens: int
    ones: int


def base_ten_blocks(number: int) -> BaseTenBlocks:
    """
    Return the fewest base-ten blocks that show ``number``: one block for each unit of each
    digit, so 347 is 3 flats, 4 rods and 7 units.

    Raises ``ValueError`` for a number below 0 or above ``LARGEST_BLOCKS_NUMBER``.
    """
    if not 0 <= number <= LARGEST_BLOCKS_NUMBER:
        raise ValueError(
            f"Base-ten blocks show numbers from 0 to {LARGEST_BLOCKS_NUMBER}, not {number}."
        )
    hundreds, rest = divmod(number, 100)
    tens, ones = divmod(rest, 10)
    return BaseTenBlocks(hundreds, tens, ones)


def format_number(number: int, form: PlaceValueForm) -> str:
    """
    Return ``number`` written in ``form``, for a question or its answer.

    - standard: 35,043
    - expanded: 30,000 + 5,000 + 40 + 3
    - unit: 3 ten thousands 5 thousands 4 tens 3 ones, with a digit of 1 singular: 1 ten
    - expanded notation: (3 x 10,000) + (5 x 1,000) + (4 x 10) + (3 x 1), using the
      multiplication sign rather than the letter x
    - word: thirty-five thousand, forty-three, hyphenated from twenty-one to ninety-nine, with a
      comma after "thousand" and never "and", which is reserved for the decimal point

    ``number`` must be from 1 to 999,999, which covers the numbers up to 100,000 in TEKS 3.2(A);
    otherwise ``ValueError`` is raised.
    """
    _check_in_range(number)
    match form:
        case PlaceValueForm.STANDARD:
            return f"{number:,}"
        case PlaceValueForm.EXPANDED:
            return " + ".join(f"{term:,}" for term in place_value_terms(number))
        case PlaceValueForm.UNIT:
            return " ".join(_unit(digit, place) for digit, place in _non_zero_digits(number))
        case PlaceValueForm.EXPANDED_NOTATION:
            return " + ".join(
                f"({digit} {_TIMES} {10**place:,})" for digit, place in _non_zero_digits(number)
            )
        case PlaceValueForm.WORD:
            return _word_form(number)
        case _:
            assert_never(form)


def in_given_form(data: PlaceValueQuestionData) -> str:
    """Return the question's number in its ``given`` form."""
    return format_number(data.answer, data.given)


def in_asked_form(data: PlaceValueQuestionData) -> str:
    """Return the question's number in its ``asked`` form: the answer as the student writes it."""
    return format_number(data.answer, data.asked)


def instruction(question: Question[PlaceValueQuestionData]) -> str:
    """Return what the question asks: to write its number in the asked form, or to choose it."""
    form = FORM_NAMES[question.data.asked]
    return f"Which is this number in {form}?" if question.wrong_answers else f"Write in {form}:"


def place_value_tile_question(data: PlaceValueQuestionData) -> TileQuestion:
    """
    Convert the question to a ``TileQuestion`` for the self-check tiles sheet.

    The prompt shows the number in its given form; the answer is the number in its asked form.
    """
    shown = in_given_form(data)
    answer = in_asked_form(data)
    return TileQuestion(prompt=f"{shown} = ?", answer=answer, solution=f"{shown} = {answer}")


def _check_in_range(number: int) -> None:
    if not 1 <= number <= LARGEST_NUMBER:
        raise ValueError(
            f"Place-value forms are written for 1 to {LARGEST_NUMBER:,}, not {number:,}."
        )


def _non_zero_digits(number: int) -> list[tuple[int, int]]:
    """Return each non-zero digit of ``number`` with its place (0 for ones), largest first."""
    digits = str(number)
    return [
        (int(digit), len(digits) - 1 - index) for index, digit in enumerate(digits) if digit != "0"
    ]


def _unit(digit: int, place: int) -> str:
    """Return one place in unit form, such as "1 ten" or "3 ten thousands"."""
    name = _PLACE_NAMES[place]
    return f"{digit} {name}" if digit == 1 else f"{digit} {name}s"


def _word_form(number: int) -> str:
    """Return ``number`` in words: the thousands, a comma, then the remainder."""
    thousands, rest = divmod(number, 1000)
    parts: list[str] = []
    if thousands:
        parts.append(f"{_words_below_1000(thousands)} thousand")
    if rest:
        parts.append(_words_below_1000(rest))
    return ", ".join(parts)


def _words_below_1000(number: int) -> str:
    """Return a number from 1 to 999 in words, such as "four hundred twenty-one"."""
    hundreds, rest = divmod(number, 100)
    words: list[str] = []
    if hundreds:
        words.append(f"{_UP_TO_NINETEEN[hundreds]} hundred")
    if rest >= 20:
        tens, ones = divmod(rest, 10)
        words.append(f"{_TENS[tens]}-{_UP_TO_NINETEEN[ones]}" if ones else _TENS[tens])
    elif rest:
        words.append(_UP_TO_NINETEEN[rest])
    return " ".join(words)
