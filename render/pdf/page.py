"""
Page layout shared by every PDF worksheet.

Defines the page geometry and fonts, and draws the header and footer, wrapped text and the
answer key pages.
"""

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from typing import BinaryIO

from reportlab.lib.colors import gray
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.question import BLANK

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 54
TEXT_INDENT = 28  # question text is indented past its number
TEXT_WIDTH = PAGE_WIDTH - 2 * MARGIN - TEXT_INDENT
FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"
TEXT_SIZE = 14
LINE_HEIGHT = 20
FIRST_LINE_Y: float = PAGE_HEIGHT - MARGIN - 60

# A word with its preceding whitespace. A bracketed term, such as (3 x 10,000), is one word.
_WORD = re.compile(r"(\s*)(\([^)]*\)|\S+)")


def draw_text(
    pdf: Canvas, x: float, y: float, text: str, size: float, blank_side: float | None = None
) -> None:
    """
    Draw ``text`` from ``x`` along baseline ``y``, rendering each ``BLANK`` as an empty square.

    Like ``drawString``, it uses the current font, which must be ``FONT`` at ``size``.
    Helvetica has no square glyph, so each square is drawn as a box ``blank_side`` wide and high
    (1.4 times ``size`` by default), centred on the middle of a digit.
    """
    side = _square_side(size, blank_side)
    middle = y + size * 0.35  # about halfway up a digit
    first, *rest = text.split(BLANK)
    pdf.drawString(x, y, first)
    x += stringWidth(first, FONT, size)
    for piece in rest:
        pdf.rect(x, middle - side / 2, side, side, stroke=1, fill=0)
        x += side
        pdf.drawString(x, y, piece)
        x += stringWidth(piece, FONT, size)


def text_width(text: str, size: float, blank_side: float | None = None) -> float:
    """
    Return the width of ``text`` as ``draw_text`` draws it, in ``FONT`` at ``size``.

    Each ``BLANK`` counts as the width of its square rather than of the narrower □ glyph that
    ``stringWidth`` would measure.
    """
    pieces = text.split(BLANK)
    widths = sum(stringWidth(piece, FONT, size) for piece in pieces)
    return float(widths) + (len(pieces) - 1) * _square_side(size, blank_side)


def _square_side(size: float, blank_side: float | None) -> float:
    """Return the side of a ``BLANK``'s square: ``blank_side`` if given, else 1.4 times ``size``."""
    return blank_side or size * 1.4


def wrap(text: str, size: float, width: float) -> list[str]:
    """
    Split ``text`` into lines no wider than ``width``, as far as its words allow.

    A sum, such as expanded form or expanded notation, breaks after a "+", so each line ends
    with its "+" and every term stays whole. A term too long for a line, such as a number in
    word form before an "=", breaks between words, as does text that is not a sum. A bracketed
    term, such as (3 x 10,000), counts as one word. Lines are measured as drawn, including any
    trailing "+", and spacing within a line is preserved.
    """

    def fits(line: str) -> bool:
        return text_width(line, size) <= width

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
    when ``name_line`` is set, and ``label`` in the footer.
    """

    title: str
    label: str
    name_line: bool


def start_page(pdf: Canvas, header: Header) -> float:
    """Draw a new page's header and footer, and return the y at which content starts."""
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 18)
    pdf.drawString(MARGIN, PAGE_HEIGHT - MARGIN, header.title)
    if header.name_line:
        pdf.setFont(FONT, TEXT_SIZE)
        pdf.drawString(MARGIN, PAGE_HEIGHT - MARGIN - 30, "Name: " + "_" * 28)
        pdf.drawString(PAGE_WIDTH / 2 + 40, PAGE_HEIGHT - MARGIN - 30, "Date: " + "_" * 16)
    pdf.setFont(FONT, 9)
    pdf.setFillColor(gray)
    pdf.drawString(MARGIN, MARGIN / 2, header.label)
    pdf.setFillColor("black")
    return FIRST_LINE_Y


def draw_answer_key(pdf: Canvas, header: Header, solutions: Iterable[str]) -> None:
    """
    Draw the answer key, starting on a new page, with each solution numbered and wrapped.

    A solution that would run past the bottom margin starts on the next page.
    """
    key_header = replace(header, title=f"{header.title}: Answer Key", name_line=False)
    pdf.showPage()
    y = start_page(pdf, key_header)
    for number, solution in enumerate(solutions, start=1):
        lines = wrap(solution, TEXT_SIZE, TEXT_WIDTH)
        if y - (len(lines) - 1) * LINE_HEIGHT < MARGIN + LINE_HEIGHT:
            pdf.showPage()
            y = start_page(pdf, key_header)
        pdf.setFont(FONT, TEXT_SIZE)
        pdf.drawString(MARGIN, y, f"{number}.")
        for line in lines:
            pdf.drawString(MARGIN + TEXT_INDENT, y, line)
            y -= LINE_HEIGHT
