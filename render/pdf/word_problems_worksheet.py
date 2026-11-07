"""
PDF worksheets of word problems, each drawn with the sheet's representation, with an optional answer
key page.

The first page has the representation's instruction under its header, and for base-ten blocks a key
to the blocks. Each problem has its number and wording, a hint if the representation has one and
hints aren't turned off, the representation, and an answer line. A text-only problem's
representation is a box to show the work in. A number line's last box is its answer, so it has no
answer line. A sheet for the self-check tiles case has no answer lines, and ends with a page for the
answer bank and pattern.
"""

from collections.abc import Sequence
from typing import BinaryIO, assert_never

from reportlab.lib.colors import HexColor, gray
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.base_ten_blocks import blocks_diagram
from core.basic_operations.data import BasicOperationQuestionData
from core.basic_operations.representation import (
    EqualStripDiagram,
    Representation,
    StripDiagram,
    basic_operation_tile_question,
    equation,
    hint,
    instruction,
    number_line_jumps,
    stem,
    strip_diagram,
)
from core.question import Question
from render.pdf.diagrams import (
    BLOCKS_KEY_HEIGHT,
    COLOUR_BLOCKS,
    GREY_BLOCKS,
    NUMBER_LINE_HEIGHT,
    STRIP_HEIGHT,
    BlockColours,
    blocks_height,
    draw_blocks,
    draw_blocks_key,
    draw_equal_strip,
    draw_number_line,
    draw_strip,
)
from render.pdf.page import (
    BOLD_FONT,
    CONTENT_WIDTH,
    FIRST_LINE_Y,
    FONT,
    ITALIC_FONT,
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

INSTRUCTION_SIZE = 12
INSTRUCTION_LINE_HEIGHT = 16
INSTRUCTION_GAP = 10  # extra space between the instruction and the first problem
HINT_SIZE = 11
HINT_LINE_HEIGHT = 15
REPRESENTATION_RAISE = 6  # a representation's top is this far above the next text baseline
ANSWER_DROP = 26  # from the bottom of the representation down to the answer line, room to write
ANSWER_LABEL = "Answer: "
ANSWER_LINE_LENGTH = 120
PROBLEM_GAP = 22  # from the answer line, or the representation, down to the next problem's baseline
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
    representation: Representation,
    hints: bool,
    slot_of: Sequence[int] | None,
    black_and_white: bool = False,
) -> None:
    """
    Render word problems, each drawn with ``representation``, and the answer key if requested, to
    ``path``.

    Each problem's hint is left out when ``hints`` is False, and so is the note beside base-ten
    blocks saying how many to cross out. Base-ten blocks are grey when ``black_and_white`` is
    set. A problem that would run past the bottom margin starts on the next page. The answer key
    gives each problem's equation and answer. ``path`` is a filename or a binary file-like
    object.

    With ``slot_of``, the sheet is for the self-check tiles case: the problems have no answer
    lines, and the answer bank and pattern follow on a page of their own. ``slot_of[i]`` is the
    slot of question i + 1's answer, as in ``core.self_check_tiles``, so there are at most 12
    questions, and their answers must be distinct. The answer key adds each answer's slot letter.
    """
    pdf = new_pdf(path, header.title)
    answer_lines = slot_of is None and representation is not Representation.NUMBER_LINE
    colours = GREY_BLOCKS if black_and_white else COLOUR_BLOCKS

    operations = {question.data.operation for question in questions}
    y = _draw_instruction(pdf, instruction(representation, operations), start_page(pdf, header))
    if representation is Representation.BLOCKS:
        top = y + REPRESENTATION_RAISE
        draw_blocks_key(pdf, MARGIN, top, colours)
        y = top - BLOCKS_KEY_HEIGHT - PROBLEM_GAP
    for number, question in enumerate(questions, start=1):
        lines = wrap(stem(question.data), TEXT_SIZE, TEXT_WIDTH)
        hint_text = hint(question.data, representation) if hints else None
        hint_lines = wrap(hint_text, HINT_SIZE, TEXT_WIDTH) if hint_text is not None else []
        height = (
            len(lines) * LINE_HEIGHT
            + len(hint_lines) * HINT_LINE_HEIGHT
            - REPRESENTATION_RAISE
            + _representation_height(question.data, representation)
            + (ANSWER_DROP if answer_lines else 0)
        )
        if y - height < MARGIN:
            pdf.showPage()
            y = start_page(pdf, header)
        y = _draw_problem(
            pdf,
            number,
            question.data,
            lines,
            hint_lines,
            representation,
            answer_lines,
            hints,
            colours,
            y,
        )

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
    representation: Representation,
    answer_line: bool,
    hints: bool,
    colours: BlockColours,
    y: float,
) -> float:
    """
    Draw one problem, from its number down to its representation, followed by an answer line if
    ``answer_line`` is set, and return the y below it.

    ``hints`` and ``colours`` are for base-ten blocks: whether to write the note saying how many
    to cross out, and the blocks' colours.
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

    top = y + REPRESENTATION_RAISE
    _draw_representation(pdf, data, representation, MARGIN + TEXT_INDENT, top, hints, colours)

    bottom = top - _representation_height(data, representation)
    if answer_line:
        bottom -= ANSWER_DROP
        pdf.setFont(BOLD_FONT, TEXT_SIZE)
        pdf.drawString(MARGIN + TEXT_INDENT, bottom, ANSWER_LABEL)
        line_x = MARGIN + TEXT_INDENT + stringWidth(ANSWER_LABEL, BOLD_FONT, TEXT_SIZE)
        pdf.line(line_x, bottom, line_x + ANSWER_LINE_LENGTH, bottom)
    return bottom - PROBLEM_GAP


def _representation_height(
    data: BasicOperationQuestionData, representation: Representation
) -> float:
    match representation:
        case Representation.STRIP:
            return STRIP_HEIGHT
        case Representation.NONE:
            return WORK_BOX_HEIGHT
        case Representation.NUMBER_LINE:
            return NUMBER_LINE_HEIGHT
        case Representation.BLOCKS:
            return blocks_height(blocks_diagram(data))
        case _:
            assert_never(representation)


def _draw_representation(
    pdf: Canvas,
    data: BasicOperationQuestionData,
    representation: Representation,
    x: float,
    top: float,
    hints: bool,
    colours: BlockColours,
) -> None:
    """
    Draw the problem's representation with its top-left corner at (``x``, ``top``). ``hints`` and
    ``colours`` are for base-ten blocks, as in ``_draw_problem``.
    """
    match representation:
        case Representation.STRIP:
            diagram = strip_diagram(data)
            match diagram:
                case StripDiagram():
                    draw_strip(pdf, x, top, diagram)
                case EqualStripDiagram():
                    draw_equal_strip(pdf, x, top, diagram)
                case _:
                    assert_never(diagram)
        case Representation.NONE:
            _draw_work_box(pdf, x, top)
        case Representation.NUMBER_LINE:
            draw_number_line(pdf, x, top, data.operands[0], number_line_jumps(data))
        case Representation.BLOCKS:
            draw_blocks(pdf, x, top, blocks_diagram(data), colours, note=hints)
        case _:
            assert_never(representation)


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
