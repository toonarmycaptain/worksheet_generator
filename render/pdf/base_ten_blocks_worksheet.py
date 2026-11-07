"""
PDF worksheets of questions shown with base-ten blocks, with an optional answer key page.

The first page has the key to the blocks under its header. Each question has its number and
prompt, then its blocks. A number to write has "=" and a box for the answer beside its blocks. A
sum or difference has a rule under its blocks, then a label and the box: "Sum =", or for a
difference its equation, which says how many blocks to cross out. A sheet for the self-check
tiles case has no boxes, rules or labels, so a difference notes beside its blocks how many to
cross out, and the sheet ends with a page for the answer bank and pattern.
"""

from collections.abc import Sequence
from typing import BinaryIO, assert_never

from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.base_ten_blocks import (
    BlocksDiagram,
    BlocksQuestionData,
    blocks_answer_label,
    blocks_prompt,
    blocks_question_diagram,
    blocks_solution,
    blocks_tile_question,
)
from core.basic_operations.data import BasicOperationQuestionData
from core.placevalue.data import PlaceValueQuestionData
from core.question import FreeResponse, Question
from render.pdf.diagrams import (
    BLOCKS_KEY_HEIGHT,
    COLOUR_BLOCKS,
    GREY_BLOCKS,
    BlockColours,
    blocks_height,
    draw_blocks,
    draw_blocks_key,
)
from render.pdf.page import (
    BOLD_FONT,
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

KEY_RAISE = 10  # the key's top is level with the top of the first line's capitals
KEY_GAP = 26  # from the bottom of the key down to the first question's baseline
BLOCKS_RAISE = 6  # the blocks' top is this far above the next text baseline
QUESTION_GAP = 22  # from the bottom of a question down to the next question's baseline
BOX_WIDTH = 70
BOX_HEIGHT = 26
BOX_CORNER_RADIUS = 4
BOX_COLOUR = HexColor("#4a5568")  # dark grey
LABEL_GAP = 8  # from the blocks to "=", and from a label to its box
LABEL_RAISE = 8  # from the bottom of the box up to its label's baseline
RULE_DROP = 12  # from the bottom of the blocks down to the rule
RULE_LENGTH = 250  # from the left margin
RULE_WIDTH = 1.5
RULE_COLOUR = HexColor("#2d3748")  # near black
ANSWER_DROP = 34  # from the rule down to the bottom of the box


def render_base_ten_blocks_worksheet(
    questions: Sequence[Question[BlocksQuestionData, FreeResponse]],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    slot_of: Sequence[int] | None,
    black_and_white: bool = False,
) -> None:
    """
    Render questions shown with base-ten blocks, and the answer key if requested, to ``path``.

    The blocks are grey when ``black_and_white`` is set. A question that would run past the
    bottom margin starts on the next page. The answer key gives each number to write, and each
    sum or difference's equation and answer. ``path`` is a filename or a binary file-like object.

    With ``slot_of``, the sheet is for the self-check tiles case: the questions have no boxes,
    and the answer bank and pattern follow on a page of their own. ``slot_of[i]`` is the slot of
    question i + 1's answer, as in ``core.self_check_tiles``, so there are at most 12 questions,
    and their answers must be distinct. The answer key adds each answer's slot letter.
    """
    pdf = new_pdf(path, header.title)
    boxes = slot_of is None
    colours = GREY_BLOCKS if black_and_white else COLOUR_BLOCKS

    top = start_page(pdf, header) + KEY_RAISE
    draw_blocks_key(pdf, MARGIN, top, colours)
    y = top - BLOCKS_KEY_HEIGHT - KEY_GAP
    for number, question in enumerate(questions, start=1):
        lines = wrap(blocks_prompt(question.data), TEXT_SIZE, TEXT_WIDTH)
        diagram = blocks_question_diagram(question.data)
        body = _body_height(question.data, diagram, boxes)
        if y - (len(lines) * LINE_HEIGHT - BLOCKS_RAISE + body) < MARGIN:
            pdf.showPage()
            y = start_page(pdf, header)
        y = _draw_question(pdf, number, question.data, lines, diagram, boxes, colours, y)

    if slot_of is None:
        solutions = [blocks_solution(question.data) for question in questions]
    else:
        tile_questions = [blocks_tile_question(question.data) for question in questions]
        pdf.showPage()
        start_page(pdf, header)
        answers = [tile_question.answer for tile_question in tile_questions]
        draw_tiles(pdf, answers, slot_of, FIRST_LINE_Y - BANK_HEADING_HEIGHT)
        solutions = tile_solutions(tile_questions, slot_of)
    if answer_key:
        draw_answer_key(pdf, header, solutions)

    pdf.save()


def _body_height(data: BlocksQuestionData, diagram: BlocksDiagram, boxes: bool) -> float:
    """
    Return the height of the question below its prompt: its blocks, and with ``boxes`` the box
    beside them, or the rule and box below them.
    """
    height = blocks_height(diagram)
    if not boxes:
        return height
    match data:
        case PlaceValueQuestionData():
            return max(height, BOX_HEIGHT)
        case BasicOperationQuestionData():
            return height + RULE_DROP + ANSWER_DROP
        case _:
            assert_never(data)


def _draw_question(
    pdf: Canvas,
    number: int,
    data: BlocksQuestionData,
    lines: list[str],
    diagram: BlocksDiagram,
    boxes: bool,
    colours: BlockColours,
    y: float,
) -> float:
    """
    Draw one question from its number down, with its answer box if ``boxes`` is set, and return
    the next question's baseline.
    """
    pdf.setFont(FONT, TEXT_SIZE)
    pdf.drawString(MARGIN, y, f"{number}.")
    for line in lines:
        pdf.drawString(MARGIN + TEXT_INDENT, y, line)
        y -= LINE_HEIGHT

    x = MARGIN + TEXT_INDENT
    top = y + BLOCKS_RAISE
    height = blocks_height(diagram)
    bottom = top - _body_height(data, diagram, boxes)
    match data:
        case PlaceValueQuestionData():
            # the blocks and the box are centred on each other
            space = top - bottom
            right = draw_blocks(pdf, x, top - (space - height) / 2, diagram, colours, note=False)
            if boxes:
                label = blocks_answer_label(data)
                _draw_answer(pdf, right + LABEL_GAP, bottom + (space - BOX_HEIGHT) / 2, label)
        case BasicOperationQuestionData():
            # without boxes there is no equation, so the note says how many to cross out
            draw_blocks(pdf, x, top, diagram, colours, note=not boxes)
            if boxes:
                rule_y = top - height - RULE_DROP
                pdf.saveState()
                pdf.setStrokeColor(RULE_COLOUR)
                pdf.setLineWidth(RULE_WIDTH)
                pdf.line(MARGIN, rule_y, MARGIN + RULE_LENGTH, rule_y)
                pdf.restoreState()
                _draw_answer(pdf, x, bottom, blocks_answer_label(data))
        case _:
            assert_never(data)
    return bottom - QUESTION_GAP


def _draw_answer(pdf: Canvas, x: float, box_bottom: float, label: str) -> None:
    """Draw ``label`` from ``x``, then the box for the answer, with its bottom at ``box_bottom``."""
    pdf.saveState()
    pdf.setFont(BOLD_FONT, TEXT_SIZE)
    pdf.setFillColor("black")
    pdf.drawString(x, box_bottom + LABEL_RAISE, label)
    box_x = x + stringWidth(label, BOLD_FONT, TEXT_SIZE) + LABEL_GAP
    pdf.setStrokeColor(BOX_COLOUR)
    pdf.setLineWidth(1)
    pdf.roundRect(box_x, box_bottom, BOX_WIDTH, BOX_HEIGHT, BOX_CORNER_RADIUS, fill=0)
    pdf.restoreState()
