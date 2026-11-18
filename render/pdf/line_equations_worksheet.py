"""
PDF worksheets of questions about lines, with an optional answer key page.

Each question asks for a feature of a line, such as its slope, or its equation in a form, with the
line shown under it as an equation, two points, or a point and slope, or the line it's parallel
or perpendicular to. Below that come an answer line, two labelled blanks for the slope and
y-intercept, lettered choices, or, for the self-check tiles case, nothing: the answer bank and
pattern follow on a page of their own. Fractions are drawn stacked, as STAAR prints them,
since an inline fraction such as -3/4x is ambiguous.
"""

from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction
from string import ascii_uppercase
from typing import BinaryIO

from reportlab.pdfgen.canvas import Canvas

from core.line_equations.data import LineFeature, LineQuestion
from core.line_equations.representation import (
    Pieces,
    answer_pieces,
    choice_pieces,
    given_pieces,
    instruction,
    tile_answer_pieces,
)
from core.question import MultipleChoice
from render.pdf.page import (
    FONT,
    FRACTION_ROOM,
    LINE_HEIGHT,
    MARGIN,
    TEXT_INDENT,
    TEXT_SIZE,
    TEXT_WIDTH,
    Header,
    choice_label,
    correct_letters,
    draw_numbered_lines,
    draw_pieces,
    make_room,
    new_pdf,
    pieces_width,
    start_page,
    wrap,
)
from render.pdf.tiles import draw_tiles_page

ANSWER_LINE_DROP = 14  # offset of the answer line below the next text baseline
ANSWER_HEIGHT = 38  # answer line plus the gap below it, as on the place-value sheet
CHOICE_INDENT = 22  # offset of a choice from its letter
CHOICE_COLUMNS = 4  # choices that fit go in a row, each in a quarter of the width
CHOICE_MARGIN = 18  # the least gap between a choice in a row and the next choice's letter
CHOICES_GAP = 18  # gap between a question's choices and the next question
TILES_GAP = 14  # gap between questions on a self-check tiles sheet, which has no answer lines
# the two blanks of a slope and y-intercept question, under the line, with room to write
BLANKS = ("Slope: ______________", "y-intercept: ______________")
BLANKS_DROP = 24  # from the line's baseline down to the blanks'
BLANKS_HEIGHT = 52  # the blanks plus the gap below them


def render_line_equations_worksheet(
    questions: Sequence[LineQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    slot_of: Sequence[int] | None = None,
) -> None:
    """
    Render questions about lines, and the answer key if requested, to ``path``.

    Each question states what to find, with the line on its own line below it. A free-response
    question has an answer line, or for the slope and y-intercept, two labelled blanks. A
    multiple-choice question has its lettered choices in a row when every one fits a quarter of
    the width with room to spare, such as numbers, points and short equations, and otherwise one
    under another, such as statements.
    A question that would run past the bottom margin starts on the next page.

    With ``slot_of``, the sheet is for the self-check tiles case: the questions have no answer
    lines, and the answer bank and pattern follow on a page of their own. The answers must be
    distinct. ``slot_of[i]`` is the slot of question i + 1's answer, as in
    ``core.self_check_tiles``, so there are at most 12 questions.

    The answer key gives each answer: a number, "undefined", an ordered pair, the slope and
    y-intercept, or an equation, after the correct letter for a multiple-choice question, and
    followed by its slot letter on a tiles sheet. ``path`` is a filename or a binary file-like
    object.
    """
    pdf = new_pdf(path, header.title)

    y = start_page(pdf, header)
    for number, question in enumerate(questions, start=1):
        lines = wrap(instruction(question.data), TEXT_SIZE, TEXT_WIDTH)
        given = given_pieces(question.data)
        below = _below(question, tiles=slot_of is not None)
        height = (len(lines) + 1) * LINE_HEIGHT + 2 * _room(given) + _height(below)
        y = make_room(pdf, header, y, height)
        y = draw_numbered_lines(pdf, number, lines, y) - _room(given)
        draw_pieces(pdf, MARGIN + TEXT_INDENT, y, given, TEXT_SIZE)
        y -= LINE_HEIGHT + _room(given)
        y = _draw_below(pdf, below, y)

    if slot_of is None:
        solutions = [_solution(question) for question in questions]
    else:
        draw_tiles_page(
            pdf, header, [tile_answer_pieces(question.data) for question in questions], slot_of
        )
        solutions = [
            (*answer_pieces(question.data), f"    ({ascii_uppercase[slot]})")
            for question, slot in zip(questions, slot_of, strict=True)
        ]
    if answer_key:
        _draw_answer_key(pdf, header, solutions)

    pdf.save()


# What goes under a question's line: "tiles" (nothing), "line", "blanks", or its choices in a
# "row" or a "column", each choice as (letter, pieces)
type Below = tuple[str, list[tuple[str, Pieces]]]


def _below(question: LineQuestion, tiles: bool) -> Below:
    """Return what goes under the question's line, as ``render_line_equations_worksheet`` says."""
    response = question.response
    if isinstance(response, MultipleChoice):
        choices = [
            (choice_label(index), choice_pieces(question.data, option))
            for index, option in enumerate(response.options)
        ]
        room = TEXT_WIDTH / CHOICE_COLUMNS - CHOICE_INDENT - CHOICE_MARGIN
        fits = all(pieces_width(pieces, TEXT_SIZE) <= room for _, pieces in choices)
        return ("row" if fits else "column", choices)
    if tiles:
        return ("tiles", [])
    if question.data.asked is LineFeature.SLOPE_AND_Y_INTERCEPT:
        return ("blanks", [])
    return ("line", [])


def _height(below: Below) -> float:
    """Return the height of what goes under a question's line, with the gap after it."""
    kind, choices = below
    match kind:
        case "tiles":
            return TILES_GAP
        case "blanks":
            return BLANKS_HEIGHT
        case "row":
            return LINE_HEIGHT + 2 * max(_room(pieces) for _, pieces in choices) + CHOICES_GAP
        case "column":
            return sum(LINE_HEIGHT + 2 * _room(pieces) for _, pieces in choices) + CHOICES_GAP
        case _:
            return ANSWER_HEIGHT


def _draw_below(pdf: Canvas, below: Below, y: float) -> float:
    """Draw what goes under a question's line from baseline ``y``, and return the y below it."""
    left = MARGIN + TEXT_INDENT
    kind, choices = below
    match kind:
        case "tiles":
            return y - TILES_GAP
        case "blanks":
            pdf.setFont(FONT, TEXT_SIZE)
            pdf.drawString(left, y - BLANKS_DROP, BLANKS[0])
            pdf.drawString(left + TEXT_WIDTH / 2, y - BLANKS_DROP, BLANKS[1])
            return y - BLANKS_HEIGHT
        case "row":
            room = max(_room(pieces) for _, pieces in choices)
            y -= room
            for column, (letter, pieces) in enumerate(choices):
                _draw_choice(pdf, left + column * TEXT_WIDTH / CHOICE_COLUMNS, y, letter, pieces)
            return y - LINE_HEIGHT - room - CHOICES_GAP
        case "column":
            for letter, pieces in choices:
                y -= _room(pieces)
                _draw_choice(pdf, left, y, letter, pieces)
                y -= LINE_HEIGHT + _room(pieces)
            return y - CHOICES_GAP
        case _:
            line_y = y - ANSWER_LINE_DROP
            pdf.line(left, line_y, left + TEXT_WIDTH, line_y)
            return y - ANSWER_HEIGHT


def _draw_choice(pdf: Canvas, x: float, y: float, letter: str, pieces: Pieces) -> None:
    """Draw a choice's letter at ``x`` and the choice beside it, on baseline ``y``."""
    pdf.setFont(FONT, TEXT_SIZE)
    pdf.drawString(x, y, letter)
    draw_pieces(pdf, x + CHOICE_INDENT, y, pieces, TEXT_SIZE)


def _solution(question: LineQuestion) -> Pieces:
    """Return the question's answer for the key, after its letter if it's multiple choice."""
    response = question.response
    if isinstance(response, MultipleChoice):
        (correct,) = response.correct_indexes
        option = choice_pieces(question.data, response.options[correct])
        return (f"{correct_letters(response)}) ", *option)
    return answer_pieces(question.data)


def _room(pieces: Pieces) -> float:
    """Return the extra space a line of ``pieces`` needs above and below: some for a fraction."""
    return FRACTION_ROOM if any(isinstance(piece, Fraction) for piece in pieces) else 0


def _draw_answer_key(pdf: Canvas, header: Header, solutions: Sequence[Pieces]) -> None:
    """
    Draw the answer key, starting on a new page, with each solution numbered, as
    ``draw_answer_key`` does for text, its fractions stacked. A solution that would run past the
    bottom margin starts on the next page.
    """
    key_header = replace(header, title=f"{header.title}: Answer Key", name_line=False)
    pdf.showPage()
    y = start_page(pdf, key_header)
    for number, solution in enumerate(solutions, start=1):
        room = _room(solution)
        if y - 2 * room < MARGIN + LINE_HEIGHT:
            pdf.showPage()
            y = start_page(pdf, key_header)
        y -= room
        pdf.setFont(FONT, TEXT_SIZE)
        pdf.drawString(MARGIN, y, f"{number}.")
        draw_pieces(pdf, MARGIN + TEXT_INDENT, y, solution, TEXT_SIZE)
        y -= LINE_HEIGHT + room
