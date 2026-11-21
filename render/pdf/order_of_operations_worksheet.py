"""
PDF worksheets of order of operations questions, with an optional answer key page.

Each problem is its number and question, then what it shows: the expression, an expression
equal to a step with a box, or a worked simplification's lines; then what the student answers
on:
- lettered choices: values or expressions in a row when every one fits its share of the width,
  else one under another; sentences one under another, wrapped;
- expressions to circle, or to count, without letters, laid out as choices are;
- answer lines: one, or two to explain.

Expressions are drawn with their fractions stacked. A sheet for the self-check tiles case has no
choices or answer lines, and ends with a page for the answer bank and pattern. A problem that
would run past the bottom margin starts on the next page.
"""

from collections.abc import Sequence
from fractions import Fraction
from typing import BinaryIO

from reportlab.pdfgen.canvas import Canvas

from core.order_of_operations.data import (
    FindErrorQuestionData,
    FirstOperationQuestionData,
    FirstResultQuestionData,
    OrderOfOperationsQuestion,
    ParenthesesQuestionData,
    StepBlankQuestionData,
    ValueCountQuestionData,
    ValueQuestionData,
)
from core.order_of_operations.representation import (
    TileQuestionData,
    circled,
    option_pieces,
    order_of_operations_tile_question,
    question,
    shown_lines,
    solution,
    tile_answer_pieces,
)
from core.question import FreeResponse, MultipleChoice
from core.written_numbers import Pieces
from render.pdf.page import (
    BOLD_FONT,
    CONTENT_WIDTH,
    FONT,
    FRACTION_ROOM,
    MARGIN,
    Header,
    choice_label,
    correct_letters,
    draw_answer_key,
    draw_fraction,
    draw_text,
    fraction_width,
    make_room,
    new_pdf,
    start_page,
    text_width,
    wrap,
)
from render.pdf.tiles import draw_tiles_page, tile_solutions

QUESTION_SIZE = 12  # every problem's text and its choices
QUESTION_LINE_HEIGHT = 15
EXPRESSION_SIZE = 13  # the expressions and steps shown under a question
EXPRESSION_LINE_HEIGHT = 20
DESCENT = 5  # from a line's baseline down to the bottom of its space
NUMBER_WIDTH = 24  # from a problem's number to its text
TEXT_WIDTH = CONTENT_WIDTH - NUMBER_WIDTH
EXPRESSION_INDENT = 16  # the expression shown, past the question's text
BELOW_GAP = 10  # from the question's last line down to the top of what is under it
PROBLEM_GAP = 26  # from the bottom of a problem down to the next problem's baseline

LETTER_WIDTH = 24  # room for "A)" left of each choice
CHOICE_MARGIN = 16  # the least gap between a choice in a row and the next choice's letter
CHOICE_GAP = 6  # between two choices one under another

ANSWER_LINE_DROP = 24  # from the top of an answer line's space down to the line
ANSWER_LINE_GAP = 26  # between two answer lines
EXPLAIN_LINES = 2  # to give an operation, a statement or a step and say why


def render_order_of_operations_worksheet(
    questions: Sequence[OrderOfOperationsQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    slot_of: Sequence[int] | None,
) -> None:
    """
    Render order of operations problems, and the answer key if requested, to ``path``.

    The answer key gives each problem's answer, after the correct letters for lettered choices,
    with the working that shows it where it helps. ``path`` is a filename or a binary file-like
    object.

    With ``slot_of``, the sheet is for the self-check tiles case: the questions must all be
    written tiles forms (see ``core.order_of_operations.generator``), with different answers,
    and the answer bank and pattern follow on a page of their own. ``slot_of[i]`` is the slot of
    question i + 1's answer, as in ``core.self_check_tiles``, so there are at most 12 questions.
    The answer key adds each answer's slot letter.
    """
    pdf = new_pdf(path, header.title)
    y = start_page(pdf, header)
    for number, each in enumerate(questions, start=1):
        y = _draw_problem(pdf, header, number, each, slot_of is not None, y)

    if slot_of is None:
        solutions = [_solution(each) for each in questions]
    else:
        tile_data = [_tile_data(each) for each in questions]
        answers = [tile_answer_pieces(data) for data in tile_data]
        draw_tiles_page(pdf, header, answers, slot_of)
        tile_questions = [order_of_operations_tile_question(data) for data in tile_data]
        solutions = tile_solutions(tile_questions, slot_of)
    if answer_key:
        # expressions and sentences, not sums to break after each +
        draw_answer_key(pdf, header, solutions, sums=False)

    pdf.save()


def _tile_data(each: OrderOfOperationsQuestion) -> TileQuestionData:
    """
    Return a tiles sheet's question's data. Raises ``ValueError`` for a question with no tiles
    form.
    """
    data = each.data
    forms = (
        ValueQuestionData,
        StepBlankQuestionData,
        ValueCountQuestionData,
        FirstResultQuestionData,
    )
    if isinstance(data, forms) and isinstance(each.response, FreeResponse):
        return data
    raise ValueError("A self-check tiles sheet asks only written tiles forms.")


def _solution(each: OrderOfOperationsQuestion) -> str:
    """Return the answer key's entry, after the correct letters for lettered choices."""
    entry = solution(each.data)
    if isinstance(each.response, MultipleChoice):
        return f"{correct_letters(each.response)}) {entry}"
    return entry


def _draw_problem(
    pdf: Canvas,
    header: Header,
    number: int,
    each: OrderOfOperationsQuestion,
    tiles: bool,
    y: float,
) -> float:
    """
    Draw a problem from baseline ``y``, moving to a new page first if it won't fit, and return
    the next problem's baseline. On a tiles sheet, ``tiles``, it has no choices or answer lines.
    """
    data = each.data
    response = each.response
    choices = isinstance(response, MultipleChoice)
    lines = wrap(question(data, choices), QUESTION_SIZE, TEXT_WIDTH, sums=False)
    shown = shown_lines(data)
    options = (
        [option_pieces(data, option) for option in response.options]
        if isinstance(response, MultipleChoice)
        else circled(data, choices)
    )
    answer_lines = 0 if tiles or options else _answer_lines(each)
    shown_height = sum(_line_height(line) for line in shown)
    below = _options_height(options) + answer_lines * ANSWER_LINE_GAP
    height = (len(lines) - 1) * QUESTION_LINE_HEIGHT + shown_height + BELOW_GAP + below
    y = make_room(pdf, header, y, height)
    pdf.setFillColor("black")
    pdf.setFont(FONT, QUESTION_SIZE)
    pdf.drawString(MARGIN, y, f"{number}.")
    left = MARGIN + NUMBER_WIDTH
    for line in lines:
        pdf.drawString(left, y, line)
        y -= QUESTION_LINE_HEIGHT
    # below the last line's baseline, leaving room for its descenders
    top = y + QUESTION_LINE_HEIGHT - BELOW_GAP
    for pieces in shown:
        line_height = _line_height(pieces)
        baseline = top - line_height + DESCENT + (FRACTION_ROOM if _stacked(pieces) else 0)
        _draw_pieces(pdf, left + EXPRESSION_INDENT, baseline, pieces, EXPRESSION_SIZE)
        top -= line_height
    if options:
        _draw_options(pdf, options, left, top, lettered=choices)
    for index in range(answer_lines):
        line_y = top - ANSWER_LINE_DROP - index * ANSWER_LINE_GAP
        pdf.line(left, line_y, left + TEXT_WIDTH, line_y)
    return top - below - PROBLEM_GAP


def _answer_lines(each: OrderOfOperationsQuestion) -> int:
    """Return how many answer lines a written problem has: two to explain, else one."""
    explained = (FirstOperationQuestionData, ParenthesesQuestionData, FindErrorQuestionData)
    return EXPLAIN_LINES if isinstance(each.data, explained) else 1


def _stacked(pieces: Pieces) -> bool:
    """Return whether ``pieces`` has a stacked fraction."""
    return any(isinstance(piece, Fraction) for piece in pieces)


def _line_height(pieces: Pieces) -> float:
    """Return the height of a line of an expression, taller with a stacked fraction."""
    return EXPRESSION_LINE_HEIGHT + (2 * FRACTION_ROOM if _stacked(pieces) else 0)


def _pieces_width(pieces: Pieces, size: float) -> float:
    """Return the width ``_draw_pieces`` takes for ``pieces`` at ``size``."""
    return sum(
        fraction_width(piece, size) if isinstance(piece, Fraction) else text_width(piece, size)
        for piece in pieces
    )


def _draw_pieces(pdf: Canvas, x: float, y: float, pieces: Pieces, size: float) -> float:
    """
    Draw ``pieces`` from ``x`` on baseline ``y`` at ``size``: text with each ``BLANK`` as a box,
    and fractions stacked. Return the x after them.
    """
    pdf.setFont(FONT, size)
    for piece in pieces:
        if isinstance(piece, Fraction):
            x = draw_fraction(pdf, x, y, piece, size)
        else:
            draw_text(pdf, x, y, piece, size)
            x += text_width(piece, size)
    return x


def _in_a_row(options: Sequence[Pieces]) -> bool:
    """Return whether every option fits its share of the width, beside its letter."""
    share = TEXT_WIDTH / len(options)
    room = share - LETTER_WIDTH - CHOICE_MARGIN
    return all(_pieces_width(option, QUESTION_SIZE) <= room for option in options)


def _option_lines(option: Pieces) -> list[Pieces]:
    """Return an option's lines one under another: a sentence wrapped, else one line."""
    if len(option) == 1 and isinstance(option[0], str):
        width = TEXT_WIDTH - LETTER_WIDTH
        return [(line,) for line in wrap(option[0], QUESTION_SIZE, width, sums=False)]
    return [option]


def _option_line_height(line: Pieces) -> float:
    """Return the height of a line of an option, taller with a stacked fraction."""
    return QUESTION_LINE_HEIGHT + (2 * FRACTION_ROOM if _stacked(line) else 0)


def _options_height(options: Sequence[Pieces]) -> float:
    """Return the height of the options, in a row or one under another."""
    if not options:
        return 0
    if _in_a_row(options):
        return max(_option_line_height(option) for option in options)
    heights = [
        sum(_option_line_height(line) for line in _option_lines(option)) for option in options
    ]
    return sum(heights) + (len(options) - 1) * CHOICE_GAP


def _draw_options(
    pdf: Canvas, options: Sequence[Pieces], left: float, top: float, lettered: bool
) -> None:
    """
    Draw the options from ``top`` down, lettered with ``lettered``: in a row, each in an equal
    share of the width, when every one fits, else one under another, a sentence wrapped beside
    its letter.
    """
    if _in_a_row(options):
        share = TEXT_WIDTH / len(options)
        stacked = any(_stacked(option) for option in options)
        height = max(_option_line_height(option) for option in options)
        baseline = top - height + DESCENT + (FRACTION_ROOM if stacked else 0)
        for index, option in enumerate(options):
            x = left + index * share
            if lettered:
                pdf.setFont(BOLD_FONT, QUESTION_SIZE)
                pdf.drawString(x, baseline, choice_label(index))
            _draw_pieces(pdf, x + LETTER_WIDTH, baseline, option, QUESTION_SIZE)
        return
    y = top
    for index, option in enumerate(options):
        for line_index, line in enumerate(_option_lines(option)):
            height = _option_line_height(line)
            baseline = y - height + DESCENT + (FRACTION_ROOM if _stacked(line) else 0)
            if lettered and line_index == 0:
                pdf.setFont(BOLD_FONT, QUESTION_SIZE)
                pdf.drawString(left, baseline, choice_label(index))
            _draw_pieces(pdf, left + LETTER_WIDTH, baseline, line, QUESTION_SIZE)
            y -= height
        y -= CHOICE_GAP
