"""
PDF worksheets of word problems, each drawn with the sheet's representation, or on a sheet that
mixes them, its own, with an optional answer key page.

The first page has the instruction under its header, a line for each representation on the sheet and
each way it's answered, and if any problem is drawn with base-ten blocks, a key to the blocks. Each
problem has its number and wording, a hint if the representation has one and hints aren't turned
off, the representation, and an answer line. A text-only problem's representation is a box to show
the work in, unless the boxes are left out, and an equation's is a line to write it on. A number
line's last box is its answer, so it has no answer line. A multiple-choice problem whose
representation is chosen has no hint, and has its lettered equations or number lines instead, in
rows of two. One whose answer is chosen has its representation, but an equation's line, and four
lettered numbers in a row in place of the answer line. A two-step problem is shown only with strip
diagrams, as one bar under its whole, as text only, or with its equation. A sheet for the
self-check tiles case has no answer lines, and ends with a page for the answer bank and pattern.
"""

from collections.abc import Sequence
from typing import BinaryIO, TypeIs, assert_never

from reportlab.lib.colors import HexColor, gray
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.base_ten_blocks import blocks_diagram
from core.basic_operations.data import BasicOperationQuestionData, TwoStepQuestionData
from core.basic_operations.representation import (
    CHOOSE_NUMBER_WHERE_GIVEN,
    REPRESENTATION_NAMES,
    TWO_STEP_REPRESENTATIONS,
    Representation,
    Response,
    TwoJumpLine,
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
from core.question import MultipleChoice
from core.self_check_tiles import TileQuestion
from render.pdf.diagrams import (
    BLOCKS_KEY_HEIGHT,
    COLOUR_BLOCKS,
    GREY_BLOCKS,
    NUMBER_LINE_HEIGHT,
    STRIP_HEIGHT,
    TWO_JUMP_LINE_DROP,
    TWO_JUMP_LINE_HEIGHT,
    BlockColours,
    blocks_height,
    draw_blocks,
    draw_blocks_key,
    draw_number_line,
    draw_strip_diagram,
    draw_two_jump_line,
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
# With nothing drawn, from the representation's top down to the baseline of what follows the text:
# an answer or equation line, the numbers to choose from, or the first row of lettered choices
CHOICE_DROP = 12
# from a drawing's bottom down to the baseline of the answer line or the numbers to choose from
DRAWING_GAP = 22
ANSWER_DROP = 26  # from the equation line down to the answer line, room to write the equation
ANSWER_LABEL = "Answer: "
ANSWER_LINE_LENGTH = 120
PROBLEM_GAP = 22  # from a problem's bottom down to the next problem's baseline
# Text only: the box to show the work in, as wide as the text, with a label in its top-left corner
WORK_BOX_HEIGHT = 60
WORK_BOX_CORNER_RADIUS = 4
WORK_BOX_COLOUR = HexColor("#cbd5e0")  # light grey
WORK_BOX_LABEL = "Show your work"
WORK_BOX_LABEL_SIZE = 9
WORK_BOX_LABEL_COLOUR = HexColor("#a0aec0")  # grey
WORK_BOX_LABEL_INSET = 5  # from the box's left edge to the label
WORK_BOX_LABEL_DROP = 12  # from the box's top down to the label's baseline
# Equations, written: a labelled line, like the answer line
EQUATION_LABEL = "Equation: "
EQUATION_DROP = CHOICE_DROP  # from the representation's top down to the line
EQUATION_LINE_LENGTH = 300
# Equations or number lines to choose from, in rows below the problem's text
CHOICE_COLUMNS = 2
NUMBER_CHOICE_COLUMNS = 4  # a row of the four numbers to choose an answer from
CHOICE_ROW_HEIGHT = 26  # from one row's baseline to the next
# The squares reach below the baseline, so the last row ends this far below it, and so does a
# problem ending with a line or a row of numbers, so problems are evenly spaced
CHOICE_DESCENT = 8
LINE_CHOICE_LETTER_WIDTH = 26  # room for "A)" left of each number line
LINE_CHOICE_GAP = 24  # between a number line and the next choice's letter
# each number line's width
LINE_CHOICE_WIDTH = (TEXT_WIDTH - LINE_CHOICE_GAP) / CHOICE_COLUMNS - LINE_CHOICE_LETTER_WIDTH
LINE_CHOICE_ROW_HEIGHT = TWO_JUMP_LINE_HEIGHT + 9  # from one row's top to the next


def render_word_problems_worksheet(
    questions: Sequence[WordProblemQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    representation: Representation | Sequence[Representation],
    hints: bool,
    slot_of: Sequence[int] | None,
    black_and_white: bool = False,
    work_box: bool = False,
) -> None:
    """
    Render word problems, each drawn with ``representation``, or with the representation at its
    index if a sequence of them is given, and the answer key if requested, to ``path``. The
    instruction has a line for each representation on the sheet and each way it's answered, in
    the order of ``Representation``, written ones first.

    Each problem's hint is left out when ``hints`` is False, and so is the note beside base-ten
    blocks saying how many to cross out. Base-ten blocks are grey when ``black_and_white`` is
    set. Text-only problems have no box to show the work in when ``work_box`` is False. A problem
    that would run past the bottom margin starts on the next page. A multiple-choice problem whose
    representation is chosen has its lettered options instead of its representation and an answer
    line, and no hint; on a sheet of them, the instruction says to choose. One whose answer is
    chosen from numbers has them in a row in place of the answer line, and an equation's has no
    line to write it on. A two-step problem needs its representation to
    be strip diagrams, text only or equations, or raises ``ValueError``. The answer key gives each
    problem's equation and answer (each step's, for a two-step problem), and a multiple-choice
    problem's correct letter.
    ``path`` is a filename or a binary file-like object.

    With ``slot_of``, the sheet is for the self-check tiles case: the problems have no answer
    lines, and the answer bank and pattern follow on a page of their own. ``slot_of[i]`` is the
    slot of question i + 1's answer, as in ``core.self_check_tiles``, so there are at most 12
    questions, and their answers must be distinct. The answer key adds each answer's slot letter.
    """
    representations = (
        [representation] * len(questions)
        if isinstance(representation, Representation)
        else list(representation)
    )
    drawn = list(zip(representations, questions, strict=True))
    if any(
        isinstance(question.data, TwoStepQuestionData) and each not in TWO_STEP_REPRESENTATIONS
        for each, question in drawn
    ):
        raise ValueError("Only strip diagrams, text only and equations show two-step problems.")
    pdf = new_pdf(path, header.title)
    colours = GREY_BLOCKS if black_and_white else COLOUR_BLOCKS

    y = draw_instruction(pdf, _instructions(drawn, work_box), start_page(pdf, header))
    if Representation.BLOCKS in representations:
        top = y + REPRESENTATION_RAISE
        draw_blocks_key(pdf, MARGIN, top, colours)
        y = top - BLOCKS_KEY_HEIGHT - PROBLEM_GAP
    for number, (representation, question) in enumerate(drawn, start=1):
        answer_lines = slot_of is None and representation is not Representation.NUMBER_LINE
        lines = wrap(stem(question.data), TEXT_SIZE, TEXT_WIDTH)
        hint_text = (
            hint(question.data, representation)
            if hints and _response(question) is not Response.MULTIPLE_CHOICE
            else None
        )
        hint_lines = wrap(hint_text, HINT_SIZE, TEXT_WIDTH) if hint_text is not None else []
        height = (
            len(lines) * LINE_HEIGHT
            + len(hint_lines) * HINT_LINE_HEIGHT
            - REPRESENTATION_RAISE
            + _body_height(question, representation, work_box, answer_lines)
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


def _instructions(
    drawn: Sequence[tuple[Representation, WordProblemQuestion]], work_box: bool
) -> str:
    """
    Return the sheet's instruction: a line for each representation in ``drawn`` and each way it's
    answered, in the order of ``Representation``, then of ``Response``, each for the operations of
    its own problems, and whether they have two steps. A representation answered both in writing
    and by choosing from numbers has one line for both, ending with ``CHOOSE_NUMBER_WHERE_GIVEN``,
    but equations, whose written answers have a line for the equation, have two. ``work_box`` is
    as in ``instruction``.
    """
    lines = []
    for representation in Representation:
        answered = {
            response: [
                question
                for each, question in drawn
                if each is representation and _response(question) is response
            ]
            for response in Response
        }
        # one line for both, as the help drawn is the same, but an equation's line
        together = representation is not Representation.EQUATION and all(
            answered[response] for response in (Response.FREE_RESPONSE, Response.NUMBER_CHOICE)
        )
        if together:
            answered[Response.FREE_RESPONSE] += answered.pop(Response.NUMBER_CHOICE)
        for response, questions in answered.items():
            if questions:
                operations = {
                    step.operation for question in questions for step in _steps(question.data)
                }
                two_steps = any(
                    isinstance(question.data, TwoStepQuestionData) for question in questions
                )
                choices = response is Response.MULTIPLE_CHOICE
                numbers = response is Response.NUMBER_CHOICE
                line = instruction(
                    representation, operations, work_box, choices, two_steps, numbers
                )
                if together and response is Response.FREE_RESPONSE:
                    line = f"{line} {CHOOSE_NUMBER_WHERE_GIVEN}"
                lines.append(line)
    return "\n".join(lines)


def _response(question: WordProblemQuestion) -> Response:
    """
    Return how the problem is answered: in writing, by choosing its representation, or by
    choosing its answer from numbers.
    """
    if _chooses_number(question.response):
        return Response.NUMBER_CHOICE
    if isinstance(question.response, MultipleChoice):
        return Response.MULTIPLE_CHOICE
    return Response.FREE_RESPONSE


def _chooses_number(response: object) -> TypeIs[MultipleChoice[int]]:
    """Return whether ``response`` is an answer to choose from numbers."""
    return isinstance(response, MultipleChoice) and isinstance(response.options[0], int)


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
    else its equation solved, followed by its correct letter if it has choices.
    """
    if isinstance(question.data, TwoStepQuestionData):
        solved = solved_steps(question.data)
    else:
        solved = solved_equation(question.data)
    if isinstance(question.response, MultipleChoice):
        return f"{solved}    ({correct_letters(question.response)})"
    return solved


def _body_height(
    question: WordProblemQuestion,
    representation: Representation,
    work_box: bool,
    answer_line: bool,
) -> float:
    """
    Return the height of the problem below its text: its lettered options, if its representation
    is chosen, or else its representation and its answer line, if ``answer_line`` is set, or the
    numbers to choose its answer from in the line's place.
    """
    if _response(question) is Response.NUMBER_CHOICE:
        shown, box = _help(representation, work_box)
        height = _representation_height(question.data, shown, box)
        return height + _line_drop(shown, height) + CHOICE_DESCENT
    if isinstance(question.response, MultipleChoice):
        options = question.response.options
        last_row = (len(options) - 1) // CHOICE_COLUMNS
        if isinstance(options[0], TwoJumpLine):
            return last_row * LINE_CHOICE_ROW_HEIGHT + TWO_JUMP_LINE_HEIGHT
        return CHOICE_DROP + last_row * CHOICE_ROW_HEIGHT + CHOICE_DESCENT
    height = _representation_height(question.data, representation, work_box)
    if answer_line:
        return height + _line_drop(representation, height) + CHOICE_DESCENT
    if representation is Representation.EQUATION:  # its line ends the problem
        return height + CHOICE_DESCENT
    return height


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
    Draw one problem, from its number down to its lettered options if its representation is
    chosen, or else to its representation and an answer line if ``answer_line`` is set, or the
    numbers to choose its answer from in the line's place, and return the y below it.

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
    response = question.response
    numbers = _chooses_number(response)
    if isinstance(response, MultipleChoice) and not _chooses_number(response):
        return _draw_choices(pdf, response.options, top) - PROBLEM_GAP
    if numbers:
        representation, work_box = _help(representation, work_box)
    _draw_representation(
        pdf, question.data, representation, MARGIN + TEXT_INDENT, top, hints, colours, work_box
    )

    height = _representation_height(question.data, representation, work_box)
    bottom = top - height
    if _chooses_number(response):
        bottom -= _line_drop(representation, height)
        _draw_number_choices(pdf, response.options, bottom)
    elif answer_line:
        bottom -= _line_drop(representation, height)
        _draw_labelled_line(pdf, MARGIN + TEXT_INDENT, bottom, ANSWER_LABEL, ANSWER_LINE_LENGTH)
    if numbers or answer_line or representation is Representation.EQUATION:
        bottom -= CHOICE_DESCENT  # as below lettered equations
    return bottom - PROBLEM_GAP


def _help(representation: Representation, work_box: bool) -> tuple[Representation, bool]:
    """
    Return what's drawn to help solve a problem whose answer is chosen from numbers, and whether
    it has a box to show the work in: its representation, but text only without a box for an
    equation, which has no line to write it on.
    """
    if representation is Representation.EQUATION:
        return Representation.NONE, False
    return representation, work_box


def _line_drop(representation: Representation, height: float) -> float:
    """
    Return how far below the bottom of ``representation``, drawn ``height`` high, the answer line
    or the numbers to choose an answer from have their baseline: ``CHOICE_DROP`` with nothing
    drawn, as lettered choices; ``ANSWER_DROP`` below an equation's line, room to write the
    equation; or else ``DRAWING_GAP``.
    """
    if height == 0:
        return CHOICE_DROP
    if representation is Representation.EQUATION:
        return ANSWER_DROP
    return DRAWING_GAP


def _draw_number_choices(pdf: Canvas, options: Sequence[int], baseline: float) -> None:
    """Draw the numbers to choose an answer from in a row on ``baseline``, each after its letter."""
    pdf.setFont(FONT, TEXT_SIZE)
    for index, option in enumerate(options):
        x = MARGIN + TEXT_INDENT + index * TEXT_WIDTH / NUMBER_CHOICE_COLUMNS
        draw_text(pdf, x, baseline, f"{choice_label(index)} {option:,}", TEXT_SIZE)


def _draw_labelled_line(pdf: Canvas, x: float, baseline: float, label: str, length: float) -> None:
    """Draw ``label`` in bold from ``x``, followed on its baseline by a line ``length`` long."""
    pdf.setFont(BOLD_FONT, TEXT_SIZE)
    pdf.drawString(x, baseline, label)
    line_x = x + stringWidth(label, BOLD_FONT, TEXT_SIZE)
    pdf.line(line_x, baseline, line_x + length, baseline)


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
        case Representation.EQUATION:
            return EQUATION_DROP
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
        case Representation.EQUATION:
            _draw_labelled_line(pdf, x, top - EQUATION_DROP, EQUATION_LABEL, EQUATION_LINE_LENGTH)
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


def _draw_choices(pdf: Canvas, options: Sequence[str | TwoJumpLine], top: float) -> float:
    """
    Draw the options to choose from, equations or number lines, ``CHOICE_COLUMNS`` to a row, each
    after its letter, from ``top`` down, and return the bottom of the last row.
    """
    lines = [option for option in options if isinstance(option, TwoJumpLine)]
    if lines:  # a problem's options are all of one kind
        return _draw_line_choices(pdf, lines, top)
    pdf.setFont(FONT, TEXT_SIZE)
    first_baseline = top - CHOICE_DROP
    for index, option in enumerate(options):
        row, column = divmod(index, CHOICE_COLUMNS)
        x = MARGIN + TEXT_INDENT + column * TEXT_WIDTH / CHOICE_COLUMNS
        baseline = first_baseline - row * CHOICE_ROW_HEIGHT
        draw_text(pdf, x, baseline, f"{choice_label(index)} {option}", TEXT_SIZE)
    last_row = (len(options) - 1) // CHOICE_COLUMNS
    return first_baseline - last_row * CHOICE_ROW_HEIGHT - CHOICE_DESCENT


def _draw_line_choices(pdf: Canvas, lines: Sequence[TwoJumpLine], top: float) -> float:
    """
    Draw the number lines to choose from, ``CHOICE_COLUMNS`` to a row, each with its letter level
    with its line, from ``top`` down, and return the bottom of the last row.
    """
    for index, line in enumerate(lines):
        row, column = divmod(index, CHOICE_COLUMNS)
        x = (
            MARGIN
            + TEXT_INDENT
            + column * (LINE_CHOICE_LETTER_WIDTH + LINE_CHOICE_WIDTH + LINE_CHOICE_GAP)
        )
        row_top = top - row * LINE_CHOICE_ROW_HEIGHT
        pdf.setFont(BOLD_FONT, TEXT_SIZE)
        pdf.drawString(x, row_top - TWO_JUMP_LINE_DROP - 5, choice_label(index))
        draw_two_jump_line(pdf, x + LINE_CHOICE_LETTER_WIDTH, row_top, line, LINE_CHOICE_WIDTH)
    last_row = (len(lines) - 1) // CHOICE_COLUMNS
    return top - last_row * LINE_CHOICE_ROW_HEIGHT - TWO_JUMP_LINE_HEIGHT


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
