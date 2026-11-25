"""Tests for the shared page layout: text measurement and wrapping, and answer key page breaks."""

from fractions import Fraction
from io import BytesIO
from unittest.mock import call, create_autospec

import pytest
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.question import BLANK
from core.written_numbers import FractionStyle, Piece, Pieces, UnreducedFraction
from render.pdf.page import (
    BOLD_FONT,
    FONT,
    SLANTED_RAISE,
    TEXT_SIZE,
    TEXT_WIDTH,
    Header,
    draw_answer_key,
    draw_fraction,
    draw_pieces,
    fit_font,
    fraction_width,
    pieces_width,
    stacked,
    text_width,
    wrap,
    wrap_pieces,
)
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
    ("width", "size"),
    [
        # "Number of Paddleboats" in bold is 112.24 wide at 10
        (120, 10),
        # 101.02 at 9 is too wide for 100, and 95.4 at 8.5 fits
        (100, 8.5),
        # too wide even at the smallest size, 6, which is used anyway
        (40, 6),
    ],
)
def test_fit_font(width: float, size: float) -> None:
    """The font is set at the size asked for if the text fits, else smaller, down to 6."""
    pdf = create_autospec(Canvas, instance=True)

    fit_font(pdf, "Number of Paddleboats", BOLD_FONT, 10, width)

    assert pdf.setFont.call_args_list == [call(BOLD_FONT, size)]


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
        # one-line solutions: 32 fill the key's first page, which follows the sheet's page 1
        (["7"] * 32, 2),
        (["7"] * 33, 3),
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
    draw_answer_key(pdf, Header(title="Place Value", label="Sheet A", name_line=False), solutions)
    assert pdf.getPageNumber() == last_page


def test_a_written_fraction_is_drawn_as_written() -> None:
    """2/8 is drawn as 2 over 8, where Fraction(2, 8) would be drawn as 1/4."""
    pdf = create_autospec(Canvas, instance=True)
    draw_pieces(pdf, 0, 0, ("x = ", UnreducedFraction(2, 8)), TEXT_SIZE)
    assert [each.args[2] for each in pdf.drawCentredString.call_args_list] == ["2", "8"]


@pytest.mark.parametrize(
    ("piece", "expected"),
    [
        (Fraction(1, 2), True),
        (UnreducedFraction(2, 8), True),
        (UnreducedFraction(2, 8, FractionStyle.SLASH), False),
        (UnreducedFraction(2, 8, FractionStyle.SLANTED), False),
        ("x = ", False),
    ],
)
def test_stacked(piece: Piece, expected: bool) -> None:
    """Only a stacked fraction needs room above and below its line."""
    assert stacked(piece) == expected


def test_a_fraction_with_a_slash_is_text() -> None:
    """3/4 with a slash is drawn on the line, as text."""
    pdf = create_autospec(Canvas, instance=True)
    fraction = UnreducedFraction(3, 4, FractionStyle.SLASH)
    end = draw_fraction(pdf, 10, 0, fraction, TEXT_SIZE)
    width = stringWidth("3/4", FONT, TEXT_SIZE)
    assert (pdf.drawString.call_args_list, end, fraction_width(fraction, TEXT_SIZE)) == (
        [call(10, 0, "3/4")],
        10 + width,
        width,
    )


def test_a_slanted_fraction_raises_its_numerator_beside_a_slanting_slash() -> None:
    """3/4 slanted: a small 3 raised, a slash, and a small 4 on the baseline."""
    pdf = create_autospec(Canvas, instance=True)
    fraction = UnreducedFraction(3, 4, FractionStyle.SLANTED)
    end = draw_fraction(pdf, 0, 0, fraction, 10)
    numerator, denominator = pdf.drawString.call_args_list
    assert (numerator.args[1:], denominator.args[1:], pdf.line.call_count, end) == (
        (10 * SLANTED_RAISE, "3"),
        (0, "4"),
        1,
        fraction_width(fraction, 10),
    )


def test_draw_pieces_draws_a_blank_as_a_square() -> None:
    """A blank in text beside a fraction is a square to write in."""
    pdf = create_autospec(Canvas, instance=True)
    draw_pieces(pdf, 0, 0, (f"{BLANK} = ", UnreducedFraction(1, 4)), TEXT_SIZE)
    assert pdf.rect.call_count == 1


QUESTION: Pieces = (
    "Which is greater, ",
    UnreducedFraction(3, 6),
    " or ",
    UnreducedFraction(3, 8),
    "?",
)


@pytest.mark.parametrize(
    ("width", "lines"),
    [
        (TEXT_WIDTH, [QUESTION]),
        # a break between words; "3/8?" stays together
        (
            pieces_width(("Which is greater,",), TEXT_SIZE) + 1,
            [
                ("Which is greater,",),
                (UnreducedFraction(3, 6), " or ", UnreducedFraction(3, 8), "?"),
            ],
        ),
    ],
)
def test_wrap_pieces(width: float, lines: list[Pieces]) -> None:
    """Pieces wrap between words, each fraction joined to the text it touches."""
    assert wrap_pieces(QUESTION, TEXT_SIZE, width) == lines


@pytest.mark.parametrize(
    ("pieces", "lines"),
    [
        # spaces ending one piece and starting the next are all kept
        (("Shade  ", " ", UnreducedFraction(3, 4)), [("Shade   ", UnreducedFraction(3, 4))]),
        # spaces at the very end are dropped
        (("Shade ", UnreducedFraction(3, 4), " "), [("Shade ", UnreducedFraction(3, 4))]),
    ],
)
def test_wrap_pieces_spacing(pieces: Pieces, lines: list[Pieces]) -> None:
    """Spacing within a line is kept, and the spaces at its end aren't drawn."""
    assert wrap_pieces(pieces, TEXT_SIZE, TEXT_WIDTH) == lines
