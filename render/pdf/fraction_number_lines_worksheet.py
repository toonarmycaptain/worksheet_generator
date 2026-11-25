"""
PDF worksheets of fractions on a number line questions, with an optional answer key page.

Naming and marking points go two to a row, in columns, when two come together; distance stories,
dividing a line and comparing distances take the page's width. Each problem is its number and
question, then its number line, then what the student answers on: lettered choices, lettered
lines one under another, or an answer line, followed by the unit for a distance. A line to mark,
divide or mark two points on is where the student answers, and "Which point shows 3/8?" letters
its points on the line itself.

A sheet for the self-check tiles case has no choices or answer lines, and ends with a page for
the answer bank, where a marking question's answer is a small line with its point, and the
pattern. A row of problems that would run past the bottom margin starts on the next page.
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from string import ascii_uppercase
from typing import BinaryIO

from reportlab.pdfgen.canvas import Canvas

from core.fraction_models.number_lines import FractionLine, LinePoint
from core.fraction_number_lines.data import (
    CompareQuestionData,
    Comparison,
    DistanceAsked,
    DistanceQuestionData,
    FractionNumberLinesQuestion,
    MarkPointQuestionData,
    NamePointQuestionData,
)
from core.fraction_number_lines.representation import (
    answer_unit,
    comparison_pieces,
    fraction_number_lines_tile_question,
    question,
    solution,
)
from core.question import FreeResponse, MultipleChoice
from core.written_numbers import Pieces, UnreducedFraction
from render.pdf.graphics.fractions import (
    COLOUR_FRACTIONS,
    GREY_FRACTIONS,
    FractionColours,
    draw_fraction_line,
    fraction_line_drop,
    fraction_line_height,
)
from render.pdf.page import (
    BOLD_FONT,
    CONTENT_WIDTH,
    FONT,
    FRACTION_ROOM,
    MARGIN,
    TEXT_SIZE,
    Header,
    choice_label,
    correct_letters,
    draw_answer_key,
    draw_pieces,
    new_pdf,
    pieces_width,
    stacked,
    start_page,
    wrap_pieces,
)
from render.pdf.tiles import BOX_WIDTH, BankAnswer, BankPicture, draw_tiles_page

QUESTION_SIZE = 12  # every problem's text and its choices
LINE_GAP = 3  # between two lines of a problem's text
NUMBER_WIDTH = 24  # from a problem's number to its text
COLUMN_GAP = 18
COLUMN_WIDTH = (CONTENT_WIDTH - COLUMN_GAP) / 2
BELOW_GAP = 8  # from a problem's text to its line, and from that to its choices
ROW_GAP = 22  # from the bottom of a row of problems to the top of the next

LETTER_WIDTH = 24  # room for "A)" left of each choice
CHOICE_GAP = 12  # between two choices in a row
CHOICE_ROW_HEIGHT = QUESTION_SIZE + LINE_GAP  # a row of lettered choices without stacked fractions
LINE_CHOICE_GAP = 10  # between two lines to choose from, one under the other
ANSWER_LINE_DROP = 28  # from the top of an answer line's space down to the line
ANSWER_LINE_LENGTH = 110
UNIT_GAP = 4  # from the end of an answer line to its unit
BANK_LINE_WIDTH = BOX_WIDTH - 6  # a line in a tiles answer bank's box, nearly as wide as the box


@dataclass(frozen=True)
class _Block:
    """A problem as laid out: its text's lines, its number line, and what the student answers
    on."""

    lines: list[Pieces]
    line: FractionLine | None
    choices: tuple[Pieces, ...]  # lettered choices, written, from the first letter
    first_letter: int  # the index of the first written choice's letter: after a line's points
    lines_to_choose: tuple[FractionLine, ...]  # lettered lines, one under another
    answer_line: bool
    unit: str | None  # written after the answer line
    wide: bool  # whether it takes the page's width, not a column


def render_fraction_number_lines_worksheet(
    questions: Sequence[FractionNumberLinesQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    slot_of: Sequence[int] | None,
    black_and_white: bool = False,
) -> None:
    """
    Render fractions on a number line problems, and the answer key if requested, to ``path``,
    with jumps, arrows and stars in blue, or grey with ``black_and_white``.

    The answer key gives each problem's answer, after the correct letters for lettered choices,
    with how the line shows it, its fractions written as the problem writes them. ``path`` is a
    filename or a binary file-like object.

    With ``slot_of``, the sheet is for the self-check tiles case: the questions must be written,
    with different answers, as ``core.fraction_number_lines.generator`` makes them, and the
    answer bank and pattern follow on a page of their own. ``slot_of[i]`` is the slot of question
    i + 1's answer, as in ``core.self_check_tiles``, so there are at most 12 questions. The
    answer key adds each answer's slot letter.
    """
    colours = GREY_FRACTIONS if black_and_white else COLOUR_FRACTIONS
    tiles = slot_of is not None
    pdf = new_pdf(path, header.title)
    blocks = [_block(each, tiles) for each in questions]
    top = start_page(pdf, header) + QUESTION_SIZE
    for row in _rows(blocks):
        height = max(_height(block) for _, block in row)
        if top - height < MARGIN:
            pdf.showPage()
            top = start_page(pdf, header) + QUESTION_SIZE
        for column, (index, block) in enumerate(row):
            x = MARGIN + column * (COLUMN_WIDTH + COLUMN_GAP)
            _draw_block(pdf, index + 1, block, x, top, colours)
        top -= height + ROW_GAP

    solutions: list[str | Pieces] = [_solution(each) for each in questions]
    if slot_of is not None:
        tile_questions = [fraction_number_lines_tile_question(each.data) for each in questions]
        answers = [_bank_answer(each.answer, colours) for each in tile_questions]
        draw_tiles_page(pdf, header, answers, slot_of)
        solutions = [
            (*solution(each.data), f"    ({choice_label(slot)[0]})")
            for each, slot in zip(questions, slot_of, strict=True)
        ]
    if answer_key:
        draw_answer_key(pdf, header, solutions)
    pdf.save()


def _solution(each: FractionNumberLinesQuestion) -> Pieces:
    """Return the answer key's entry, after the correct letters for lettered choices."""
    entry = solution(each.data)
    if isinstance(each.response, MultipleChoice):
        return (f"{correct_letters(each.response)}) ", *entry)
    return entry


def _block(each: FractionNumberLinesQuestion, tiles: bool) -> _Block:
    """Lay out a problem: what it shows, and whether it's in a column or as wide as the page."""
    data, response = each.data, each.response
    choosing = isinstance(response, MultipleChoice)
    wide = not isinstance(data, NamePointQuestionData | MarkPointQuestionData)
    text_width = (CONTENT_WIDTH if wide else COLUMN_WIDTH) - NUMBER_WIDTH
    lines = wrap_pieces(question(data, choosing, tiles), QUESTION_SIZE, text_width)
    options = response.options if isinstance(response, MultipleChoice) else ()
    line: FractionLine | None = data.line
    choices: list[Pieces] = []
    first_letter = 0
    lines_to_choose: list[FractionLine] = []
    if isinstance(data, MarkPointQuestionData):
        if tiles:
            line = None
        elif options:
            # the points are lettered on the line, and "None of these" follows as a choice
            points = tuple(
                LinePoint(option * data.line.parts, ascii_uppercase[index])
                for index, option in enumerate(options)
                if isinstance(option, Fraction)
            )
            line = replace(data.line, points=points)
            first_letter = len(points)
            choices = [(option,) for option in options if isinstance(option, str)]
    else:
        for option in options:
            if isinstance(option, FractionLine):
                lines_to_choose.append(option)
            elif isinstance(option, Comparison):
                choices.append(comparison_pieces(option))
            elif isinstance(option, UnreducedFraction | str):
                choices.append((option,))
    if lines_to_choose:
        line = None  # the lines to choose from are the question's lines
    answer_line = isinstance(response, FreeResponse) and not tiles and _answers_on_a_line(each)
    return _Block(
        lines,
        line,
        tuple(choices),
        first_letter,
        tuple(lines_to_choose),
        answer_line,
        answer_unit(data) if answer_line else None,
        wide,
    )


def _answers_on_a_line(each: FractionNumberLinesQuestion) -> bool:
    """Return whether a written problem's answer goes on an answer line: a fraction or a name,
    not a point the student marks or a line the student divides."""
    data = each.data
    if isinstance(data, DistanceQuestionData):
        return data.asked is DistanceAsked.HOW_FAR
    return isinstance(data, NamePointQuestionData | CompareQuestionData)


def _rows(blocks: Sequence[_Block]) -> list[list[tuple[int, _Block]]]:
    """Return the problems by rows: two column problems side by side when they come together,
    else one to a row."""
    rows: list[list[tuple[int, _Block]]] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        if not block.wide and index + 1 < len(blocks) and not blocks[index + 1].wide:
            rows.append([(index, block), (index + 1, blocks[index + 1])])
            index += 2
        else:
            rows.append([(index, block)])
            index += 1
    return rows


def _text_width(block: _Block) -> float:
    """Return the width of a problem's text, beside its number."""
    return (CONTENT_WIDTH if block.wide else COLUMN_WIDTH) - NUMBER_WIDTH


def _room(line: Pieces) -> float:
    """Return the room a line of text needs above and below for a stacked fraction."""
    return FRACTION_ROOM * QUESTION_SIZE / TEXT_SIZE if any(map(stacked, line)) else 0


def _line_height(line: Pieces) -> float:
    """Return the height a line of a problem's text takes."""
    return QUESTION_SIZE + LINE_GAP + 2 * _room(line)


def _choices_per_row(block: _Block) -> int:
    """Return how many of a problem's written choices fit in a row: all four, two, or one."""
    widest = max(pieces_width(choice, QUESTION_SIZE) for choice in block.choices)
    return next(
        (
            per_row
            for per_row in (len(block.choices), 2)
            if LETTER_WIDTH + widest <= (_text_width(block) - (per_row - 1) * CHOICE_GAP) / per_row
        ),
        1,
    )


def _choice_rows(block: _Block) -> list[tuple[Pieces, ...]]:
    """Return a problem's written choices in rows."""
    per_row = _choices_per_row(block)
    return [
        block.choices[start : start + per_row] for start in range(0, len(block.choices), per_row)
    ]


def _choice_row_height(row: Sequence[Pieces]) -> float:
    """Return the height of a row of written choices."""
    return CHOICE_ROW_HEIGHT + 2 * max(_room(choice) for choice in row)


def _height(block: _Block) -> float:
    """Return the height a problem takes, from the top of its first line."""
    height = sum(_line_height(line) for line in block.lines)
    if block.line is not None:
        height += BELOW_GAP + fraction_line_height(block.line)
    if block.choices:
        height += BELOW_GAP + sum(_choice_row_height(row) for row in _choice_rows(block))
    if block.lines_to_choose:
        height += BELOW_GAP + _lines_to_choose_height(block.lines_to_choose)
    if block.answer_line:
        height += ANSWER_LINE_DROP
    return height


def _lines_to_choose_height(lines: Sequence[FractionLine]) -> float:
    """Return the height of lines to choose from, one under another."""
    return sum(fraction_line_height(each) for each in lines) + (len(lines) - 1) * LINE_CHOICE_GAP


def _draw_block(
    pdf: Canvas, number: int, block: _Block, x: float, top: float, colours: FractionColours
) -> None:
    """Draw a problem with its top-left corner at (``x``, ``top``)."""
    left = x + NUMBER_WIDTH
    width = _text_width(block)
    for index, line in enumerate(block.lines):
        room = _room(line)
        baseline = top - room - QUESTION_SIZE * 0.85
        if index == 0:
            pdf.setFillColor("black")
            pdf.setFont(FONT, QUESTION_SIZE)
            pdf.drawString(x, baseline, f"{number}.")
        draw_pieces(pdf, left, baseline, line, QUESTION_SIZE)
        top -= _line_height(line)
    if block.line is not None:
        top -= BELOW_GAP
        draw_fraction_line(pdf, left, top, block.line, width, colours)
        top -= fraction_line_height(block.line)
    if block.choices:
        top -= BELOW_GAP
        letter = block.first_letter
        per_row = _choices_per_row(block)
        share = (width - (per_row - 1) * CHOICE_GAP) / per_row
        for row in _choice_rows(block):
            room = max(_room(choice) for choice in row)
            baseline = top - room - QUESTION_SIZE * 0.85
            for column, choice in enumerate(row):
                choice_x = left + column * (share + CHOICE_GAP)
                pdf.setFillColor("black")
                pdf.setFont(BOLD_FONT, QUESTION_SIZE)
                pdf.drawString(choice_x, baseline, choice_label(letter))
                draw_pieces(pdf, choice_x + LETTER_WIDTH, baseline, choice, QUESTION_SIZE)
                letter += 1
            top -= _choice_row_height(row)
    if block.lines_to_choose:
        top -= BELOW_GAP
        for index, each in enumerate(block.lines_to_choose):
            height = fraction_line_height(each)
            pdf.setFillColor("black")
            pdf.setFont(BOLD_FONT, QUESTION_SIZE)
            letter_y = top - fraction_line_drop(each) - QUESTION_SIZE * 0.35  # level with the line
            pdf.drawString(left, letter_y, choice_label(index))
            draw_fraction_line(pdf, left + LETTER_WIDTH, top, each, width - LETTER_WIDTH, colours)
            top -= height + LINE_CHOICE_GAP
    if block.answer_line:
        line_y = top - ANSWER_LINE_DROP + 4
        length = min(ANSWER_LINE_LENGTH, width)
        pdf.setStrokeColor("black")
        pdf.line(left, line_y, left + length, line_y)
        if block.unit is not None:
            pdf.setFillColor("black")
            pdf.setFont(FONT, QUESTION_SIZE)
            pdf.drawString(left + length + UNIT_GAP, line_y, block.unit)


def _bank_answer(answer: Pieces | FractionLine, colours: FractionColours) -> BankAnswer:
    """Return an answer as the tiles bank draws it: written, or a line small enough for a
    box."""
    if isinstance(answer, tuple):
        return answer
    height = fraction_line_height(answer, compact=True)

    def draw(pdf: Canvas, x: float, top: float) -> None:
        draw_fraction_line(pdf, x, top, answer, BANK_LINE_WIDTH, colours, compact=True)

    return BankPicture(BANK_LINE_WIDTH, height, draw)
