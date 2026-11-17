"""
Tables as plain functions over a canvas: a grid of cells, some of them shaded headings, such as
a frequency table or an input-output table.
"""

from collections.abc import Sequence

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from render.pdf.page import BOLD_FONT, FONT, fit_font

OUTLINE_COLOUR = HexColor("#2d3748")  # near black
HEADING_FILL = HexColor("#edf2f7")  # very light grey
CELL_PADDING = 3  # each side of a cell's text
LINE_GAP = 2  # between the lines of a cell's text, beyond the font size
TEXT_DROP = 3  # from the middle of a cell's lines down to the baseline of the middle line


def draw_table(
    pdf: Canvas,
    x: float,
    top: float,
    column_widths: Sequence[float],
    row_heights: Sequence[float],
    cells: Sequence[Sequence[str | None]],
    *,
    heading_row: bool = False,
    heading_column: bool = False,
    heading_size: float,
    body_size: float,
) -> None:
    """
    Draw a grid of cells with its top-left corner at (``x``, ``top``), and its lines in
    ``OUTLINE_COLOUR``.

    ``cells[row][column]`` is the text of that cell, or ``None`` for a cell left empty to be
    filled in; a newline in the text starts a new line. Each line is centred across its cell,
    the cell's lines together centred down it. The headings, in the first row with
    ``heading_row`` and in the first column with ``heading_column``, are shaded in
    ``HEADING_FILL`` and drawn in ``BOLD_FONT`` at ``heading_size``; the other cells in ``FONT``
    at ``body_size``. A line too wide for its cell is drawn smaller, as ``fit_font`` does.
    """
    width = sum(column_widths)
    height = sum(row_heights)
    lefts = [x + sum(column_widths[:column]) for column in range(len(column_widths))]
    tops = [top - sum(row_heights[:row]) for row in range(len(row_heights))]

    pdf.setFillColor(HEADING_FILL)
    if heading_row:
        pdf.rect(x, top - row_heights[0], width, row_heights[0], stroke=0, fill=1)
    if heading_column:
        pdf.rect(x, top - height, column_widths[0], height, stroke=0, fill=1)
    pdf.setFillColor("black")
    for row, texts in enumerate(cells):
        for column, text in enumerate(texts):
            if text is None:
                continue
            heading = (heading_row and row == 0) or (heading_column and column == 0)
            font, size = (BOLD_FONT, heading_size) if heading else (FONT, body_size)
            lines = text.split("\n")
            centre = lefts[column] + column_widths[column] / 2
            line_height = size + LINE_GAP
            baseline = tops[row] - row_heights[row] / 2 + (len(lines) - 1) * line_height / 2
            for line in lines:
                fit_font(pdf, line, font, size, column_widths[column] - 2 * CELL_PADDING)
                pdf.drawCentredString(centre, baseline - TEXT_DROP, line)
                baseline -= line_height

    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1)
    pdf.rect(x, top - height, width, height, stroke=1, fill=0)
    for left in lefts[1:]:
        pdf.line(left, top, left, top - height)
    for row_top in tops[1:]:
        pdf.line(x, row_top, x + width, row_top)
