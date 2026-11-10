"""
PDF worksheets of word problems, each drawn with the sheet's representation, with an optional answer
key page.

The first page has the representation's instruction under its header, and for base-ten blocks a key
to the blocks. Each problem has its number and wording, a hint if the representation has one and
hints aren't turned off, the representation, and an answer line. A text-only problem's
representation is a box to show the work in, unless the boxes are left out. A number line's last
box is its answer, so it has no answer line. A problem whose equation is chosen has its lettered
equations instead, in rows of two. A two-step problem is shown only with strip diagrams, as one
bar under its whole, or as text only. A sheet for the self-check tiles case has no answer lines,
and ends with a page for the answer bank and pattern.
"""

from collections.abc import Sequence
from typing import BinaryIO, assert_never

from reportlab.lib.colors import HexColor, gray
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.base_ten_blocks import blocks_diagram
from core.basic_operations.data import BasicOperationQuestionData, TwoStepQuestionData
from core.basic_operations.representation import (
    REPRESENTATION_NAMES,
    TWO_STEP_REPRESENTATIONS,
    Representation,
    WordProblemQuestion,
    basic_operation_tile_question,
    hint,
    instruction,
    number_line_jumps,
    solved_equation,
    solved_steps,
    stem,
    strip_diagram,
    two_step_strip,
    two_step_tile_question,
)
from core.question import FreeResponse, MultipleChoice
from core.self_check_tiles import TileQuestion
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
    draw_number_line,
    draw_strip_diagram,
)
from render.pdf.page import (
    BOLD_FONT,
    FONT,
    ITALIC_FONT,
    LINE_HEIGHT,
    MARGIN,
    TEXT_INDENT,
    TEXT_SIZE,
    TEXT_WIDTH,
    Header,
    choice_label,
    correct_letters,
    draw_answer_key,
    draw_instruction,
    draw_numbered_lines,
    draw_text,
    make_room,
    new_pdf,
    start_page,
    wrap,
)
from render.pdf.tiles import draw_tiles_page, tile_solutions

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
# Equations to choose from, in rows below the problem's text
CHOICE_COLUMNS = 2
CHOICE_DROP = 12  # from the representation's top down to the first row's baseline
CHOICE_ROW_HEIGHT = 26  # from one row's baseline to the next
CHOICE_DESCENT = 8  # the squares reach below the baseline, so the last row ends this far below it


def render_word_problems_worksheet(
    questions: Sequence[WordProblemQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    representation: Representation,
    hints: bool,
    slot_of: Sequence[int] | None,
    black_and_white: bool = False,
    work_box: bool = False,
) -> None:
    """
    Render word problems, each drawn with ``representation``, and the answer key if requested, to
    ``path``.

    Each problem's hint is left out when ``hints`` is False, and so is the note beside base-ten
    blocks saying how many to cross out. Base-ten blocks are grey when ``black_and_white`` is
    set. Text-only problems have no box to show the work in when ``work_box`` is False. A problem
    that would run past the bottom margin starts on the next page. A multiple-choice problem has
    its lettered options instead of an answer line. A two-step problem needs ``representation`` to
    be strip diagrams or text only, or raises ``ValueError``. The answer key gives each problem's
    equation and answer (each step's, for a two-step problem), and a multiple-choice problem's
    correct letter.
    ``path`` is a filename or a binary file-like object.

    With ``slot_of``, the sheet is for the self-check tiles case: the problems have no answer
    lines, and the answer bank and pattern follow on a page of their own. ``slot_of[i]`` is the
    slot of question i + 1's answer, as in ``core.self_check_tiles``, so there are at most 12
    questions, and their answers must be distinct. The answer key adds each answer's slot letter.
    """
    two_steps = any(isinstance(question.data, TwoStepQuestionData) for question in questions)
    if two_steps and representation not in TWO_STEP_REPRESENTATIONS:
        raise ValueError("Only strip diagrams and text only show two-step problems.")
    pdf = new_pdf(path, header.title)
    answer_lines = slot_of is None and representation is not Representation.NUMBER_LINE
    colours = GREY_BLOCKS if black_and_white else COLOUR_BLOCKS

    operations = {step.operation for question in questions for step in _steps(question.data)}
    y = draw_instruction(
        pdf, instruction(representation, operations, work_box), start_page(pdf, header)
    )
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
            + _representation_height(question.data, representation, work_box)
            + _response_height(question.response, answer_lines)
        )
        y = make_room(pdf, header, y, height)
        y = _draw_problem(
            pdf,
            number,
            question,
            lines,
            hint_lines,
            representation,
            answer_lines,
            hints,
            colours,
            work_box,
            y,
        )

    if slot_of is None:
        solutions = [_solution(question) for question in questions]
    else:
        tile_questions = [_tile_question(question.data) for question in questions]
        answers = [tile_question.answer for tile_question in tile_questions]
        draw_tiles_page(pdf, header, answers, slot_of)
        solutions = tile_solutions(tile_questions, slot_of)
    if answer_key:
        draw_answer_key(pdf, header, solutions)

    pdf.save()


def _steps(
    data: BasicOperationQuestionData | TwoStepQuestionData,
) -> tuple[BasicOperationQuestionData, ...]:
    """Return the problem's steps: its two for a two-step problem, or else the problem itself."""
    return data.steps if isinstance(data, TwoStepQuestionData) else (data,)


def _tile_question(data: BasicOperationQuestionData | TwoStepQuestionData) -> TileQuestion:
    """Convert the problem to a ``TileQuestion``, as its kind of data is converted."""
    if isinstance(data, TwoStepQuestionData):
        return two_step_tile_question(data)
    return basic_operation_tile_question(data)


def _solution(question: WordProblemQuestion) -> str:
    """
    Return the problem's line in the answer key: each step solved for a two-step problem, or
    else its equation solved, with its correct letter if it has choices.
    """
    if isinstance(question.data, TwoStepQuestionData):
        return solved_steps(question.data)
    if isinstance(question.response, MultipleChoice):
        return f"{solved_equation(question.data)}    ({correct_letters(question.response)})"
    return solved_equation(question.data)


def _response_height(response: FreeResponse | MultipleChoice[str], answer_line: bool) -> float:
    """
    Return the height below the representation of the problem's lettered options, if it has
    them, or else of its answer line, if ``answer_line`` is set.
    """
    if isinstance(response, MultipleChoice):
        rows = -(-len(response.options) // CHOICE_COLUMNS)  # rounded up
        return CHOICE_DROP + (rows - 1) * CHOICE_ROW_HEIGHT + CHOICE_DESCENT
    return ANSWER_DROP if answer_line else 0


def _draw_problem(
    pdf: Canvas,
    number: int,
    question: WordProblemQuestion,
    lines: list[str],
    hint_lines: list[str],
    representation: Representation,
    answer_line: bool,
    hints: bool,
    colours: BlockColours,
    work_box: bool,
    y: float,
) -> float:
    """
    Draw one problem, from its number down to its representation, followed by its lettered
    options if it has them, or else an answer line if ``answer_line`` is set, and return the y
    below it.

    ``hints`` and ``colours`` are for base-ten blocks: whether to write the note saying how many
    to cross out, and the blocks' colours. ``work_box`` is for text only: whether to draw the box
    to show the work in.
    """
    y = draw_numbered_lines(pdf, number, lines, y)
    pdf.setFont(ITALIC_FONT, HINT_SIZE)
    pdf.setFillColor(gray)
    for line in hint_lines:
        pdf.drawString(MARGIN + TEXT_INDENT, y, line)
        y -= HINT_LINE_HEIGHT
    pdf.setFillColor("black")

    top = y + REPRESENTATION_RAISE
    _draw_representation(
        pdf, question.data, representation, MARGIN + TEXT_INDENT, top, hints, colours, work_box
    )

    bottom = top - _representation_height(question.data, representation, work_box)
    if isinstance(question.response, MultipleChoice):
        bottom = _draw_choices(pdf, question.response.options, bottom)
    elif answer_line:
        bottom -= ANSWER_DROP
        pdf.setFont(BOLD_FONT, TEXT_SIZE)
        pdf.drawString(MARGIN + TEXT_INDENT, bottom, ANSWER_LABEL)
        line_x = MARGIN + TEXT_INDENT + stringWidth(ANSWER_LABEL, BOLD_FONT, TEXT_SIZE)
        pdf.line(line_x, bottom, line_x + ANSWER_LINE_LENGTH, bottom)
    return bottom - PROBLEM_GAP


def _representation_height(
    data: BasicOperationQuestionData | TwoStepQuestionData,
    representation: Representation,
    work_box: bool,
) -> float:
    match representation:
        case Representation.STRIP:
            return STRIP_HEIGHT
        case Representation.NONE:
            return WORK_BOX_HEIGHT if work_box else 0
        case Representation.NUMBER_LINE:
            return NUMBER_LINE_HEIGHT
        case Representation.BLOCKS:
            return blocks_height(blocks_diagram(_one_step(data, representation)))
        case Representation.EQUATION_CHOICE:
            return 0  # the equations are the problem's options, below it
        case _:
            assert_never(representation)


def _draw_representation(
    pdf: Canvas,
    data: BasicOperationQuestionData | TwoStepQuestionData,
    representation: Representation,
    x: float,
    top: float,
    hints: bool,
    colours: BlockColours,
    work_box: bool,
) -> None:
    """
    Draw the problem's representation with its top-left corner at (``x``, ``top``): for a
    two-step problem's strip diagram, its one bar. ``hints`` and ``colours`` are for base-ten
    blocks, and ``work_box`` for text only, as in ``_draw_problem``.
    """
    match representation:
        case Representation.STRIP:
            if isinstance(data, TwoStepQuestionData):
                draw_strip_diagram(pdf, x, top, two_step_strip(data))
            else:
                draw_strip_diagram(pdf, x, top, strip_diagram(data))
        case Representation.NONE:
            if work_box:
                _draw_work_box(pdf, x, top)
        case Representation.NUMBER_LINE:
            one_step = _one_step(data, representation)
            draw_number_line(pdf, x, top, one_step.operands[0], number_line_jumps(one_step))
        case Representation.BLOCKS:
            diagram = blocks_diagram(_one_step(data, representation))
            draw_blocks(pdf, x, top, diagram, colours, note=hints)
        case Representation.EQUATION_CHOICE:
            pass  # the equations are the problem's options, drawn by _draw_choices
        case _:
            assert_never(representation)


def _one_step(
    data: BasicOperationQuestionData | TwoStepQuestionData, representation: Representation
) -> BasicOperationQuestionData:
    """
    Return the one-step problem's data, for a representation that shows only one step, or raise
    ``ValueError`` for a two-step problem.
    """
    if isinstance(data, TwoStepQuestionData):
        raise ValueError(f"{REPRESENTATION_NAMES[representation]} show only one-step problems.")
    return data


def _draw_choices(pdf: Canvas, options: Sequence[str], top: float) -> float:
    """
    Draw the options to choose from, ``CHOICE_COLUMNS`` to a row, each after its letter, from
    ``top`` down, and return the bottom of the last row.
    """
    pdf.setFont(FONT, TEXT_SIZE)
    first_baseline = top - CHOICE_DROP
    for index, option in enumerate(options):
        row, column = divmod(index, CHOICE_COLUMNS)
        x = MARGIN + TEXT_INDENT + column * TEXT_WIDTH / CHOICE_COLUMNS
        baseline = first_baseline - row * CHOICE_ROW_HEIGHT
        draw_text(pdf, x, baseline, f"{choice_label(index)} {option}", TEXT_SIZE)
    last_row = (len(options) - 1) // CHOICE_COLUMNS
    return first_baseline - last_row * CHOICE_ROW_HEIGHT - CHOICE_DESCENT


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
