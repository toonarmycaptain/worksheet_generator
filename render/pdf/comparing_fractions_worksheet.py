"""
PDF worksheets of comparing fractions questions, with an optional answer key page.

Compare questions and greatest and least questions without pictures go two to a row, in columns,
when two come together, unless they show a fraction wall; everything else takes the page's
width. Each problem is its number and question, then its pictures in a row (number lines one
above another) or its wall, then what the student writes or circles under them, then what the
student answers on: lettered choices, lettered pictures, an answer line, or lines to explain on.

A sheet for the self-check tiles case has no choices, work or answer lines, and ends with a page
for the answer bank and the pattern. A row of problems that would run past the bottom margin
starts on the next page.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil
from typing import BinaryIO

from reportlab.pdfgen.canvas import Canvas

from core.comparing_fractions.data import (
    CompareQuestionData,
    ComparingFractionsQuestion,
    DrawQuestionData,
    EveryQuestionData,
    ExplainQuestionData,
    GreatestQuestionData,
    LessGreaterForm,
    LessGreaterQuestionData,
    Picture,
    WordQuestionData,
)
from core.comparing_fractions.representation import (
    answer_line,
    choice_pieces,
    comparing_fractions_tile_question,
    question,
    solution,
    work,
    writing_lines,
)
from core.fraction_models.area_models import AreaModel, FractionWall, Grid, Strip
from core.fraction_models.number_lines import FractionLine
from core.fraction_models.object_groups import ObjectGroup
from core.question import FreeResponse, MultipleChoice
from core.written_numbers import Pieces
from render.pdf.graphics.fractions import (
    COLOUR_FRACTIONS,
    GREY_FRACTIONS,
    ROW_LABEL_ROOM,
    ROW_LABEL_SIZE,
    FractionColours,
    draw_area_model,
    draw_fraction_line,
    draw_fraction_wall,
    draw_object_group,
    fraction_line_drop,
    fraction_line_height,
    fraction_wall_height,
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
from render.pdf.tiles import draw_tiles_page

QUESTION_SIZE = 12  # every problem's text and its choices
LINE_GAP = 3  # between two lines of a problem's text
NUMBER_WIDTH = 24  # from a problem's number to its text
COLUMN_GAP = 18
COLUMN_WIDTH = (CONTENT_WIDTH - COLUMN_GAP) / 2
BELOW_GAP = 8  # from a problem's text to its pictures, and from those to what follows
ROW_GAP = 22  # from the bottom of a row of problems to the top of the next

# Pictures in a row: each in an equal share of the row, a gap between, at most this large
PICTURE_GAP = 16
STRIP_WIDTH, STRIP_HEIGHT = 200, 36
GRID_WIDTH, GRID_HEIGHT = 150, 90
ROUND_SIDE = 90  # a circle or another shape cut from its centre
OBJECT_SPACING = 32  # from one object in a group to the next, at most
LINE_WIDTH = 360  # a number line, and a fraction wall
LINE_STACK_GAP = 6  # between two number lines, one above the other

LETTER_WIDTH = 24  # room for "A)" left of each choice
CHOICE_GAP = 12  # between two choices in a row
ANSWER_LINE_DROP = 28  # from the top of an answer line's space down to the line
ANSWER_LINE_LENGTH = 110
WRITING_LINE_GAP = 28  # from one line to explain on to the next


@dataclass(frozen=True)
class _Block:
    """A problem as laid out: its text's lines, its pictures, wall and work, and what the
    student answers on."""

    lines: list[Pieces]
    pictures: tuple[Picture, ...]  # in a row, or number lines one above another
    lettered: bool  # whether the pictures are the lettered choices
    wall: FractionWall | None
    work: list[Pieces]
    choices: tuple[Pieces, ...]  # lettered choices, written
    second_row: tuple[Picture, ...]  # pictures in a row, below the first: to choose or circle
    second_lettered: bool  # whether the second row's pictures are lettered choices
    answer_line: bool
    writing_lines: int  # lines as wide as the problem, to explain on
    wide: bool  # whether it takes the page's width, not a column


def render_comparing_fractions_worksheet(
    questions: Sequence[ComparingFractionsQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    slot_of: Sequence[int] | None,
    black_and_white: bool = False,
) -> None:
    """
    Render comparing fractions problems, and the answer key if requested, to ``path``, with
    shading in blue, or grey with ``black_and_white``.

    The answer key gives each problem's answer, after the correct letters for lettered choices,
    with why, its fractions written as the problem writes them. ``path`` is a filename or a
    binary file-like object.

    With ``slot_of``, the sheet is for the self-check tiles case: the questions must be written,
    with different answers, as ``core.comparing_fractions.generator`` makes them, and the answer
    bank and pattern follow on a page of their own. ``slot_of[i]`` is the slot of question
    i + 1's answer, as in ``core.self_check_tiles``, so there are at most 12 questions. The answer
    key adds each answer's slot letter.
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
        tile_questions = [comparing_fractions_tile_question(each.data) for each in questions]
        draw_tiles_page(pdf, header, [each.answer for each in tile_questions], slot_of)
        solutions = [
            (*solution(each.data), f"    ({choice_label(slot)[0]})")
            for each, slot in zip(questions, slot_of, strict=True)
        ]
    if answer_key:
        draw_answer_key(pdf, header, solutions)
    pdf.save()


def _solution(each: ComparingFractionsQuestion) -> Pieces:
    """Return the answer key's entry, after the correct letters for lettered choices."""
    entry = solution(each.data)
    if isinstance(each.response, MultipleChoice):
        return (f"{correct_letters(each.response)}) ", *entry)
    return entry


def _block(each: ComparingFractionsQuestion, tiles: bool) -> _Block:
    """Lay out a problem: what it shows, and whether it's in a column or as wide as the page."""
    data, response = each.data, each.response
    choosing = isinstance(response, MultipleChoice)
    options = response.options if isinstance(response, MultipleChoice) else ()
    pictures: tuple[Picture, ...] = ()
    wall: FractionWall | None = None
    second_row: tuple[Picture, ...] = ()
    if isinstance(data, LessGreaterQuestionData):
        pictures = (data.model,)
        if data.form is LessGreaterForm.DIVIDE:
            pictures = (data.model, *([data.blank] * 3))
        second_row = data.pictures or tuple(each for each in options if isinstance(each, AreaModel))
    elif isinstance(data, DrawQuestionData):
        pictures = data.blanks
    elif isinstance(data, CompareQuestionData | ExplainQuestionData | GreatestQuestionData):
        pictures, wall = data.pictures, data.wall
    elif isinstance(data, WordQuestionData):
        pictures = data.pictures
    lettered = bool(options) and all(_is_picture(option) for option in options) and not second_row
    choices = () if lettered or second_row else _written_choices(each)
    wide = (
        not (
            isinstance(data, CompareQuestionData | EveryQuestionData)
            or (isinstance(data, GreatestQuestionData) and not data.pictures)
        )
        or wall is not None
    )
    width = (CONTENT_WIDTH if wide else COLUMN_WIDTH) - NUMBER_WIDTH
    return _Block(
        lines=wrap_pieces(question(data, choosing, tiles), QUESTION_SIZE, width),
        pictures=pictures,
        lettered=lettered,
        wall=wall,
        work=wrap_pieces(work(data, choosing, tiles), QUESTION_SIZE, width),
        choices=choices,
        second_row=second_row,
        second_lettered=choosing,
        answer_line=isinstance(response, FreeResponse)
        and not tiles
        and answer_line(data, choosing, tiles),
        writing_lines=writing_lines(data, choosing, tiles),
        wide=wide,
    )


def _is_picture(option: object) -> bool:
    """Return whether a choice is a picture."""
    return isinstance(option, AreaModel | ObjectGroup | FractionLine)


def _written_choices(each: ComparingFractionsQuestion) -> tuple[Pieces, ...]:
    """Return a question's written choices as written maths."""
    if not isinstance(each.response, MultipleChoice):
        return ()
    found = [choice_pieces(each.data, option) for option in each.response.options]
    return tuple(pieces for pieces in found if pieces is not None)


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


def _lines_height(lines: Sequence[Pieces]) -> float:
    """Return the height lines of text take."""
    return sum(_line_height(line) for line in lines)


# --- choices


def _choices_per_row(block: _Block) -> int:
    """Return how many of a problem's written choices fit in a row: all four, two, or one."""
    widest = max(pieces_width(choice, QUESTION_SIZE) for choice in block.choices)
    width = _text_width(block)
    return next(
        (
            per_row
            for per_row in (len(block.choices), 2)
            if LETTER_WIDTH + widest <= (width - (per_row - 1) * CHOICE_GAP) / per_row
        ),
        1,
    )


def _choice_rows(block: _Block) -> list[list[list[Pieces]]]:
    """Return a problem's written choices in rows, each choice as its lines: one to a row, a
    choice wraps."""
    per_row = _choices_per_row(block)
    room = (_text_width(block) - (per_row - 1) * CHOICE_GAP) / per_row - LETTER_WIDTH
    wrapped = [wrap_pieces(choice, QUESTION_SIZE, room) for choice in block.choices]
    return [wrapped[start : start + per_row] for start in range(0, len(wrapped), per_row)]


def _choice_row_height(row: Sequence[Sequence[Pieces]]) -> float:
    """Return the height of a row of written choices: its tallest choice's."""
    return max(_lines_height(choice) for choice in row)


# --- pictures


def _area_size(models: Sequence[AreaModel], width: float) -> tuple[float, float]:
    """Return the width of each of ``models`` side by side in ``width``, and their height:
    strips long and low, grids wider than high, other shapes square."""
    count = len(models)
    room = (width - (count - 1) * PICTURE_GAP) / count
    split = models[0].split
    if isinstance(split, Strip) and not models[0].look:
        share = min(room, STRIP_WIDTH)
        return share, STRIP_HEIGHT
    if isinstance(split, Grid):
        share = min(room, GRID_WIDTH)
        return share, share * GRID_HEIGHT / GRID_WIDTH
    share = min(room, ROUND_SIDE)
    return share, share


def _group_spacing(groups: Sequence[ObjectGroup], width: float) -> float:
    """Return the spacing of ``groups``' objects side by side in ``width``, the same for all,
    so their objects are the same size."""
    room = (width - (len(groups) - 1) * PICTURE_GAP) / len(groups)
    columns = max(min(each.count, each.per_row) for each in groups)
    return min(OBJECT_SPACING, room / columns)


def _pictures_height(pictures: Sequence[Picture], width: float, lettered: bool) -> float:
    """Return the height of pictures in a row, or number lines one above another, with a letter
    under each, or beside each line, when they're ``lettered``."""
    first = pictures[0]
    if isinstance(first, FractionLine):
        lines = [each for each in pictures if isinstance(each, FractionLine)]
        heights = sum(fraction_line_height(each) for each in lines)
        return heights + (len(lines) - 1) * LINE_STACK_GAP
    label = ROW_LABEL_ROOM if lettered else 0
    if isinstance(first, ObjectGroup):
        groups = [each for each in pictures if isinstance(each, ObjectGroup)]
        rows = max(ceil(each.count / each.per_row) for each in groups)
        return rows * _group_spacing(groups, width) + label
    models = [each for each in pictures if isinstance(each, AreaModel)]
    return _area_size(models, width)[1] + label


def _draw_pictures(
    pdf: Canvas,
    pictures: Sequence[Picture],
    x: float,
    top: float,
    width: float,
    lettered: bool,
    colours: FractionColours,
) -> None:
    """Draw pictures in a row from (``x``, ``top``), or number lines one above another, each
    lettered under it, or beside it, when they're ``lettered``."""
    first = pictures[0]
    if isinstance(first, FractionLine):
        left = x + LETTER_WIDTH if lettered else x
        line_width = min(LINE_WIDTH, width - (left - x))
        for index, line in enumerate(each for each in pictures if isinstance(each, FractionLine)):
            if lettered:
                _letter(pdf, x, top - fraction_line_drop(line) - QUESTION_SIZE * 0.35, index)
            draw_fraction_line(pdf, left, top, line, line_width, colours)
            top -= fraction_line_height(line) + LINE_STACK_GAP
        return
    if isinstance(first, ObjectGroup):
        groups = [each for each in pictures if isinstance(each, ObjectGroup)]
        spacing = _group_spacing(groups, width)
        rows = max(ceil(each.count / each.per_row) for each in groups)
        share = max(min(each.count, each.per_row) for each in groups) * spacing
        for index, group in enumerate(groups):
            left = x + index * (share + PICTURE_GAP)
            columns = min(group.count, group.per_row)
            group_rows = ceil(group.count / group.per_row)
            draw_object_group(
                pdf, left, top, group, columns * spacing, group_rows * spacing, colours
            )
            if lettered:
                _label_under(pdf, left + share / 2, top - rows * spacing, index)
        return
    models = [each for each in pictures if isinstance(each, AreaModel)]
    share, height = _area_size(models, width)
    for index, model in enumerate(models):
        left = x + index * (share + PICTURE_GAP)
        draw_area_model(pdf, left, top, model, share, height, colours)
        if lettered:
            _label_under(pdf, left + share / 2, top - height, index)


def _letter(pdf: Canvas, x: float, baseline: float, index: int) -> None:
    """Draw a choice's letter, "A)", in bold."""
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, QUESTION_SIZE)
    pdf.drawString(x, baseline, choice_label(index))


def _label_under(pdf: Canvas, middle: float, bottom: float, index: int) -> None:
    """Draw a picture's letter centred under it, its bottom at ``bottom``."""
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, ROW_LABEL_SIZE)
    pdf.drawCentredString(middle, bottom - ROW_LABEL_ROOM + 4, choice_label(index)[0])


# --- a problem


def _height(block: _Block) -> float:
    """Return the height a problem takes, from the top of its first line."""
    width = _text_width(block)
    height = _lines_height(block.lines)
    if block.pictures:
        height += BELOW_GAP + _pictures_height(block.pictures, width, block.lettered)
    if block.wall is not None:
        height += BELOW_GAP + fraction_wall_height(block.wall)
    if block.work:
        height += BELOW_GAP + _lines_height(block.work)
    if block.second_row:
        height += BELOW_GAP + _pictures_height(block.second_row, width, block.second_lettered)
    if block.choices:
        height += BELOW_GAP + sum(_choice_row_height(row) for row in _choice_rows(block))
    if block.answer_line:
        height += ANSWER_LINE_DROP
    return height + block.writing_lines * WRITING_LINE_GAP


def _draw_lines(pdf: Canvas, lines: Sequence[Pieces], left: float, top: float) -> float:
    """Draw lines of text from (``left``, ``top``) down, and return the y below them."""
    for line in lines:
        baseline = top - _room(line) - QUESTION_SIZE * 0.85
        draw_pieces(pdf, left, baseline, line, QUESTION_SIZE)
        top -= _line_height(line)
    return top


def _draw_block(
    pdf: Canvas, number: int, block: _Block, x: float, top: float, colours: FractionColours
) -> None:
    """Draw a problem with its top-left corner at (``x``, ``top``)."""
    left = x + NUMBER_WIDTH
    width = _text_width(block)
    pdf.setFillColor("black")
    pdf.setFont(FONT, QUESTION_SIZE)
    pdf.drawString(x, top - _room(block.lines[0]) - QUESTION_SIZE * 0.85, f"{number}.")
    top = _draw_lines(pdf, block.lines, left, top)
    if block.pictures:
        top -= BELOW_GAP
        _draw_pictures(pdf, block.pictures, left, top, width, block.lettered, colours)
        top -= _pictures_height(block.pictures, width, block.lettered)
    if block.wall is not None:
        top -= BELOW_GAP
        draw_fraction_wall(pdf, left, top, block.wall, min(LINE_WIDTH, width))
        top -= fraction_wall_height(block.wall)
    if block.work:
        top -= BELOW_GAP
        pdf.setFillColor("black")
        top = _draw_lines(pdf, block.work, left, top)
    if block.second_row:
        top -= BELOW_GAP
        _draw_pictures(pdf, block.second_row, left, top, width, block.second_lettered, colours)
        top -= _pictures_height(block.second_row, width, block.second_lettered)
    if block.choices:
        top -= BELOW_GAP
        letter = 0
        per_row = _choices_per_row(block)
        share = (width - (per_row - 1) * CHOICE_GAP) / per_row
        for row in _choice_rows(block):
            for column, choice in enumerate(row):
                choice_x = left + column * (share + CHOICE_GAP)
                baseline = top - _room(choice[0]) - QUESTION_SIZE * 0.85
                _letter(pdf, choice_x, baseline, letter)
                pdf.setFillColor("black")
                _draw_lines(pdf, choice, choice_x + LETTER_WIDTH, top)
                letter += 1
            top -= _choice_row_height(row)
    pdf.setStrokeColor("black")
    if block.answer_line:
        line_y = top - ANSWER_LINE_DROP + 4
        pdf.line(left, line_y, left + min(ANSWER_LINE_LENGTH, width), line_y)
    for _ in range(block.writing_lines):
        top -= WRITING_LINE_GAP
        pdf.line(left, top + 4, left + width, top + 4)
