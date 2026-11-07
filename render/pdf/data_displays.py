"""
Displays of data sets, as plain functions over a canvas: frequency tables, pictographs, bar
graphs and dot plots of categories, and lists and number-line dot plots of numbers.

``draw_display`` fills a panel, given its top-left corner, width and height. Every word it draws
comes from ``core.discrete_data.representation``. A display to complete leaves out the counts at
``blanks``, the indexes of its categories or ticks.
"""

import math
from collections.abc import Collection, Sequence
from enum import StrEnum

from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.discrete_data.data import CategoricalData, DataDisplay, NumericalData
from core.discrete_data.representation import (
    axis_title,
    category_header,
    count_header,
    display_title,
    dot_plot_key,
    labels,
    pictograph_key,
)
from render.pdf.page import BOLD_FONT, FONT, ITALIC_FONT, wrap

OUTLINE_COLOUR = HexColor("#2d3748")  # near black
MARK_COLOUR = HexColor("#2b6cb0")  # blue: pictograph symbols and dot plot Xs
BAR_FILL = HexColor("#cfe3f7")  # light blue
HEADER_FILL = HexColor("#edf2f7")  # very light grey
GRID_COLOUR = HexColor("#cbd5e0")  # light grey
KEY_COLOUR = HexColor("#718096")  # grey, for a dot plot's "Each X = 1 student"

TITLE_SIZE = 10
TITLE_DROP = 10  # from the panel's top down to the title's baseline
BODY_DROP = 16  # from the panel's top down to the display under the title
SMALLEST_LABEL_SIZE = 6  # a label too wide for its space shrinks, down to this size

TABLE_WIDTH = 200  # at most; a table is centred in its panel
TABLE_LABEL_SHARE = 0.45  # of the table's width, for the categories' column
TABLE_ROW_HEIGHT = 20  # at most

PICTOGRAPH_LABEL_WIDTH = 66
PICTOGRAPH_ROW_HEIGHT = 24  # at most
SYMBOL_RADIUS = 7  # at most
SYMBOL_GAP = 3
KEY_LABEL = "Key:"
KEY_LABEL_WIDTH = 26  # from the key's left edge to its symbol

BAR_AXIS_WIDTH = 36  # left of the axis, for its numbers and title
BAR_SHARE = 0.6  # of each category's slot, for its bar
SMALLEST_INTERVAL_HEIGHT = 9  # a smaller interval labels every other line

X_STEP = 10.5  # between a dot plot's stacked Xs, at most
MOST_XS = 10  # a dot plot leaves room for this many Xs in a stack

LIST_SIZE = 11
LIST_LINE_HEIGHT = 16
LIST_CELL_WIDTH = 26
LIST_CELL_HEIGHT = 20
LIST_COLUMNS = 8  # at most, in a grid

NUMBER_LINE_INSET = 14  # from each end of the line to its first and last ticks
LABELLED_TICK_GAP = 13  # ticks closer than this label only every other number
ARROW_LENGTH = 5
ARROW_HALF_WIDTH = 3


class NumberListStyle(StrEnum):
    """How a list of numbers is shown. Values are stable identifiers for the API."""

    GRID = "grid"  # a grid of boxes, easy to cross off while counting
    COMMAS = "commas"  # separated by commas, in a box


def draw_display(
    pdf: Canvas,
    display: DataDisplay,
    dataset: CategoricalData | NumericalData,
    x: float,
    top: float,
    width: float,
    height: float,
    blanks: Collection[int],
    list_style: NumberListStyle,
) -> None:
    """
    Draw ``dataset`` as ``display`` in the panel whose top-left corner is (``x``, ``top``),
    leaving out the counts at ``blanks``. ``list_style`` is for a list.

    Raises ``ValueError`` if ``display`` can't show ``dataset``: a categorical data set is shown
    in a table, pictograph, bar graph or dot plot, and a numerical one in a list or a number-line
    dot plot.
    """
    pdf.saveState()
    _draw_title(pdf, x, top, width, display_title(dataset))
    match display, dataset:
        case DataDisplay.TABLE, CategoricalData():
            _draw_table(pdf, x, top, width, height, dataset, blanks)
        case DataDisplay.PICTOGRAPH, CategoricalData():
            _draw_pictograph(pdf, x, top, width, height, dataset, blanks)
        case DataDisplay.BAR_GRAPH, CategoricalData():
            _draw_bar_graph(pdf, x, top, width, height, dataset, blanks)
        case DataDisplay.DOT_PLOT, CategoricalData():
            _draw_dot_plot(pdf, x, top, width, height, dataset, blanks)
        case DataDisplay.LIST, NumericalData():
            _draw_list(pdf, x, top, width, dataset.values, list_style)
        case DataDisplay.NUMBER_LINE_DOT_PLOT, NumericalData():
            _draw_number_line_dot_plot(pdf, x, top, width, height, dataset, blanks)
        case _:
            raise ValueError(f"A {display} display can't show {type(dataset).__name__}.")
    pdf.restoreState()


def _draw_title(pdf: Canvas, x: float, top: float, width: float, title: str) -> None:
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, TITLE_SIZE)
    pdf.drawCentredString(x + width / 2, top - TITLE_DROP, title)


def _fit_font(pdf: Canvas, text: str, font: str, size: float, width: float) -> None:
    """Set ``font`` at ``size``, or smaller if needed for ``text`` to fit ``width``."""
    while size > SMALLEST_LABEL_SIZE and stringWidth(text, font, size) > width:
        size -= 0.5
    pdf.setFont(font, size)


def _draw_table(
    pdf: Canvas,
    x: float,
    top: float,
    width: float,
    height: float,
    dataset: CategoricalData,
    blanks: Collection[int],
) -> None:
    """A frequency table: a header row, then each category beside its count."""
    table_width = min(width, TABLE_WIDTH)
    table_x = x + (width - table_width) / 2
    label_width = table_width * TABLE_LABEL_SHARE
    count_centre = table_x + label_width + (table_width - label_width) / 2
    rows = len(dataset.counts) + 1
    row_height = min(TABLE_ROW_HEIGHT, (height - 18) / rows)
    table_top = top - BODY_DROP
    table_bottom = table_top - rows * row_height

    pdf.setFillColor(HEADER_FILL)
    pdf.rect(table_x, table_top - row_height, table_width, row_height, stroke=0, fill=1)
    pdf.setFillColor("black")
    header_baseline = table_top - row_height / 2 - 3
    category_heading = category_header(dataset)
    _fit_font(pdf, category_heading, BOLD_FONT, 9, label_width - 6)
    pdf.drawCentredString(table_x + label_width / 2, header_baseline, category_heading)
    count_heading = count_header(dataset)
    _fit_font(pdf, count_heading, BOLD_FONT, 9, table_width - label_width - 6)
    pdf.drawCentredString(count_centre, header_baseline, count_heading)
    for row, (label, count) in enumerate(zip(labels(dataset), dataset.counts, strict=True), 1):
        baseline = table_top - row * row_height - row_height / 2 - 3
        _fit_font(pdf, label, FONT, 10, label_width - 6)
        pdf.drawCentredString(table_x + label_width / 2, baseline, label)
        if row - 1 not in blanks:
            pdf.setFont(FONT, 10)
            pdf.drawCentredString(count_centre, baseline, str(count))

    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1)
    pdf.rect(table_x, table_bottom, table_width, rows * row_height, stroke=1, fill=0)
    pdf.line(table_x + label_width, table_top, table_x + label_width, table_bottom)
    for row in range(1, rows):
        row_y = table_top - row * row_height
        pdf.line(table_x, row_y, table_x + table_width, row_y)


def _draw_pictograph(
    pdf: Canvas,
    x: float,
    top: float,
    width: float,
    height: float,
    dataset: CategoricalData,
    blanks: Collection[int],
) -> None:
    """
    A pictograph: a row of stars for each category, each star worth the scale, and a half star
    for half of it, with the key under the rows.
    """
    rows = len(dataset.counts)
    grid_top = top - BODY_DROP
    row_height = min(PICTOGRAPH_ROW_HEIGHT, (height - BODY_DROP - 20) / rows)
    grid_bottom = grid_top - rows * row_height
    radius = min(SYMBOL_RADIUS, (row_height - 6) / 2)
    step = 2 * radius + SYMBOL_GAP
    first_symbol_x = x + PICTOGRAPH_LABEL_WIDTH + 6 + radius

    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1)
    pdf.rect(x, grid_bottom, width, rows * row_height, stroke=1, fill=0)
    pdf.line(x + PICTOGRAPH_LABEL_WIDTH, grid_top, x + PICTOGRAPH_LABEL_WIDTH, grid_bottom)
    for row, (label, count) in enumerate(zip(labels(dataset), dataset.counts, strict=True)):
        row_top = grid_top - row * row_height
        if row:
            pdf.setStrokeColor(GRID_COLOUR)
            pdf.line(x, row_top, x + width, row_top)
        pdf.setFillColor("black")
        _fit_font(pdf, label, FONT, 10, PICTOGRAPH_LABEL_WIDTH - 8)
        pdf.drawString(x + 5, row_top - row_height / 2 - 3.5, label)
        if row in blanks:
            continue
        whole, remainder = divmod(count, dataset.scale)
        for symbol in range(whole + (1 if remainder else 0)):
            centre_x = first_symbol_x + symbol * step
            _draw_star(pdf, centre_x, row_top - row_height / 2, radius, half=symbol == whole)

    key_text = pictograph_key(dataset)
    key_baseline = grid_bottom - 13
    key_width = KEY_LABEL_WIDTH + 2 * radius + 4 + stringWidth(key_text, BOLD_FONT, 9)
    key_x = x + (width - key_width) / 2
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 9)
    pdf.drawString(key_x, key_baseline, KEY_LABEL)
    _draw_star(pdf, key_x + KEY_LABEL_WIDTH + radius, key_baseline + 3, radius)
    pdf.setFillColor("black")
    pdf.drawString(key_x + KEY_LABEL_WIDTH + 2 * radius + 4, key_baseline, key_text)


def _draw_star(
    pdf: Canvas, centre_x: float, centre_y: float, radius: float, half: bool = False
) -> None:
    """Draw a five-pointed star, or with ``half`` only its left half."""
    points = []
    for k in range(10):
        angle = math.pi / 2 + k * math.pi / 5
        point_radius = radius if k % 2 == 0 else radius * 0.45
        points.append(
            (centre_x + point_radius * math.cos(angle), centre_y + point_radius * math.sin(angle))
        )
    pdf.saveState()
    if half:
        clip = pdf.beginPath()
        clip.rect(centre_x - radius - 1, centre_y - radius - 1, radius + 1, 2 * radius + 2)
        pdf.clipPath(clip, stroke=0, fill=0)
    star = pdf.beginPath()
    star.moveTo(*points[0])
    for point in points[1:]:
        star.lineTo(*point)
    star.close()
    pdf.setFillColor(MARK_COLOUR)
    pdf.drawPath(star, stroke=0, fill=1)
    pdf.restoreState()


def _draw_bar_graph(
    pdf: Canvas,
    x: float,
    top: float,
    width: float,
    height: float,
    dataset: CategoricalData,
    blanks: Collection[int],
) -> None:
    """
    A bar graph: a bar for each category on an axis with intervals of the scale, which goes one
    interval past the largest count. Bars may end between grid lines.
    """
    scale = dataset.scale
    axis_top_value = (max(dataset.counts) // scale + 1) * scale
    left, right = x + BAR_AXIS_WIDTH, x + width - 4
    bottom, plot_top = top - height + 16, top - 20
    intervals = axis_top_value // scale
    label_every = 1 if (plot_top - bottom) / intervals >= SMALLEST_INTERVAL_HEIGHT else 2

    def y_for(value: float) -> float:
        return bottom + (plot_top - bottom) * value / axis_top_value

    pdf.setLineWidth(0.6)
    for interval in range(intervals + 1):
        value = interval * scale
        pdf.setStrokeColor(GRID_COLOUR)
        pdf.line(left, y_for(value), right, y_for(value))
        if interval % label_every == 0:
            pdf.setFillColor("black")
            pdf.setFont(FONT, 7)
            pdf.drawRightString(left - 3, y_for(value) - 2.5, str(value))
    slot = (right - left) / len(dataset.counts)
    for index, (label, count) in enumerate(zip(labels(dataset), dataset.counts, strict=True)):
        centre = left + slot * (index + 0.5)
        if index not in blanks:
            pdf.setStrokeColor(OUTLINE_COLOUR)
            pdf.setFillColor(BAR_FILL)
            pdf.setLineWidth(1)
            bar_width = slot * BAR_SHARE
            pdf.rect(
                centre - bar_width / 2, bottom, bar_width, y_for(count) - bottom, stroke=1, fill=1
            )
        pdf.setFillColor("black")
        _fit_font(pdf, label, FONT, 8, slot - 2)
        pdf.drawCentredString(centre, bottom - 10, label)

    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1)
    pdf.line(left, bottom, right, bottom)
    pdf.line(left, bottom, left, plot_top)
    pdf.saveState()
    pdf.translate(x + 7, (bottom + plot_top) / 2)
    pdf.rotate(90)
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 7)
    pdf.drawCentredString(0, 0, count_header(dataset))
    pdf.restoreState()


def _draw_dot_plot(
    pdf: Canvas,
    x: float,
    top: float,
    width: float,
    height: float,
    dataset: CategoricalData,
    blanks: Collection[int],
) -> None:
    """A dot plot of categories: a column of Xs above each category's name, each X worth 1."""
    _draw_dot_plot_key(pdf, x, top, width, dot_plot_key(dataset))
    left, right = x + 6, x + width - 6
    baseline = top - height + 16
    x_step = min(X_STEP, (height - BODY_DROP - 36) / MOST_XS)  # clear of the key
    slot = (right - left) / len(dataset.counts)
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1)
    pdf.line(left, baseline, right, baseline)
    for index, (label, count) in enumerate(zip(labels(dataset), dataset.counts, strict=True)):
        column_x = left + slot * (index + 0.5)
        pdf.setStrokeColor(OUTLINE_COLOUR)
        pdf.line(column_x, baseline - 3, column_x, baseline + 3)
        pdf.setFillColor("black")
        _fit_font(pdf, label, FONT, 8, slot - 2)
        pdf.drawCentredString(column_x, baseline - 11, label)
        if index not in blanks:
            _draw_xs(pdf, column_x, baseline + 3, count, x_step)


def _draw_dot_plot_key(pdf: Canvas, x: float, top: float, width: float, key: str) -> None:
    pdf.setFillColor(KEY_COLOUR)
    pdf.setFont(ITALIC_FONT, 8)
    pdf.drawCentredString(x + width / 2, top - 21, key)


def _draw_xs(pdf: Canvas, centre_x: float, bottom: float, count: int, step: float) -> None:
    """Draw a stack of ``count`` Xs, the lowest with its baseline at ``bottom``."""
    pdf.setFillColor(MARK_COLOUR)
    pdf.setFont(BOLD_FONT, 9)
    for mark in range(count):
        pdf.drawCentredString(centre_x, bottom + mark * step, "X")


def _draw_list(
    pdf: Canvas,
    x: float,
    top: float,
    width: float,
    values: Sequence[int],
    style: NumberListStyle,
) -> None:
    """The numbers in order: in a grid of boxes, or separated by commas in a box."""
    list_top = top - 18
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(0.8)
    pdf.setFillColor("black")
    pdf.setFont(FONT, LIST_SIZE)
    match style:
        case NumberListStyle.COMMAS:
            lines = wrap(", ".join(map(str, values)), LIST_SIZE, width - 16)
            box_height = len(lines) * LIST_LINE_HEIGHT + 8
            pdf.roundRect(x, list_top - box_height, width, box_height, 4, stroke=1, fill=0)
            for line_number, line in enumerate(lines):
                pdf.drawString(x + 8, list_top - LIST_LINE_HEIGHT * (line_number + 1), line)
        case NumberListStyle.GRID:
            columns = min(LIST_COLUMNS, len(values), int((width - 4) // LIST_CELL_WIDTH))
            grid_x = x + (width - columns * LIST_CELL_WIDTH) / 2
            for index, value in enumerate(values):
                row, column = divmod(index, columns)
                cell_x = grid_x + column * LIST_CELL_WIDTH
                cell_top = list_top - row * LIST_CELL_HEIGHT
                pdf.rect(
                    cell_x,
                    cell_top - LIST_CELL_HEIGHT,
                    LIST_CELL_WIDTH,
                    LIST_CELL_HEIGHT,
                    stroke=1,
                    fill=0,
                )
                pdf.drawCentredString(
                    cell_x + LIST_CELL_WIDTH / 2, cell_top - LIST_CELL_HEIGHT / 2 - 4, str(value)
                )


def _draw_number_line_dot_plot(
    pdf: Canvas,
    x: float,
    top: float,
    width: float,
    height: float,
    dataset: NumericalData,
    blanks: Collection[int],
) -> None:
    """
    A dot plot on a number line: a tick for every number, even those with no Xs, and an X above
    a number for each time it is in the list. A crowded line labels only every other number.
    """
    _draw_dot_plot_key(pdf, x, top, width, dot_plot_key(dataset))
    left, right = x + 6, x + width - 6
    baseline = top - height + 30  # room for the numbers and the axis title
    ticks = dataset.ticks
    tick_gap = (right - left - 2 * NUMBER_LINE_INSET) / (len(ticks) - 1)
    tick_step = ticks[1] - ticks[0]
    x_step = min(X_STEP, (height - 60) / MOST_XS)  # clear of the key

    def tick_x(index: int) -> float:
        return left + NUMBER_LINE_INSET + tick_gap * index

    def labelled(index: int) -> bool:
        return tick_gap >= LABELLED_TICK_GAP or (ticks[index] // tick_step) % 2 == 0

    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setFillColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1)
    pdf.line(left, baseline, right, baseline)
    for tip, direction in ((left, 1), (right, -1)):
        arrow = pdf.beginPath()
        arrow.moveTo(tip, baseline)
        arrow.lineTo(tip + ARROW_LENGTH * direction, baseline + ARROW_HALF_WIDTH)
        arrow.lineTo(tip + ARROW_LENGTH * direction, baseline - ARROW_HALF_WIDTH)
        arrow.close()
        pdf.drawPath(arrow, fill=1, stroke=0)
    for index, (label, count) in enumerate(zip(labels(dataset), dataset.counts, strict=True)):
        tick_half = 4 if labelled(index) else 2.5
        pdf.setStrokeColor(OUTLINE_COLOUR)
        pdf.line(tick_x(index), baseline - tick_half, tick_x(index), baseline + tick_half)
        if labelled(index):
            pdf.setFillColor("black")
            pdf.setFont(FONT, 9)
            pdf.drawCentredString(tick_x(index), baseline - 13, label)
        if index not in blanks:
            _draw_xs(pdf, tick_x(index), baseline + 5, count, x_step)
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 8)
    pdf.drawCentredString((left + right) / 2, baseline - 25, axis_title(dataset))
