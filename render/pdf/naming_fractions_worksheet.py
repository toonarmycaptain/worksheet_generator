"""
PDF worksheets of naming fractions questions, with an optional answer key page.

Naming and shading questions go two to a row, in columns, when two come together; stories, and
questions with four pictures to choose from, take the page's width. Each problem is its number and
question, then its picture, then what the student answers on: lettered fractions in a row,
lettered pictures two to a row, or an answer line. A shading question's picture is where the
student answers, and so is a whole to cut into shares, beside its answer line.

A sheet for the self-check tiles case has no choices or answer lines, and ends with a page for the
answer bank, where a shading question's answer is its picture, and the pattern. A row of problems
that would run past the bottom margin starts on the next page.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil, sqrt
from typing import BinaryIO, assert_never

from reportlab.pdfgen.canvas import Canvas

from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    AreaModel,
    CutShape,
    Grid,
    Lattice,
    RadialPartition,
    Rectangle,
    SlicedCircle,
    Strip,
    TriangleGrid,
)
from core.fraction_models.object_groups import ObjectGroup
from core.naming_fractions.data import (
    NameQuestionData,
    NamingFractionsQuestion,
    Picture,
    ShadeQuestionData,
)
from core.naming_fractions.representation import (
    naming_fractions_tile_question,
    question,
    solution,
)
from core.question import FreeResponse, MultipleChoice
from core.written_numbers import Pieces, UnreducedFraction
from render.pdf.graphics.fractions import (
    COLOUR_FRACTIONS,
    GREY_FRACTIONS,
    FractionColours,
    draw_area_model,
    draw_object_group,
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
    stacked,
    start_page,
    wrap_pieces,
)
from render.pdf.tiles import BOX_PADDING, BOX_WIDTH, BankAnswer, BankPicture, draw_tiles_page

QUESTION_SIZE = 12  # every problem's text and its choices
LINE_GAP = 3  # between two lines of a problem's text
NUMBER_WIDTH = 24  # from a problem's number to its text
COLUMN_GAP = 18
COLUMN_WIDTH = (CONTENT_WIDTH - COLUMN_GAP) / 2
BELOW_GAP = 8  # from a problem's text to its picture, and from that to its choices
ROW_GAP = 22  # from the bottom of a row of problems to the top of the next

# The most room a picture takes, across and down: in a column, as wide as the page's text, and
# as one of four choices, two to a row
COLUMN_PICTURE_HEIGHT = 100
WIDE_PICTURE_HEIGHT = 130
CHOICE_PICTURE_HEIGHT = 90
BANK_PICTURE_WIDTH = BOX_WIDTH - 2 * BOX_PADDING
BANK_PICTURE_HEIGHT = 52
OBJECT_SPACING = 40  # from one object in a group to the next, at full size
GRID_PART = 36  # a side of a grid's part, at full size

LETTER_WIDTH = 24  # room for "A)" left of each choice
CHOICE_ROW_HEIGHT = QUESTION_SIZE + 2 * FRACTION_ROOM + LINE_GAP  # a row of lettered fractions
PICTURE_CHOICE_GAP = 12  # between two rows of pictures to choose from, and two pictures
ANSWER_LINE_DROP = 28  # from the top of an answer line's space down to the line
ANSWER_LINE_LENGTH = 150


@dataclass(frozen=True)
class _Block:
    """A problem as laid out: its text's lines, its picture and what the student answers on."""

    lines: list[Pieces]
    picture: Picture | None
    fractions: tuple[UnreducedFraction, ...]  # lettered fractions to choose from
    pictures: tuple[Picture, ...]  # lettered pictures to choose from
    answer_line: bool
    wide: bool  # whether it takes the page's width, not a column


def render_naming_fractions_worksheet(
    questions: Sequence[NamingFractionsQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    slot_of: Sequence[int] | None,
    black_and_white: bool = False,
) -> None:
    """
    Render naming fractions problems, and the answer key if requested, to ``path``, with shading
    in blue, or grey with ``black_and_white``.

    The answer key gives each problem's answer, after the correct letters for lettered choices,
    with how the picture or story shows it, its fractions written as the problem writes them.
    ``path`` is a filename or a binary file-like object.

    With ``slot_of``, the sheet is for the self-check tiles case: the questions must be written,
    with different answers, as ``core.naming_fractions.generator`` makes them, and the answer
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
        tile_questions = [naming_fractions_tile_question(each.data) for each in questions]
        answers = [_bank_answer(each.answer, colours) for each in tile_questions]
        draw_tiles_page(pdf, header, answers, slot_of)
        solutions = [
            (*solution(each.data), f"    ({choice_label(slot)[0]})")
            for each, slot in zip(questions, slot_of, strict=True)
        ]
    if answer_key:
        draw_answer_key(pdf, header, solutions)
    pdf.save()


def _solution(each: NamingFractionsQuestion) -> Pieces:
    """Return the answer key's entry, after the correct letters for lettered choices."""
    entry = solution(each.data)
    if isinstance(each.response, MultipleChoice):
        return (f"{correct_letters(each.response)}) ", *entry)
    return entry


def _block(each: NamingFractionsQuestion, tiles: bool) -> _Block:
    """Lay out a problem: what it shows, and whether it's in a column or as wide as the page."""
    data, response = each.data, each.response
    choices = isinstance(response, MultipleChoice)
    shade = isinstance(data, ShadeQuestionData)
    wide = not (isinstance(data, NameQuestionData) or (shade and not choices))
    text_width = (CONTENT_WIDTH if wide else COLUMN_WIDTH) - NUMBER_WIDTH
    lines = wrap_pieces(question(data, choices, tiles), QUESTION_SIZE, text_width)
    picture = None if shade and (choices or tiles) else data.picture
    options = response.options if isinstance(response, MultipleChoice) else ()
    fractions = tuple(option for option in options if isinstance(option, UnreducedFraction))
    pictures = tuple(option for option in options if not isinstance(option, UnreducedFraction))
    answer_line = isinstance(response, FreeResponse) and not (tiles or shade)
    return _Block(lines, picture, fractions, pictures, answer_line, wide)


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


def _height(block: _Block) -> float:
    """Return the height a problem takes, from the top of its first line."""
    height = sum(_line_height(line) for line in block.lines)
    if block.picture is not None:
        height += BELOW_GAP + _picture_size(block.picture, *_picture_room(block))[1]
    if block.fractions:
        height += BELOW_GAP + CHOICE_ROW_HEIGHT
    if block.pictures:
        height += BELOW_GAP + _picture_choices_height(block.pictures)
    if block.answer_line:
        height += ANSWER_LINE_DROP
    return height


def _picture_room(block: _Block) -> tuple[float, float]:
    """Return the most room a problem's picture takes, across and down."""
    return _text_width(block), WIDE_PICTURE_HEIGHT if block.wide else COLUMN_PICTURE_HEIGHT


def _choice_width() -> float:
    """Return the most width a picture to choose from takes, beside its letter."""
    return (CONTENT_WIDTH - NUMBER_WIDTH - PICTURE_CHOICE_GAP) / 2 - LETTER_WIDTH


def _picture_choices_height(pictures: Sequence[Picture]) -> float:
    """Return the height of pictures to choose from, two to a row."""
    heights = [_picture_size(each, _choice_width(), CHOICE_PICTURE_HEIGHT)[1] for each in pictures]
    rows = [max(heights[start : start + 2]) for start in range(0, len(heights), 2)]
    return sum(rows) + (len(rows) - 1) * PICTURE_CHOICE_GAP


def _draw_block(
    pdf: Canvas, number: int, block: _Block, x: float, top: float, colours: FractionColours
) -> None:
    """Draw a problem with its top-left corner at (``x``, ``top``)."""
    left = x + NUMBER_WIDTH
    for index, line in enumerate(block.lines):
        room = _room(line)
        baseline = top - room - QUESTION_SIZE * 0.85
        if index == 0:
            pdf.setFillColor("black")
            pdf.setFont(FONT, QUESTION_SIZE)
            pdf.drawString(x, baseline, f"{number}.")
        draw_pieces(pdf, left, baseline, line, QUESTION_SIZE)
        top -= _line_height(line)
    if block.picture is not None:
        top -= BELOW_GAP
        width, height = _picture_size(block.picture, *_picture_room(block))
        _draw_picture(pdf, block.picture, left, top, width, height, colours)
        top -= height
    if block.fractions:
        top -= BELOW_GAP
        share = _text_width(block) / len(block.fractions)
        baseline = top - FRACTION_ROOM - QUESTION_SIZE * 0.85
        for index, option in enumerate(block.fractions):
            option_x = left + index * share
            pdf.setFont(BOLD_FONT, QUESTION_SIZE)
            pdf.drawString(option_x, baseline, choice_label(index))
            draw_pieces(pdf, option_x + LETTER_WIDTH, baseline, (option,), QUESTION_SIZE)
        top -= CHOICE_ROW_HEIGHT
    if block.pictures:
        top -= BELOW_GAP
        _draw_picture_choices(pdf, block.pictures, left, top, colours)
        top -= _picture_choices_height(block.pictures)
    if block.answer_line:
        line_y = top - ANSWER_LINE_DROP + 4
        pdf.line(left, line_y, left + min(ANSWER_LINE_LENGTH, _text_width(block)), line_y)


def _draw_picture_choices(
    pdf: Canvas, pictures: Sequence[Picture], left: float, top: float, colours: FractionColours
) -> None:
    """Draw pictures to choose from, two to a row, each after its letter, from ``top`` down."""
    width = _choice_width()
    sizes = [_picture_size(each, width, CHOICE_PICTURE_HEIGHT) for each in pictures]
    for start in range(0, len(pictures), 2):
        for index in range(start, min(start + 2, len(pictures))):
            column_x = left + (index - start) * (LETTER_WIDTH + width + PICTURE_CHOICE_GAP)
            pdf.setFillColor("black")
            pdf.setFont(BOLD_FONT, QUESTION_SIZE)
            pdf.drawString(column_x, top - QUESTION_SIZE, choice_label(index))
            picture_width, picture_height = sizes[index]
            _draw_picture(
                pdf,
                pictures[index],
                column_x + LETTER_WIDTH,
                top,
                picture_width,
                picture_height,
                colours,
            )
        top -= max(height for _, height in sizes[start : start + 2]) + PICTURE_CHOICE_GAP


def _draw_picture(
    pdf: Canvas,
    picture: Picture,
    x: float,
    top: float,
    width: float,
    height: float,
    colours: FractionColours,
) -> None:
    """Draw a picture in a box ``width`` by ``height`` with its top-left corner at (x, top)."""
    if isinstance(picture, ObjectGroup):
        draw_object_group(pdf, x, top, picture, width, height, colours)
    else:
        draw_area_model(pdf, x, top, picture, width, height, colours)


def _bank_answer(answer: Pieces | Picture, colours: FractionColours) -> BankAnswer:
    """Return an answer as the tiles bank draws it: written, or a picture small enough for a
    box."""
    if isinstance(answer, tuple):
        return answer
    width, height = _picture_size(answer, BANK_PICTURE_WIDTH, BANK_PICTURE_HEIGHT)

    def draw(pdf: Canvas, x: float, top: float) -> None:
        _draw_picture(pdf, answer, x, top, width, height, colours)

    return BankPicture(width, height, draw)


def _picture_size(picture: Picture, most_width: float, most_height: float) -> tuple[float, float]:
    """Return the size a picture is drawn at: its full size, shrunk to fit the room given."""
    width, height = _full_size(picture)
    scale = min(1, most_width / width, most_height / height)
    return width * scale, height * scale


def _full_size(picture: Picture) -> tuple[float, float]:
    """Return a picture's size, across and down, when there's room for all of it."""
    if isinstance(picture, ObjectGroup):
        rows = ceil(picture.count / picture.per_row)
        return min(picture.count, picture.per_row) * OBJECT_SPACING, rows * OBJECT_SPACING
    return _model_size(picture)


def _model_size(model: AreaModel) -> tuple[float, float]:
    """Return an area model's full size: each shape in its own proportions."""
    split = model.split
    if model.look is DrawnObject.ROUND_CAKE:
        return 130, 91
    if model.look is DrawnObject.CHOCOLATE_BAR and split.parts == 1:
        return 200, 64
    match split:
        case Strip():
            return 220, 40
        case Grid():
            if split.parts == 1:
                return (110, 110) if model.look is DrawnObject.SQUARE_CAKE else (200, 100)
            return split.columns * GRID_PART, split.rows * GRID_PART
        case RadialPartition():
            return (180, 100) if isinstance(split.outline, Rectangle) else (110, 110)
        case SlicedCircle():
            return 110, 110
        case TriangleGrid():
            return 120, 104
        case CutShape():
            return _cut_shape_size(split)
        case _:
            assert_never(split)


def _cut_shape_size(cut: CutShape) -> tuple[float, float]:
    """Return a cut shape's full size, in its outline's proportions, up to 130 by 110."""
    corners = cut.outline.corners
    if cut.outline.lattice is Lattice.TRIANGLE:  # across, and down a line 60 degrees from it
        points = [(float(x) + float(y) / 2, float(y) * sqrt(3) / 2) for x, y in corners]
    else:
        points = [(float(x), float(y)) for x, y in corners]
    across = max(x for x, _ in points) - min(x for x, _ in points)
    down = max(y for _, y in points) - min(y for _, y in points)
    scale = min(130 / across, 110 / down)
    return across * scale, down * scale
