"""
PDF worksheets of multiplication word problems, each with six lettered models to choose its own
three from, with an optional answer key page.

The first page has the sheet's instruction under its header. Each problem has its number, its
wording, and its models in rows of two, each with its letter: arrays, number lines of equal
jumps, strip diagrams and repeated additions.
"""

from collections.abc import Sequence
from string import ascii_uppercase
from typing import BinaryIO, assert_never

from reportlab.pdfgen.canvas import Canvas

from core.basic_operations.multiplication_models import (
    MULTIPLICATION_MODELS_INSTRUCTION,
    Array,
    EqualJumpLine,
    MultiplicationModel,
    MultiplicationModelsQuestion,
    RepeatedAddition,
    model_description,
)
from core.basic_operations.representation import EqualStripDiagram, StripDiagram, solved_equation
from render.pdf.diagrams import (
    EQUAL_JUMP_LINE_HEIGHT,
    STRIP_HEIGHT,
    UNKNOWN_LABEL,
    draw_array,
    draw_equal_jump_line,
    draw_strip_diagram,
)
from render.pdf.page import (
    BOLD_FONT,
    FONT,
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
    make_room,
    new_pdf,
    start_page,
    wrap,
)

CHOICE_COLUMNS = 2
CHOICE_LETTER_WIDTH = 26  # room for "A)" left of each model
CHOICE_GAP = 24  # between a model and the next choice's letter
MODEL_WIDTH = (TEXT_WIDTH - CHOICE_GAP) / CHOICE_COLUMNS - CHOICE_LETTER_WIDTH
MODEL_HEIGHT = 60  # the box each model is centred in
CHOICE_ROW_HEIGHT = MODEL_HEIGHT + 14  # from the top of one row of models to the top of the next
CHOICES_RAISE = 6  # the models' top is this far above the next text baseline
PROBLEM_GAP = 22  # from the last row of models down to the next problem's baseline
REPEATED_ADDITION_LINE_HEIGHT = 18  # between a repeated addition's lines, when it wraps


def render_multiplication_models_worksheet(
    questions: Sequence[MultiplicationModelsQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    jump_labels: bool,
) -> None:
    """
    Render word problems, each with its models to choose from, and the answer key if requested,
    to ``path``. With ``jump_labels``, each number line's jumps are numbered.

    A problem that would run past the bottom margin starts on the next page. The answer key gives
    each problem's equation and answer and its correct letters, then on a line of its own what
    each wrong model shows. ``path`` is a filename or a binary file-like object.
    """
    pdf = new_pdf(path, header.title)
    y = draw_instruction(pdf, MULTIPLICATION_MODELS_INSTRUCTION, start_page(pdf, header))
    for number, question in enumerate(questions, start=1):
        lines = wrap(question.data.question_text or "", TEXT_SIZE, TEXT_WIDTH)
        options = question.response.options
        rows = -(-len(options) // CHOICE_COLUMNS)  # rounded up
        height = len(lines) * LINE_HEIGHT - CHOICES_RAISE + rows * CHOICE_ROW_HEIGHT
        y = make_room(pdf, header, y, height)
        y = draw_numbered_lines(pdf, number, lines, y)
        y = _draw_choices(pdf, options, y + CHOICES_RAISE, jump_labels)

    if answer_key:
        solutions = [_solution(question) for question in questions]
        draw_answer_key(pdf, header, solutions)
    pdf.save()


def _solution(question: MultiplicationModelsQuestion) -> str:
    """
    Return the problem's answer key entry: its equation solved and its correct letters, then a
    line for each wrong model, "Not B: array has 5 rows of 6".
    """
    response = question.response
    wrong = [
        f"Not {ascii_uppercase[index]}: {model_description(model)}"
        for index, model in enumerate(response.options)
        if index not in response.correct_indexes
    ]
    return "\n".join([f"{solved_equation(question.data)}    ({correct_letters(response)})", *wrong])


def _draw_choices(
    pdf: Canvas, options: Sequence[MultiplicationModel], top: float, jump_labels: bool
) -> float:
    """
    Draw the models to choose from, ``CHOICE_COLUMNS`` to a row, each with its letter, from
    ``top`` down, and return the next problem's baseline.
    """
    for index, model in enumerate(options):
        row, column = divmod(index, CHOICE_COLUMNS)
        x = MARGIN + TEXT_INDENT + column * (CHOICE_LETTER_WIDTH + MODEL_WIDTH + CHOICE_GAP)
        row_top = top - row * CHOICE_ROW_HEIGHT
        pdf.setFillColor("black")
        pdf.setFont(BOLD_FONT, TEXT_SIZE)
        pdf.drawString(x, row_top - MODEL_HEIGHT / 2 - TEXT_SIZE / 3, choice_label(index))
        _draw_model(pdf, x + CHOICE_LETTER_WIDTH, row_top, model, jump_labels)
    last_row = (len(options) - 1) // CHOICE_COLUMNS
    return top - last_row * CHOICE_ROW_HEIGHT - MODEL_HEIGHT - PROBLEM_GAP


def _draw_model(
    pdf: Canvas, x: float, top: float, model: MultiplicationModel, jump_labels: bool
) -> None:
    """
    Draw ``model`` centred from top to bottom in a box ``MODEL_WIDTH`` wide and ``MODEL_HEIGHT``
    high with its top-left corner at (``x``, ``top``). An array is centred across it too, and the
    others fill its width, or start at its left.
    """
    match model:
        case Array():
            draw_array(pdf, x, top, model, MODEL_WIDTH, MODEL_HEIGHT)
        case EqualJumpLine():
            line_top = top - (MODEL_HEIGHT - EQUAL_JUMP_LINE_HEIGHT) / 2
            draw_equal_jump_line(pdf, x, line_top, model, MODEL_WIDTH, jump_labels)
        case EqualStripDiagram() | StripDiagram():
            strip_top = top - (MODEL_HEIGHT - STRIP_HEIGHT) / 2
            draw_strip_diagram(pdf, x, strip_top, model, MODEL_WIDTH)
        case RepeatedAddition():
            _draw_repeated_addition(pdf, x, top - MODEL_HEIGHT / 2, model)
        case _:
            assert_never(model)


def _draw_repeated_addition(
    pdf: Canvas, x: float, middle: float, addition: RepeatedAddition
) -> None:
    """
    Draw ``addition`` with its total as "?", from ``x``, centred from top to bottom on
    ``middle``, in the text's size, wrapped after a "+" to fit ``MODEL_WIDTH``.
    """
    text = " + ".join(str(addend) for addend in addition.addends) + f" = {UNKNOWN_LABEL}"
    lines = wrap(text, TEXT_SIZE, MODEL_WIDTH)
    pdf.setFillColor("black")
    pdf.setFont(FONT, TEXT_SIZE)
    y = middle + (len(lines) - 1) * REPEATED_ADDITION_LINE_HEIGHT / 2 - TEXT_SIZE / 3
    for line in lines:
        pdf.drawString(x, y, line)
        y -= REPEATED_ADDITION_LINE_HEIGHT
