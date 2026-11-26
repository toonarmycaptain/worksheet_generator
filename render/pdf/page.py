"""
Page layout shared by every PDF worksheet.

Defines the page geometry and fonts, and draws the header and footer, a sheet's instruction,
wrapped text, stacked fractions, a problem's number and text, and the answer key pages. Also
shrinks text to fit its space, starts a new page when a problem won't fit, and letters
multiple-choice options.
"""

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from datetime import date
from fractions import Fraction
from string import ascii_uppercase
from typing import Any, BinaryIO

from reportlab.lib.colors import gray
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.question import BLANK, CIRCLE, MultipleChoice
from core.written_numbers import FractionStyle, Piece, Pieces, UnreducedFraction, merge_pieces

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 54
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
TEXT_INDENT = 28  # question text is indented past its number
TEXT_WIDTH = PAGE_WIDTH - 2 * MARGIN - TEXT_INDENT
FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"
ITALIC_FONT = "Helvetica-Oblique"  # same widths as FONT, so wrap measures it correctly
TEXT_SIZE = 14
LINE_HEIGHT = 20
HEADER_ROW = 30  # from the title to the Name/Date line, and from either to the content
INSTRUCTION_SIZE = 12
INSTRUCTION_LINE_HEIGHT = 16
INSTRUCTION_GAP = 10  # extra space between the instruction and the first problem
SMALLEST_FIT_SIZE = 6  # fit_font shrinks text too wide for its space down to this size
FRACTION_SCALE = 0.85  # a stacked fraction's numbers, as a share of the text's size
FRACTION_ROOM = 6  # the extra space a line with a stacked fraction needs above and below
# A slanted fraction, like ¾: its numbers' size, as a share of the text's, how far the numerator
# is raised, and the slash's rise and run, as shares of the text's size
SLANTED_SCALE = 0.62
SLANTED_RAISE = 0.42
SLASH_RISE = 0.8
SLASH_RUN = 0.32

# A word with its preceding whitespace. A bracketed term, such as (3 x 10,000), is one word.
_WORD = re.compile(r"(\s*)(\([^)]*\)|\S+)")
_BLANKS = re.compile(f"({BLANK}|{CIRCLE})")  # an empty square or circle to write in


def draw_text(
    pdf: Canvas, x: float, y: float, text: str, size: float, blank_side: float | None = None
) -> None:
    """
    Draw ``text`` from ``x`` along baseline ``y``, rendering each ``BLANK`` as an empty square
    and each ``CIRCLE`` as an empty circle.

    Like ``drawString``, it uses the current font, which must be ``FONT`` at ``size``.
    Helvetica has neither glyph, so each square is drawn as a box ``blank_side`` wide and high
    (1.4 times ``size`` by default), centred on the middle of a digit, and each circle as wide.
    """
    side = _square_side(size, blank_side)
    middle = y + size * 0.35  # about halfway up a digit
    for piece in _BLANKS.split(text):
        if piece == BLANK:
            pdf.rect(x, middle - side / 2, side, side, stroke=1, fill=0)
            x += side
        elif piece == CIRCLE:
            pdf.circle(x + side / 2, middle, side / 2, stroke=1, fill=0)
            x += side
        else:
            pdf.drawString(x, y, piece)
            x += stringWidth(piece, FONT, size)


def draw_fraction(
    pdf: Canvas, x: float, y: float, fraction: Fraction | UnreducedFraction, size: float
) -> float:
    """
    Draw ``fraction`` from ``x`` beside text on baseline ``y`` in ``FONT`` at ``size``, and
    return the x after it. The fraction is drawn as given, so a sign goes in the text before it.

    A ``Fraction`` is drawn stacked, and an ``UnreducedFraction`` in its style. Stacked, the
    numerator and denominator are centred over and under a bar at the height of a minus sign, at
    ``FRACTION_SCALE`` of ``size``. With a slash, it's text: 3/4. Slanted, like ¾, a small
    numerator is raised before a slanting slash, and a small denominator sits on the baseline
    after it.
    """
    style = fraction.style if isinstance(fraction, UnreducedFraction) else FractionStyle.STACKED
    if style is FractionStyle.SLASH:
        text = _slash_text(fraction)
        pdf.drawString(x, y, text)
        return x + stringWidth(text, FONT, size)
    if style is FractionStyle.SLANTED:
        return _draw_slanted(pdf, x, y, fraction, size)
    small = size * FRACTION_SCALE
    numerator, denominator = f"{fraction.numerator:,}", f"{fraction.denominator:,}"
    width = fraction_width(fraction, size)
    middle = x + width / 2
    bar = y + size * 0.3
    gap = small * 0.2  # between the bar and each number
    pdf.setFont(FONT, small)
    pdf.drawCentredString(middle, bar + gap, numerator)
    pdf.drawCentredString(middle, bar - gap - small * 0.72, denominator)  # 0.72: a digit's height
    pdf.line(x + size * 0.1, bar, x + width - size * 0.1, bar)
    pdf.setFont(FONT, size)
    return x + width


def fraction_width(fraction: Fraction | UnreducedFraction, size: float) -> float:
    """Return the width ``draw_fraction`` takes for ``fraction`` beside text at ``size``."""
    style = fraction.style if isinstance(fraction, UnreducedFraction) else FractionStyle.STACKED
    if style is FractionStyle.SLASH:
        return float(stringWidth(_slash_text(fraction), FONT, size))
    if style is FractionStyle.SLANTED:
        return _slanted_layout(fraction, size)[3]
    small = size * FRACTION_SCALE
    numbers = (f"{fraction.numerator:,}", f"{fraction.denominator:,}")
    return max(stringWidth(number, FONT, small) for number in numbers) + size * 0.4


def stacked(piece: Piece) -> bool:
    """Return whether ``piece`` is a fraction drawn stacked, which needs room above and below
    its line."""
    if isinstance(piece, UnreducedFraction):
        return piece.style is FractionStyle.STACKED
    return isinstance(piece, Fraction)


def _slash_text(fraction: Fraction | UnreducedFraction) -> str:
    """Return ``fraction`` written on the line with a slash: 3/4."""
    return f"{fraction.numerator:,}/{fraction.denominator:,}"


def _slanted_layout(
    fraction: Fraction | UnreducedFraction, size: float
) -> tuple[float, float, float, float]:
    """
    Return where a slanted fraction's parts go, from its left edge, beside text at ``size``: the
    numerator's left, the slash's bottom, the denominator's left, and the whole width.

    The numerator ends where it would touch the slash at its baseline's height, and the
    denominator starts clear of the slash at its top's height, so each number tucks in beside it.
    """
    small = size * SLANTED_SCALE
    numerator = stringWidth(f"{fraction.numerator:,}", FONT, small)
    denominator = stringWidth(f"{fraction.denominator:,}", FONT, small)
    margin = size * 0.05
    run_per_rise = SLASH_RUN / SLASH_RISE
    # where the slash is level with the numerator's baseline, and with the denominator's top
    slash = margin + numerator - SLANTED_RAISE * size * run_per_rise + size * 0.06
    denominator_left = slash + small * 0.72 * run_per_rise + size * 0.08
    return margin, slash, denominator_left, denominator_left + denominator + margin


def _draw_slanted(
    pdf: Canvas, x: float, y: float, fraction: Fraction | UnreducedFraction, size: float
) -> float:
    """Draw ``fraction`` slanted, like ¾, and return the x after it."""
    numerator_left, slash, denominator_left, width = _slanted_layout(fraction, size)
    small = size * SLANTED_SCALE
    pdf.setFont(FONT, small)
    pdf.drawString(x + numerator_left, y + size * SLANTED_RAISE, f"{fraction.numerator:,}")
    pdf.drawString(x + denominator_left, y, f"{fraction.denominator:,}")
    pdf.saveState()
    pdf.setLineWidth(size / 16)
    pdf.line(x + slash, y, x + slash + size * SLASH_RUN, y + size * SLASH_RISE)
    pdf.restoreState()
    pdf.setFont(FONT, size)
    return x + width


def draw_pieces(pdf: Canvas, x: float, y: float, pieces: Iterable[Piece], size: float) -> float:
    """
    Draw ``pieces`` one after another from ``x`` on baseline ``y`` in ``FONT`` at ``size``: each
    string as text, by ``draw_text``, so a ``BLANK`` is a square, and each fraction by
    ``draw_fraction``. Return the x after them.
    """
    pdf.setFont(FONT, size)
    for piece in pieces:
        if isinstance(piece, str):
            draw_text(pdf, x, y, piece, size)
            x += text_width(piece, size)
        else:
            x = draw_fraction(pdf, x, y, piece, size)
    return x


def pieces_width(pieces: Iterable[Piece], size: float) -> float:
    """Return the width ``draw_pieces`` takes for ``pieces`` at ``size``."""
    return sum(
        text_width(piece, size) if isinstance(piece, str) else fraction_width(piece, size)
        for piece in pieces
    )


def wrap_pieces(pieces: Pieces, size: float, width: float) -> list[Pieces]:
    """
    Split ``pieces`` into lines no wider than ``width``, between words, as far as they allow,
    measured as ``draw_pieces`` draws them. A fraction is a word, joined to any text it touches
    without a space, so "of 3/8?" can break before "3/8?" but never inside it. Spacing within a
    line is kept, and the space at a break is dropped.
    """
    words: list[tuple[str, list[Piece]]] = []  # each word, after the space before it
    for piece in pieces:
        parts = re.split(r"(\s+)", piece) if isinstance(piece, str) else [piece]
        for part in parts:
            if isinstance(part, str) and part.isspace():
                if words and not words[-1][1]:  # spaces at the end of one piece and the next
                    words[-1] = (words[-1][0] + part, [])
                else:
                    words.append((part, []))
            elif part != "":
                if not words:
                    words.append(("", []))
                words[-1][1].append(part)
    lines: list[list[Piece]] = []
    for space, word in words:
        if not word:  # spaces at the very end
            continue
        if lines and pieces_width([*lines[-1], space, *word], size) <= width:
            lines[-1] += [space, *word]
        else:
            lines.append(list(word))
    return [merge_pieces(line) for line in lines]


def text_width(text: str, size: float, blank_side: float | None = None) -> float:
    """
    Return the width of ``text`` as ``draw_text`` draws it, in ``FONT`` at ``size``.

    Each ``BLANK`` and ``CIRCLE`` counts as the width of its square or circle rather than of the
    narrower □ or ○ glyph that ``stringWidth`` would measure.
    """
    pieces = _BLANKS.split(text)
    blanks = sum(1 for piece in pieces if piece in (BLANK, CIRCLE))
    widths = sum(stringWidth(piece, FONT, size) for piece in pieces if piece not in (BLANK, CIRCLE))
    return float(widths) + blanks * _square_side(size, blank_side)


def fit_font(pdf: Canvas, text: str, font: str, size: float, width: float) -> None:
    """
    Set ``font`` at ``size``, or if ``text`` is wider than ``width`` at that size, at the largest
    smaller size in steps of 0.5 at which it fits, down to ``SMALLEST_FIT_SIZE``.
    """
    while size > SMALLEST_FIT_SIZE and stringWidth(text, font, size) > width:
        size -= 0.5
    pdf.setFont(font, size)


def _square_side(size: float, blank_side: float | None) -> float:
    """Return the side of a ``BLANK``'s square: ``blank_side`` if given, else 1.4 times ``size``."""
    return blank_side or size * 1.4


def wrap(text: str, size: float, width: float, sums: bool = True) -> list[str]:
    """
    Split ``text`` into lines no wider than ``width``, as far as its words allow.

    With ``sums``, a sum, such as expanded form or expanded notation, breaks after a "+", so
    each line ends with its "+" and every term stays whole; without, a "+" is a word like any
    other, for text such as "2 + 8 should be simplified first". A term too long for a line,
    such as a number in word form before an "=", breaks between words, as does text that is not
    a sum. A bracketed term, such as (3 x 10,000), counts as one word. Lines are measured as
    drawn, including any trailing "+", and spacing within a line is preserved.
    """

    def fits(line: str) -> bool:
        return text_width(line, size) <= width

    if not sums:
        return _wrap_words(text, fits)
    *before_plus, last = text.split(" + ")
    lines: list[str] = []
    for term in [*(term + " +" for term in before_plus), last]:
        if lines and fits(lines[-1] + " " + term):
            lines[-1] += " " + term
        elif fits(term):
            lines.append(term)
        else:
            # too long for a line of its own: wrap its words, starting on the current line
            start = lines.pop() + " " + term if lines else term
            lines += _wrap_words(start, fits)
    return lines


def _wrap_words(text: str, fits: Callable[[str], bool]) -> list[str]:
    """Split ``text`` between words, fitting as many words on each line as ``fits`` allows."""
    (_, first), *rest = _WORD.findall(text)
    lines = [first]
    for space, word in rest:
        if fits(lines[-1] + space + word):
            lines[-1] += space + word
        else:
            lines.append(word)
    return lines


def new_pdf(path: str | BinaryIO, title: str) -> Canvas:
    """
    Create a letter-size PDF canvas titled ``title`` that writes to ``path``.

    ``path`` is a filename or a binary file-like object.
    """
    pdf = Canvas(path, pagesize=letter)
    pdf.setTitle(title)
    return pdf


@dataclass(frozen=True)
class Header:
    """
    What ``start_page`` draws on each page: ``title`` at the top, the Name/Date line below it
    when ``name_line`` is set, and ``label`` in the footer, opposite ``copyright_notice()``.
    """

    title: str
    label: str
    name_line: bool


def copyright_notice() -> str:
    """Dated the year sheet is generated."""
    return f"© {date.today().year} toonarmycaptain.com"


def start_page(pdf: Canvas, header: Header) -> float:
    """
    Draw a new page's header and footer, and return the y at which content starts: one
    ``HEADER_ROW`` below the last header line, so content moves up when there is no Name/Date line.
    """
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 18)
    pdf.drawString(MARGIN, PAGE_HEIGHT - MARGIN, header.title)
    y = PAGE_HEIGHT - MARGIN - HEADER_ROW
    if header.name_line:
        pdf.setFont(FONT, TEXT_SIZE)
        pdf.drawString(MARGIN, y, "Name: " + "_" * 28)
        pdf.drawString(PAGE_WIDTH / 2 + 40, y, "Date: " + "_" * 16)
        y -= HEADER_ROW
    pdf.setFont(FONT, 9)
    pdf.setFillColor(gray)
    pdf.drawString(MARGIN, MARGIN / 2, header.label)
    pdf.drawRightString(PAGE_WIDTH - MARGIN, MARGIN / 2, copyright_notice())
    pdf.setFillColor("black")
    return y


def make_room(pdf: Canvas, header: Header, y: float, height: float) -> float:
    """
    Return the baseline to draw something ``height`` high from: ``y`` if it fits above the
    bottom margin, and otherwise the first baseline of a new page.
    """
    if y - height < MARGIN:
        pdf.showPage()
        return start_page(pdf, header)
    return y


def draw_numbered_lines(pdf: Canvas, number: int, lines: Iterable[str], y: float) -> float:
    """
    Draw a problem's ``number`` at the margin and its ``lines`` beside it, one under another from
    baseline ``y``, and return the baseline below the last line.
    """
    pdf.setFont(FONT, TEXT_SIZE)
    pdf.drawString(MARGIN, y, f"{number}.")
    for line in lines:
        pdf.drawString(MARGIN + TEXT_INDENT, y, line)
        y -= LINE_HEIGHT
    return y


def choice_label(index: int) -> str:
    """Return the label of a multiple-choice option at ``index``: "A)", "B)" and so on."""
    return f"{ascii_uppercase[index]})"


def correct_letters(response: MultipleChoice[Any]) -> str:
    """Return the correct options' letters, as an answer key gives them: "B", or "A, C"."""
    return ", ".join(ascii_uppercase[index] for index in sorted(response.correct_indexes))


def draw_instruction(pdf: Canvas, text: str, y: float) -> float:
    """
    Draw a sheet's instruction from baseline ``y``, rendering each ``BLANK`` as an empty square,
    and return the first problem's baseline. A newline in ``text`` starts a new line.
    """
    pdf.setFont(FONT, INSTRUCTION_SIZE)
    for paragraph in text.split("\n"):
        for line in wrap(paragraph, INSTRUCTION_SIZE, CONTENT_WIDTH):
            draw_text(pdf, MARGIN, y, line, INSTRUCTION_SIZE)
            y -= INSTRUCTION_LINE_HEIGHT
    return y - INSTRUCTION_GAP


def draw_answer_key(
    pdf: Canvas, header: Header, solutions: Iterable[str | Pieces], sums: bool = True
) -> None:
    """
    Draw the answer key, starting on a new page, with each solution numbered and wrapped: text as
    ``wrap`` does with ``sums``, and written maths as ``wrap_pieces`` does, each fraction in its
    style, a line with a stacked fraction given room above and below.

    A newline in a text solution starts a new line. A solution that would run past the bottom
    margin starts on the next page.
    """
    key_header = replace(header, title=f"{header.title}: Answer Key", name_line=False)
    pdf.showPage()
    y = start_page(pdf, key_header)
    for number, solution in enumerate(solutions, start=1):
        lines: list[str | Pieces]
        if isinstance(solution, str):
            lines = [
                line
                for row in solution.split("\n")
                for line in wrap(row, TEXT_SIZE, TEXT_WIDTH, sums)
            ]
        else:
            lines = list(wrap_pieces(solution, TEXT_SIZE, TEXT_WIDTH))
        rooms = [
            FRACTION_ROOM if not isinstance(line, str) and any(map(stacked, line)) else 0
            for line in lines
        ]
        if y - (len(lines) - 1) * LINE_HEIGHT - 2 * sum(rooms) < MARGIN + LINE_HEIGHT:
            pdf.showPage()
            y = start_page(pdf, key_header)
        pdf.setFont(FONT, TEXT_SIZE)
        for index, (line, room) in enumerate(zip(lines, rooms, strict=True)):
            y -= room
            if index == 0:
                pdf.drawString(MARGIN, y, f"{number}.")
            if isinstance(line, str):
                pdf.drawString(MARGIN + TEXT_INDENT, y, line)
            else:
                draw_pieces(pdf, MARGIN + TEXT_INDENT, y, line, TEXT_SIZE)
            y -= LINE_HEIGHT + room
