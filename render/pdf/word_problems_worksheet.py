"""
PDF worksheets of word problems, each drawn with the sheet's picture, with an optional answer key
page.

The first page has the picture's instruction under its header. Each problem has its number and
wording, a hint if the picture has one and hints aren't turned off, the picture, and an answer
line. A text-only problem's picture is a box to show the work in. A sheet for the self-check
tiles case has no answer lines, and ends with a page for the answer bank and pattern.
"""

from collections.abc import Sequence
from typing import BinaryIO, assert_never

from reportlab.lib.colors import HexColor, gray
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.basic_operations.data import BasicOperationQuestionData
from core.basic_operations.representation import (
    EqualStripDiagram,
    Picture,
    StripDiagram,
    basic_operation_tile_question,
    equation,
    hint,
    instruction,
    stem,
    strip_diagram,
)
from core.question import Question
from render.pdf.diagrams import STRIP_HEIGHT, draw_equal_strip, draw_strip
from render.pdf.page import (
    BOLD_FONT,
    CONTENT_WIDTH,
    FIRST_LINE_Y,
    FONT,
    LINE_HEIGHT,
    MARGIN,
    TEXT_INDENT,
    TEXT_SIZE,
    TEXT_WIDTH,
    Header,
    draw_answer_key,
    new_pdf,
    start_page,
    wrap,
)
from render.pdf.tiles import BANK_HEADING_HEIGHT, draw_tiles, tile_solutions

ITALIC_FONT = "Helvetica-Oblique"  # same widths as FONT, so wrap measures it correctly
INSTRUCTION_SIZE = 12
INSTRUCTION_LINE_HEIGHT = 16
INSTRUCTION_GAP = 10  # extra space between the instruction and the first problem
HINT_SIZE = 11
HINT_LINE_HEIGHT = 15
PICTURE_RAISE = 6  # a picture's top is this far above the next text baseline
ANSWER_DROP = 26  # from the bottom of the picture down to the answer line, room to write
ANSWER_LABEL = "Answer: "
ANSWER_LINE_LENGTH = 120
PROBLEM_GAP = 22  # from the answer line, or the picture, down to the next problem's baseline
# Text only: the box to show the work in, as wide as the text, with a label in its top-left corner
WORK_BOX_HEIGHT = 60
WORK_BOX_CORNER_RADIUS = 4
WORK_BOX_COLOUR = HexColor("#cbd5e0")  # light grey
WORK_BOX_LABEL = "Show your work"
WORK_BOX_LABEL_SIZE = 9
WORK_BOX_LABEL_COLOUR = HexColor("#a0aec0")  # grey
WORK_BOX_LABEL_INSET = 5  # from the box's left edge to the label
WORK_BOX_LABEL_DROP = 12  # from the box's top down to the label's baseline


def render_word_problems_worksheet(
    questions: Sequence[Question[BasicOperationQuestionData]],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    picture: Picture,
    hints: bool,
    slot_of: Sequence[int] | None,
) -> None:
    """
    Render word problems, each drawn with ``picture``, and the answer key if requested, to
    ``path``.

    Each problem's hint is left out when ``hints`` is False. A problem that would run past the
    bottom margin starts on the next page. The answer key gives each problem's equation and
    answer. ``path`` is a filename or a binary file-like object.

    With ``slot_of``, the sheet is for the self-check tiles case: the problems have no answer
    lines, and the answer bank and pattern follow on a page of their own. ``slot_of[i]`` is the
    slot of question i + 1's answer, as in ``core.self_check_tiles``, so there are at most 12
    questions, and their answers must be distinct. The answer key adds each answer's slot letter.
    """
    pdf = new_pdf(path, header.title)
    answer_lines = slot_of is None

    operations = {question.data.operation for question in questions}
    y = _draw_instruction(pdf, instruction(picture, operations), start_page(pdf, header))
    for number, question in enumerate(questions, start=1):
        lines = wrap(stem(question.data), TEXT_SIZE, TEXT_WIDTH)
        hint_text = hint(question.data, picture) if hints else None
        hint_lines = wrap(hint_text, HINT_SIZE, TEXT_WIDTH) if hint_text is not None else []
        height = (
            len(lines) * LINE_HEIGHT
            + len(hint_lines) * HINT_LINE_HEIGHT
            - PICTURE_RAISE
            + _picture_height(picture)
            + (ANSWER_DROP if answer_lines else 0)
        )
        if y - height < MARGIN:
            pdf.showPage()
            y = start_page(pdf, header)
        y = _draw_problem(pdf, number, question.data, lines, hint_lines, picture, answer_lines, y)

    if slot_of is None:
        solutions = [
            f"{equation(question.data)} = {question.data.answer}" for question in questions
        ]
    else:
        tile_questions = [basic_operation_tile_question(question.data) for question in questions]
        pdf.showPage()
        start_page(pdf, header)
        answers = [tile_question.answer for tile_question in tile_questions]
        draw_tiles(pdf, answers, slot_of, FIRST_LINE_Y - BANK_HEADING_HEIGHT)
        solutions = tile_solutions(tile_questions, slot_of)
    if answer_key:
        draw_answer_key(pdf, header, solutions)

    pdf.save()


def _draw_instruction(pdf: Canvas, text: str, y: float) -> float:
    """Draw the sheet's instruction from baseline ``y``, and return the first problem's baseline."""
    pdf.setFont(FONT, INSTRUCTION_SIZE)
    for line in wrap(text, INSTRUCTION_SIZE, CONTENT_WIDTH):
        pdf.drawString(MARGIN, y, line)
        y -= INSTRUCTION_LINE_HEIGHT
    return y - INSTRUCTION_GAP


def _draw_problem(
    pdf: Canvas,
    number: int,
    data: BasicOperationQuestionData,
    lines: list[str],
    hint_lines: list[str],
    picture: Picture,
    answer_line: bool,
    y: float,
) -> float:
    """
    Draw one problem, from its number down to its picture, followed by an answer line if
    ``answer_line`` is set, and return the y below it.
    """
    pdf.setFont(FONT, TEXT_SIZE)
    pdf.drawString(MARGIN, y, f"{number}.")
    for line in lines:
        pdf.drawString(MARGIN + TEXT_INDENT, y, line)
        y -= LINE_HEIGHT
    pdf.setFont(ITALIC_FONT, HINT_SIZE)
    pdf.setFillColor(gray)
    for line in hint_lines:
        pdf.drawString(MARGIN + TEXT_INDENT, y, line)
        y -= HINT_LINE_HEIGHT
    pdf.setFillColor("black")

    top = y + PICTURE_RAISE
    _draw_picture(pdf, data, picture, MARGIN + TEXT_INDENT, top)

    bottom = top - _picture_height(picture)
    if answer_line:
        bottom -= ANSWER_DROP
        pdf.setFont(BOLD_FONT, TEXT_SIZE)
        pdf.drawString(MARGIN + TEXT_INDENT, bottom, ANSWER_LABEL)
        line_x = MARGIN + TEXT_INDENT + stringWidth(ANSWER_LABEL, BOLD_FONT, TEXT_SIZE)
        pdf.line(line_x, bottom, line_x + ANSWER_LINE_LENGTH, bottom)
    return bottom - PROBLEM_GAP


def _picture_height(picture: Picture) -> float:
    match picture:
        case Picture.STRIP:
            return STRIP_HEIGHT
        case Picture.NONE:
            return WORK_BOX_HEIGHT
        case Picture.NUMBER_LINE | Picture.BLOCKS:
            raise NotImplementedError(f"The {picture} picture is not built yet.")
        case _:
            assert_never(picture)


def _draw_picture(
    pdf: Canvas, data: BasicOperationQuestionData, picture: Picture, x: float, top: float
) -> None:
    """Draw the problem's picture with its top-left corner at (``x``, ``top``)."""
    match picture:
        case Picture.STRIP:
            diagram = strip_diagram(data)
            match diagram:
                case StripDiagram():
                    draw_strip(pdf, x, top, diagram)
                case EqualStripDiagram():
                    draw_equal_strip(pdf, x, top, diagram)
                case _:
                    assert_never(diagram)
        case Picture.NONE:
            _draw_work_box(pdf, x, top)
        case Picture.NUMBER_LINE | Picture.BLOCKS:
            raise NotImplementedError(f"The {picture} picture is not built yet.")
        case _:
            assert_never(picture)


def _draw_work_box(pdf: Canvas, x: float, top: float) -> None:
    """Draw the box to show the work in, with its top-left corner at (``x``, ``top``)."""
    pdf.saveState()
    pdf.setStrokeColor(WORK_BOX_COLOUR)
    pdf.setLineWidth(1)
    pdf.roundRect(
        x, top - WORK_BOX_HEIGHT, TEXT_WIDTH, WORK_BOX_HEIGHT, WORK_BOX_CORNER_RADIUS, fill=0
    )
    pdf.setFont(ITALIC_FONT, WORK_BOX_LABEL_SIZE)
    pdf.setFillColor(WORK_BOX_LABEL_COLOUR)
    pdf.drawString(x + WORK_BOX_LABEL_INSET, top - WORK_BOX_LABEL_DROP, WORK_BOX_LABEL)
    pdf.restoreState()
