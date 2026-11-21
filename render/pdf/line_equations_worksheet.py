"""
PDF worksheets of questions about lines, with an optional answer key page.

Each question asks for a feature of a line, such as its slope, or its equation in a form, with the
line shown under it as an equation, two points, or a point and slope, or the line it's parallel
or perpendicular to. Below that come an answer line, two labelled blanks for the slope and
y-intercept, lettered choices, or, for the self-check tiles case, nothing: the answer bank and
pattern follow on a page of their own. A line shown as a table or a graph, or two points with a
blank grid to work on, has the table or grid in the left half under the question, and the
answer beside it in the right half. A line to graph has its blank grid there, and a table to
complete its table, beside the graph it's completed from if there is one; the answer key draws
the line on a smaller grid, or the table filled in. A graph or table to choose has four lettered
graphs, two to a row, each as wide as a question's grid, or four lettered tables, in a row or one
under another; on a self-check tiles sheet, the graphs and tables are the answer bank. Fractions
are drawn stacked, as STAAR prints them, since an inline fraction such as -3/4x is ambiguous.
"""

from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction
from string import ascii_uppercase
from typing import BinaryIO

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.line_equations.data import (
    Equation,
    Grid,
    Line,
    LineForm,
    LineQuestion,
    LineQuestionData,
    Stated,
)
from core.line_equations.representation import (
    answer_pieces,
    blank_labels,
    choice_pieces,
    choice_table_cells,
    given_pieces,
    instruction,
    point_pieces,
    table_cells,
    tile_answer_pieces,
)
from core.question import MultipleChoice
from core.written_numbers import Pieces, inline
from render.pdf.coordinate_plane import (
    AXIS_OVERHANG,
    draw_coordinate_plane,
    draw_line,
    draw_point,
    plane_height,
)
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
from render.pdf.tables import draw_table
from render.pdf.tiles import BankPicture, draw_picture_tiles_pages, draw_tiles_page

ANSWER_LINE_DROP = 14  # offset of the answer line below the next text baseline
ANSWER_HEIGHT = 38  # answer line plus the gap below it, as on the place-value sheet
CHOICE_INDENT = 22  # offset of a choice from its letter
CHOICE_COLUMNS = 4  # choices that fit go in a row, each in a quarter of the width
CHOICE_MARGIN = 18  # the least gap between a choice in a row and the next choice's letter
CHOICES_GAP = 18  # gap between a question's choices and the next question
TILES_GAP = 14  # gap between questions on a self-check tiles sheet, which has no answer lines
BLANK_LENGTH = 14  # underscores in a labelled blank, or as many as fit
BLANKS_DROP = 24  # from the line's baseline down to the blanks'
BLANKS_HEIGHT = 52  # the blanks plus the gap below them
PICTURE_GAP = 18  # between a table or grid and the answer beside it
PICTURE_WIDTH = (TEXT_WIDTH - PICTURE_GAP) / 2  # the left half, for a table or grid
ANSWER_WIDTH = TEXT_WIDTH - PICTURE_WIDTH - PICTURE_GAP  # the right half, for the answer
GRID_WIDTH = PICTURE_WIDTH - 2 * AXIS_OVERHANG  # a grid, its axes running past it both sides
PICTURE_RAISE = 10  # a picture's top is this far above the next text baseline
PICTURE_AFTER = 30  # from the bottom of a picture or its answer down to the next baseline
BLANKS_APART = (
    30  # between the baselines of the slope's blank and the y-intercept's beside a picture
)
TABLE_SIZE = 12  # a table's headings and numbers
TABLE_ROW_HEIGHT = 20
TABLE_FRACTION_ROW_HEIGHT = 28  # a row of a table with a stacked fraction in it
TABLE_COLUMN_WIDTH = 56  # each column of a table set out down the page
TABLE_HEADING_WIDTH = 28  # the headings' column of a table set out across the page
TABLE_CELL_WIDTH = 40  # at most, each number's cell of a table set out across the page
KEY_GRID_WIDTH = 0.7 * GRID_WIDTH  # a graphed line's grid in the answer key, smaller
KEY_PICTURE_GAP = 24  # below a grid or table in the answer key
CHOICE_GRID_DROP = 8  # from a graph to choose's letter's baseline down to the graph's top
CHOICE_ROW_GAP = 22  # from the bottom of a row of graphs to choose down to the next row's letters
CHOICE_TABLE_GAP = 10  # between tables to choose set out across the page, one under another


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

    A question asking for a vertical or horizontal line's equation and a statement has two
    labelled blanks, "Equation" and "Slope" or "Parallel or perpendicular". A graph or table to
    choose has four lettered graphs or tables, as ``_draw_choices`` draws them, and on a tiles
    sheet, the answer bank is the graphs and tables, lettered, as ``_bank_picture`` draws them.

    The answer key gives each answer: a number, "undefined", an ordered pair, the slope and
    y-intercept, an equation, or a statement, after the correct letter for a multiple-choice
    question, and followed by its slot letter on a tiles sheet; for a graph or table to choose,
    only the letter. ``path`` is a filename or a binary file-like object.
    """
    pdf = new_pdf(path, header.title)

    y = start_page(pdf, header)
    for number, question in enumerate(questions, start=1):
        data = question.data
        lines = wrap(instruction(data), TEXT_SIZE, TEXT_WIDTH)
        given = given_pieces(data)
        below = _below(question, tiles=slot_of is not None)
        given_height = LINE_HEIGHT + 2 * _room(given) if given else 0
        picture = _picture_height(data)
        if below[0] in ("graphs", "tables"):
            content = (picture + PICTURE_AFTER if picture else 0) + _choices_height(question)
        else:
            content = _beside_height(below, picture) if picture else _height(below)
        y = make_room(pdf, header, y, len(lines) * LINE_HEIGHT + given_height + content)
        y = draw_numbered_lines(pdf, number, lines, y)
        if given:
            y -= _room(given)
            draw_pieces(pdf, MARGIN + TEXT_INDENT, y, given, TEXT_SIZE)
            y -= LINE_HEIGHT + _room(given)
        if below[0] in ("graphs", "tables"):
            if picture:
                y = _draw_beside(pdf, data, ("none", []), y)
            y = _draw_choices(pdf, question, y)
        else:
            y = _draw_beside(pdf, data, below, y) if picture else _draw_below(pdf, below, y)

    pictures = all(question.data.chosen for question in questions)
    if slot_of is None:
        solutions = [_solution(question) for question in questions]
    elif pictures:
        draw_picture_tiles_pages(
            pdf, header, [_bank_picture(question.data) for question in questions], slot_of
        )
        solutions = [(f"({ascii_uppercase[slot]})",) for slot in slot_of]
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


# What goes under a question's line: "tiles" or "none" (nothing), "line", two labelled "blanks",
# each as (label, ()), its choices in a "row" or a "column", each choice as (letter, pieces), or
# "graphs" or "tables" to choose, which ``_draw_choices`` draws from the question
type Below = tuple[str, list[tuple[str, Pieces]]]


def _below(question: LineQuestion, tiles: bool) -> Below:
    """Return what goes under the question's line, as ``render_line_equations_worksheet`` says."""
    response = question.response
    if question.data.asked in (LineForm.GRAPH, LineForm.TABLE):
        if isinstance(response, MultipleChoice):
            return ("graphs" if question.data.asked is LineForm.GRAPH else "tables", [])
        return ("tiles" if tiles else "none", [])
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
    labels = blank_labels(question.data)
    if labels:
        return ("blanks", [(label, ()) for label in labels])
    return ("line", [])


def _height(below: Below) -> float:
    """Return the height of what goes under a question's line, with the gap after it."""
    kind, choices = below
    match kind:
        case "tiles" | "none":
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
            (first, _), (second, _) = choices
            pdf.setFont(FONT, TEXT_SIZE)
            pdf.drawString(left, y - BLANKS_DROP, _blank(first, TEXT_WIDTH / 2))
            pdf.drawString(left + TEXT_WIDTH / 2, y - BLANKS_DROP, _blank(second, TEXT_WIDTH / 2))
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


def _blank(label: str, width: float) -> str:
    """
    Return a labelled blank, "Slope: ______________", with ``BLANK_LENGTH`` underscores, or as
    many as fit in ``width`` at the text size.
    """
    text = f"{label}: "
    room = width - stringWidth(text, FONT, TEXT_SIZE) - TEXT_SIZE
    fitting = int(room // stringWidth("_", FONT, TEXT_SIZE))
    return text + "_" * min(BLANK_LENGTH, fitting)


def _shown(data: LineQuestionData) -> tuple[bool, bool]:
    """
    Return whether the question shows a grid and whether it shows a table, beside or under its
    text: a graph given, a blank grid to work on or to graph on, a table given or to complete.
    A graph or table to choose shows neither, its grid and x-values being its choices', apart
    from a graph that a table to choose is of.
    """
    if not data.chosen:
        return data.grid is not None, bool(data.table_xs)
    return data.given is LineForm.GRAPH and data.grid is not None, False


def _picture_height(data: LineQuestionData) -> float:
    """
    Return the height of the table or grid the question shows, or the taller of the two when
    it shows both, or 0 if it shows neither: a grid's with its axes' overhang above and below.
    """
    grid_shown, table_shown = _shown(data)
    heights = [0.0]
    if table_shown:
        heights.append(_table_height(data))
    if grid_shown and data.grid is not None:
        grid = data.grid
        heights.append(plane_height(GRID_WIDTH, grid.largest_x, grid.largest_y) + 2 * AXIS_OVERHANG)
    return max(heights)


def _fits_beside(below: Below) -> bool:
    """Return whether what goes under a question fits in the right half beside its picture."""
    kind, choices = below
    if kind not in ("row", "column"):
        return True
    room = ANSWER_WIDTH - CHOICE_INDENT
    return all(pieces_width(pieces, TEXT_SIZE) <= room for _, pieces in choices)


def _beside_height(below: Below, picture: float) -> float:
    """
    Return the height of a question's picture and what goes beside or below it, with the gap
    after them, as ``_draw_beside`` draws them, from the baseline under the question.
    """
    kind, choices = below
    if not _fits_beside(below):
        return picture + _height(below)
    column = 0.0
    if kind in ("row", "column"):
        column = sum(LINE_HEIGHT + 2 * _room(pieces) for _, pieces in choices)
    return max(picture, column) + PICTURE_AFTER


def _draw_beside(pdf: Canvas, data: LineQuestionData, below: Below, y: float) -> float:
    """
    Draw the question's table or grid in the left half, its top just above baseline ``y``, and
    what goes under the question beside it in the right half: lettered choices one under
    another from the top, or the answer line or two blanks at the bottom, leaving room above
    to work. Choices too wide for the right half go below the picture instead, as
    ``_draw_below`` draws them. A table to complete from a graph goes in the right half beside
    the graph. Returns the next baseline.
    """
    left = MARGIN + TEXT_INDENT
    top = y + PICTURE_RAISE
    bottom = top - _picture_height(data)
    right = left + PICTURE_WIDTH + PICTURE_GAP
    grid_shown, table_shown = _shown(data)
    if grid_shown:
        _draw_grid(pdf, data, left, top)
    if table_shown:
        _draw_line_table(pdf, data, right if grid_shown else left, top)
    kind, choices = below
    if not _fits_beside(below):
        return _draw_below(pdf, below, bottom - LINE_HEIGHT)
    end = bottom
    match kind:
        case "line":
            pdf.line(right, bottom, right + ANSWER_WIDTH, bottom)
        case "blanks":
            (first, _), (second, _) = choices
            pdf.setFont(FONT, TEXT_SIZE)
            pdf.drawString(right, bottom + BLANKS_APART, _blank(first, ANSWER_WIDTH))
            pdf.drawString(right, bottom, _blank(second, ANSWER_WIDTH))
        case "row" | "column":
            baseline = top - TEXT_SIZE
            for letter, pieces in choices:
                baseline -= _room(pieces)
                _draw_choice(pdf, right, baseline, letter, pieces)
                baseline -= LINE_HEIGHT + _room(pieces)
            end = min(bottom, baseline + LINE_HEIGHT - TEXT_SIZE)
        case _:  # tiles or a line to graph or table: nothing beside
            pass
    return end - PICTURE_AFTER


def _choice_lines(question: LineQuestion) -> list[Line]:
    """Return the lines of the graphs or tables a question offers to choose from, in order."""
    response = question.response
    assert isinstance(response, MultipleChoice)  # only multiple choice has choices
    return [option.line for option in response.options if isinstance(option, Equation)]


def _choices_height(question: LineQuestion) -> float:
    """
    Return the height of a question's graphs or tables to choose, with the gap after them, as
    ``_draw_choices`` draws them from the baseline under the question or its picture.
    """
    data = question.data
    count = len(_choice_lines(question))
    if data.asked is LineForm.GRAPH:
        rows = -(-count // 2)
        return rows * _choice_graph_height(data) + (rows - 1) * CHOICE_ROW_GAP + PICTURE_AFTER
    height = _choice_table_height(question)
    if data.table_across:
        return count * height + (count - 1) * CHOICE_TABLE_GAP + PICTURE_AFTER
    return height + PICTURE_AFTER


def _choice_graph_height(data: LineQuestionData) -> float:
    """Return the height of a graph to choose, from its letter's baseline to its grid's foot."""
    grid = data.grid
    assert grid is not None  # graphs to choose share a grid
    return (
        CHOICE_GRID_DROP
        + plane_height(GRID_WIDTH, grid.largest_x, grid.largest_y)
        + 2 * AXIS_OVERHANG
    )


def _choice_table_height(question: LineQuestion) -> float:
    """
    Return the height of each table to choose: its heading row, or its two rows across the page,
    and a row for each pair, each taller when any of the tables has a stacked fraction.
    """
    data = question.data
    cells = [choice_table_cells(data, line) for line in _choice_lines(question)]
    row_height = TABLE_FRACTION_ROW_HEIGHT if any(map(_has_fraction, cells)) else TABLE_ROW_HEIGHT
    if data.table_across:
        return 2 * row_height
    return TABLE_ROW_HEIGHT + len(data.table_xs) * row_height


def _has_fraction(cells: Sequence[Sequence[str | Pieces | None]]) -> bool:
    """Return whether any of a table's ``cells`` holds a stacked fraction."""
    return any(
        isinstance(piece, Fraction)
        for line in cells
        for cell in line
        if isinstance(cell, tuple)
        for piece in cell
    )


def _draw_choices(pdf: Canvas, question: LineQuestion, y: float) -> float:
    """
    Draw a question's graphs or tables to choose from baseline ``y``, each after or under its
    letter, and return the next baseline: graphs two to a row, each a question grid's size on
    the grid they share, the line on it with no points marked; tables set out down the page in
    a row, or across it one under another. Each table has the question's x-values.
    """
    data = question.data
    lines = _choice_lines(question)
    left = MARGIN + TEXT_INDENT
    pdf.setFont(FONT, TEXT_SIZE)
    if data.asked is LineForm.GRAPH:
        grid = data.grid
        assert grid is not None  # graphs to choose share a grid
        pitch = _choice_graph_height(data) + CHOICE_ROW_GAP
        for index, line in enumerate(lines):
            row, column = divmod(index, 2)
            x = left + column * (PICTURE_WIDTH + PICTURE_GAP)
            baseline = y - row * pitch
            pdf.setFont(FONT, TEXT_SIZE)
            pdf.drawString(x, baseline, choice_label(index))
            _draw_bare_line(pdf, line, grid, GRID_WIDTH, x, baseline - CHOICE_GRID_DROP)
        return y - _choices_height(question)
    height = _choice_table_height(question)
    row_height = (height if data.table_across else height - TABLE_ROW_HEIGHT) / (
        2 if data.table_across else len(data.table_xs)
    )
    for index, line in enumerate(lines):
        xs, ys = choice_table_cells(data, line)
        if data.table_across:
            top = y + PICTURE_RAISE - index * (height + CHOICE_TABLE_GAP)
            x = left
        else:
            top = y + PICTURE_RAISE
            x = left + index * TEXT_WIDTH / len(lines)
        pdf.setFont(FONT, TEXT_SIZE)
        pdf.drawString(x, top - PICTURE_RAISE, choice_label(index))
        table_left = x + CHOICE_INDENT
        if data.table_across:
            room = TEXT_WIDTH - CHOICE_INDENT - TABLE_HEADING_WIDTH
            cell = min(TABLE_CELL_WIDTH, room / (len(xs) - 1))
            draw_table(
                pdf,
                table_left,
                top,
                [TABLE_HEADING_WIDTH, *([cell] * (len(xs) - 1))],
                [row_height] * 2,
                [list(xs), list(ys)],
                heading_column=True,
                heading_size=TABLE_SIZE,
                body_size=TABLE_SIZE,
            )
            continue
        width = min(TABLE_COLUMN_WIDTH, (TEXT_WIDTH / len(lines) - CHOICE_INDENT - 8) / 2)
        draw_table(
            pdf,
            table_left,
            top,
            [width] * 2,
            [TABLE_ROW_HEIGHT, *([row_height] * (len(xs) - 1))],
            [[x_cell, y_cell] for x_cell, y_cell in zip(xs, ys, strict=True)],
            heading_row=True,
            heading_size=TABLE_SIZE,
            body_size=TABLE_SIZE,
        )
    return y - _choices_height(question)


def _draw_bare_line(
    pdf: Canvas, line: Line, grid: Grid, width: float, left: float, top: float
) -> None:
    """
    Draw ``line`` across ``grid`` drawn ``width`` wide, with no points marked, the axes'
    top-left overhang at (``left``, ``top``).
    """
    plane = draw_coordinate_plane(
        pdf,
        left + AXIS_OVERHANG,
        top - AXIS_OVERHANG,
        width,
        grid.largest_x,
        grid.largest_y,
        grid.step,
    )
    draw_line(pdf, plane, line.a, line.b, line.c)


def _bank_picture(data: LineQuestionData) -> BankPicture:
    """
    Return a question's answer as a picture for a tiles sheet's bank: its line on its grid, a
    question grid's size, with no points marked, or its table, filled in.
    """
    grid = data.grid
    if data.asked is LineForm.GRAPH and grid is not None:
        height = plane_height(GRID_WIDTH, grid.largest_x, grid.largest_y) + 2 * AXIS_OVERHANG
        return BankPicture(
            PICTURE_WIDTH,
            height,
            lambda pdf, left, top: _draw_bare_line(pdf, data.answer, grid, GRID_WIDTH, left, top),
        )
    return BankPicture(
        PICTURE_WIDTH,
        _table_height(data),
        lambda pdf, left, top: _draw_line_table(pdf, data, left, top, filled=True),
    )


def _draw_line_table(
    pdf: Canvas, data: LineQuestionData, left: float, top: float, filled: bool = False
) -> None:
    """
    Draw the question's table with its top-left corner at (``left``, ``top``): down the page in
    two columns, x and y, or across it in two rows, the cells a table to complete leaves out
    empty, unless ``filled``.
    """
    xs, ys = table_cells(data, filled)
    row_height = _table_row_height(data)
    if data.table_across:
        cell = min(TABLE_CELL_WIDTH, (PICTURE_WIDTH - TABLE_HEADING_WIDTH) / (len(xs) - 1))
        widths = [TABLE_HEADING_WIDTH, *([cell] * (len(xs) - 1))]
        cells = [list(xs), list(ys)]
        draw_table(
            pdf,
            left,
            top,
            widths,
            [row_height] * 2,
            cells,
            heading_column=True,
            heading_size=TABLE_SIZE,
            body_size=TABLE_SIZE,
        )
        return
    draw_table(
        pdf,
        left,
        top,
        [TABLE_COLUMN_WIDTH] * 2,
        [TABLE_ROW_HEIGHT, *([row_height] * (len(xs) - 1))],
        [[x, y] for x, y in zip(xs, ys, strict=True)],
        heading_row=True,
        heading_size=TABLE_SIZE,
        body_size=TABLE_SIZE,
    )


def _draw_grid(pdf: Canvas, data: LineQuestionData, left: float, top: float) -> None:
    """
    Draw the question's grid with its axes' top-left overhang at (``left``, ``top``) and, for a
    graph, the line on it through its two marked points, labelled with their coordinates when
    ``data.labelled`` says, the labels on either side of the line.
    """
    grid, line = data.grid, data.answer
    assert grid is not None  # only a question with a grid has a picture that isn't a table
    plane = draw_coordinate_plane(
        pdf,
        left + AXIS_OVERHANG,
        top - AXIS_OVERHANG,
        GRID_WIDTH,
        grid.largest_x,
        grid.largest_y,
        grid.step,
    )
    if data.given is not LineForm.GRAPH:
        return
    draw_line(pdf, plane, line.a, line.b, line.c)
    for point, side in zip(data.points, (1, -1), strict=False):
        label = inline(point_pieces(point, data.numbers)) if data.labelled else None
        # (a, b) is at right angles to the line ax + by = c, so a label goes off it either way
        draw_point(pdf, plane, point, label, (side * line.a, side * line.b))


def _key_picture_height(data: LineQuestionData) -> float:
    """Return the height of a line to graph's grid, or a filled table, in the answer key."""
    grid = data.grid
    if data.asked is LineForm.GRAPH and grid is not None:
        return plane_height(KEY_GRID_WIDTH, grid.largest_x, grid.largest_y) + 2 * AXIS_OVERHANG
    return _table_height(data)


def _table_height(data: LineQuestionData) -> float:
    """
    Return the height of the question's table: its heading row, or its two rows across the
    page, and a row for each pair, each taller when the table has a stacked fraction.
    """
    row_height = _table_row_height(data)
    if data.table_across:
        return 2 * row_height
    return TABLE_ROW_HEIGHT + len(data.table_xs) * row_height


def _table_row_height(data: LineQuestionData) -> float:
    """Return the height of the rows of the question's table, filled in, that hold numbers."""
    xs, ys = table_cells(data, filled=True)
    fractions = any(
        isinstance(piece, Fraction)
        for cell in (*xs, *ys)
        if isinstance(cell, tuple)
        for piece in cell
    )
    return TABLE_FRACTION_ROW_HEIGHT if fractions else TABLE_ROW_HEIGHT


def _draw_key_picture(pdf: Canvas, data: LineQuestionData, left: float, top: float) -> None:
    """
    Draw the answer to a line to graph or a table to complete, with its top-left corner at
    (``left``, ``top``): the line on a smaller grid through its key points, labelled with their
    coordinates on either side of it, or the table with every cell filled in.
    """
    grid, line = data.grid, data.answer
    if data.asked is not LineForm.GRAPH or grid is None:
        _draw_line_table(pdf, data, left, top, filled=True)
        return
    plane = draw_coordinate_plane(
        pdf,
        left + AXIS_OVERHANG,
        top - AXIS_OVERHANG,
        KEY_GRID_WIDTH,
        grid.largest_x,
        grid.largest_y,
        grid.step,
    )
    draw_line(pdf, plane, line.a, line.b, line.c)
    for point, side in zip(data.key_points, (1, -1), strict=False):
        label = inline(point_pieces(point, data.numbers))
        draw_point(pdf, plane, point, label, (side * line.a, side * line.b))


def _draw_choice(pdf: Canvas, x: float, y: float, letter: str, pieces: Pieces) -> None:
    """Draw a choice's letter at ``x`` and the choice beside it, on baseline ``y``."""
    pdf.setFont(FONT, TEXT_SIZE)
    pdf.drawString(x, y, letter)
    draw_pieces(pdf, x + CHOICE_INDENT, y, pieces, TEXT_SIZE)


def _solution(question: LineQuestion) -> Pieces | LineQuestionData:
    """
    Return the question's answer for the key, after its letter if it's multiple choice, a
    statement written short, or for a line to graph or a table to complete, its data, which the
    key draws; a graph or table to choose has only its letter.
    """
    response = question.response
    if question.data.asked in (LineForm.GRAPH, LineForm.TABLE):
        if isinstance(response, MultipleChoice):
            return (correct_letters(response),)
        return question.data
    if isinstance(response, MultipleChoice):
        (correct,) = response.correct_indexes
        answer = response.options[correct]
        option = (
            answer_pieces(question.data)
            if isinstance(answer, Stated)
            else choice_pieces(question.data, answer)
        )
        return (f"{correct_letters(response)}) ", *option)
    return answer_pieces(question.data)


def _room(pieces: Pieces) -> float:
    """Return the extra space a line of ``pieces`` needs above and below: some for a fraction."""
    return FRACTION_ROOM if any(isinstance(piece, Fraction) for piece in pieces) else 0


def _draw_answer_key(
    pdf: Canvas, header: Header, solutions: Sequence[Pieces | LineQuestionData]
) -> None:
    """
    Draw the answer key, starting on a new page, with each solution numbered, as
    ``draw_answer_key`` does for text, its fractions stacked; a line to graph drawn on a
    smaller grid through its key points, labelled, and a table to complete filled in. A
    solution that would run past the bottom margin starts on the next page.
    """
    key_header = replace(header, title=f"{header.title}: Answer Key", name_line=False)
    pdf.showPage()
    y = start_page(pdf, key_header)
    for number, solution in enumerate(solutions, start=1):
        if isinstance(solution, LineQuestionData):
            height = _key_picture_height(solution)
            if y + PICTURE_RAISE - height < MARGIN:
                pdf.showPage()
                y = start_page(pdf, key_header)
            pdf.setFont(FONT, TEXT_SIZE)
            pdf.drawString(MARGIN, y, f"{number}.")
            _draw_key_picture(pdf, solution, MARGIN + TEXT_INDENT, y + PICTURE_RAISE)
            y -= height - PICTURE_RAISE + KEY_PICTURE_GAP
            continue
        room = _room(solution)
        if y - 2 * room < MARGIN + LINE_HEIGHT:
            pdf.showPage()
            y = start_page(pdf, key_header)
        y -= room
        pdf.setFont(FONT, TEXT_SIZE)
        pdf.drawString(MARGIN, y, f"{number}.")
        draw_pieces(pdf, MARGIN + TEXT_INDENT, y, solution, TEXT_SIZE)
        y -= LINE_HEIGHT + room
