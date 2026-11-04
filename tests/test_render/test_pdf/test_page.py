"""Tests for the shared page layout: text measurement and wrapping, and answer key page breaks."""

from io import BytesIO

import pytest
from reportlab.pdfgen.canvas import Canvas

from core.question import BLANK
from render.pdf.page import TEXT_SIZE, TEXT_WIDTH, draw_answer_key, text_width, wrap
from tests.data import TIMES

# 777,777 in expanded notation: one line at the full width
EXPANDED_NOTATION = (
    f"(7 {TIMES} 100,000) + (7 {TIMES} 10,000) + (7 {TIMES} 1,000) + (7 {TIMES} 100) + "
    f"(7 {TIMES} 10) + (7 {TIMES} 1)"
)
# a self-check tiles answer key line, 777,777 from unit form to word form: three lines
UNIT_TO_WORD = (
    "7 hundred thousands 7 ten thousands 7 thousands 7 hundreds 7 tens 7 ones = seven hundred "
    "seventy-seven thousand, seven hundred seventy-seven    (L)"
)


@pytest.mark.parametrize(
    ("text", "size", "blank_side", "width"),
    [
        # Helvetica's digits are 556 thousandths of the size wide, "+", "=" and "÷" 584, and a
        # space 278
        ("3 + 4", 14, None, 31.528),
        # a square is 1.4 times the size, 19.6 at 14, where the □ glyph is 10.654
        (f"{BLANK} ÷ 4 = 7", 14, None, 67.088),
        (f"28 ÷ {BLANK} = 4", 14, None, 74.872),
        (f"{BLANK} + {BLANK} = 7", 14, None, 78.904),  # each square counts
        # the missing-number sheet's square, 36 wide at 20
        (f"{BLANK} ÷ 4 = 7", 20, 36, 103.84),
    ],
)
def test_text_width(text: str, size: float, blank_side: float | None, width: float) -> None:
    assert text_width(text, size, blank_side) == pytest.approx(width)


@pytest.mark.parametrize(
    ("text", "width", "expected"),
    [
        # short enough for one line, with its spacing kept
        ("3 + 4 = 7    (A)", TEXT_WIDTH, ["3 + 4 = 7    (A)"]),
        # a sum breaks after a "+", and each bracketed term stays whole
        (
            EXPANDED_NOTATION,
            300,
            [
                f"(7 {TIMES} 100,000) + (7 {TIMES} 10,000) + (7 {TIMES} 1,000) +",
                f"(7 {TIMES} 100) + (7 {TIMES} 10) + (7 {TIMES} 1)",
            ],
        ),
        # a bracketed term wider than the line is still not broken
        (f"(7 {TIMES} 100,000)", 50, [f"(7 {TIMES} 100,000)"]),
        # the "+" that ends a line is measured too: with "90 +" the first line is too wide
        (
            "ninety-nine thousand, nine hundred ninety-nine = 90,000 + 9,000 + 900 + 90 + 9    (L)",
            TEXT_WIDTH,
            [
                "ninety-nine thousand, nine hundred ninety-nine = 90,000 + 9,000 + 900 +",
                "90 + 9    (L)",
            ],
        ),
        # a term too long for a line of its own breaks between its words: unit form before "="
        (
            "7 hundred thousands 7 ten thousands 7 thousands 7 hundreds 7 tens 7 ones = 700,000 + "
            "70,000 + 7,000 + 700 + 70 + 7    (L)",
            TEXT_WIDTH,
            [
                "7 hundred thousands 7 ten thousands 7 thousands 7 hundreds 7 tens 7",
                "ones = 700,000 + 70,000 + 7,000 + 700 + 70 + 7    (L)",
            ],
        ),
        # and word form after "=", which starts on the line the sum before it is on
        (
            "700,000 + 70,000 + 7,000 + 700 + 70 + 7 = seven hundred seventy-seven thousand, "
            "seven hundred seventy-seven    (L)",
            TEXT_WIDTH,
            [
                "700,000 + 70,000 + 7,000 + 700 + 70 + 7 = seven hundred seventy-seven",
                "thousand, seven hundred seventy-seven    (L)",
            ],
        ),
        # text that is not a sum breaks between words
        (
            UNIT_TO_WORD,
            TEXT_WIDTH,
            [
                "7 hundred thousands 7 ten thousands 7 thousands 7 hundreds 7 tens 7",
                "ones = seven hundred seventy-seven thousand, seven hundred",
                "seventy-seven    (L)",
            ],
        ),
        # a square is measured as drawn, 67.088 for the whole equation: measured as the □
        # glyph, 58.142, it would fit on one line
        (f"{BLANK} ÷ 4 = 7", 60, [f"{BLANK} ÷ 4 =", "7"]),
    ],
)
def test_wrap(text: str, width: float, expected: list[str]) -> None:
    assert wrap(text, TEXT_SIZE, width) == expected


@pytest.mark.parametrize(
    ("solutions", "last_page"),
    [
        # one-line solutions: 31 fill the key's first page, which follows the sheet's page 1
        (["7"] * 31, 2),
        (["7"] * 32, 3),
        # three-line solutions: 10 fill a page
        ([UNIT_TO_WORD] * 10, 2),
        ([UNIT_TO_WORD] * 11, 3),
    ],
)
def test_an_answer_key_goes_on_to_another_page_when_one_is_full(
    solutions: list[str], last_page: int
) -> None:
    """A solution whose last line would fall below the bottom margin starts on the next page."""
    pdf = Canvas(BytesIO())
    draw_answer_key(pdf, "Place Value", "Sheet A", solutions)
    assert pdf.getPageNumber() == last_page
