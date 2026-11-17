"""
PDF worksheets of input-output tables, with an optional answer key page.

A sheet of tables to complete has the sheet's instruction under its header, then its problems
two to a row, each its number and rule above its titled table, which has empty cells for the
numbers left out. A sheet for the self-check tiles case leaves one number out of each table, and
ends with a page for the answer bank and pattern.

A multiple-choice sheet has its problems one under another, each saying what to do:
- choose the table that matches a rule: the rule and question, then the lettered tables in rows
  of two;
- complete a sentence about a table: the instruction, the table, the sentence with a blank,
  then the lettered choices for the blank in a row;
- choose the true statement about a table: the question, the table, then the lettered
  statements.

Tables in two columns and tables in two rows take turns, by row of problems or by problem, so a
sheet has both.
"""

from collections.abc import Collection, Sequence
from typing import BinaryIO, TypeIs

from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen.canvas import Canvas

from core.input_output_tables.data import (
    InputOutputQuestion,
    InputOutputQuestionData,
    InputOutputRuleQuestionData,
    InputOutputTableQuestion,
    InputOutputTableQuestionData,
    NumberPairs,
    Rule,
    RuleForm,
)
from core.input_output_tables.representation import (
    INSTRUCTION,
    STATEMENT_QUESTION,
    TILES_INSTRUCTION,
    completed_sentence,
    headings,
    input_output_tile_question,
    rule,
    rule_equation,
    sentence_choice,
    sentence_instruction,
    sentence_with_blank,
    solution,
    statement,
    table_question,
    table_title,
)
from core.question import FreeResponse, MultipleChoice
from render.pdf.page import (
    BOLD_FONT,
    CONTENT_WIDTH,
    FONT,
    MARGIN,
    Header,
    choice_label,
    correct_letters,
    draw_answer_key,
    draw_instruction,
    fit_font,
    make_room,
    new_pdf,
    start_page,
    wrap,
)
from render.pdf.tables import CELL_PADDING, LINE_GAP, draw_table
from render.pdf.tiles import draw_tiles_page, tile_solutions

RULE_SIZE = 12  # every problem's text: its rule, question, sentence or statements
RULE_LINE_HEIGHT = 15
NUMBER_WIDTH = 24  # from a problem's number to its text
RULE_GAP = 10  # from the last line above a table down to the top of its title
PROBLEM_GAP = 28  # from the bottom of a problem down to the next problem's baseline

COLUMN_GAP = 24  # between the two problems in a row of tables to complete
PROBLEM_WIDTH = (CONTENT_WIDTH - COLUMN_GAP) / 2  # each problem's, its number included
RULE_WIDTH = PROBLEM_WIDTH - NUMBER_WIDTH  # a table is centred across its rule's width

TEXT_WIDTH = CONTENT_WIDTH - NUMBER_WIDTH  # a multiple-choice problem's, beside its number
CHOICE_GAP = 24  # between two lettered tables in a row
CHOICE_WIDTH = (TEXT_WIDTH - CHOICE_GAP) / 2  # each lettered table's, its letter included
LETTER_WIDTH = 26  # room for "A)" left of each table or statement
CHOICE_ROW_GAP = 16  # between the rows of lettered tables
ANSWER_GAP = 26  # from the bottom of a table down to the first line of the sentence or statements
STATEMENT_GAP = 6  # between two lettered statements
SENTENCE_CHOICES_GAP = 6  # between a sentence to complete and its row of lettered choices

TITLE_SIZE = 10
TITLE_DROP = 10  # from the top of a table's title down to its baseline
TITLE_HEIGHT = 16  # from the top of a table's title down to the table
HEADING_SIZE = 10
BODY_SIZE = 11
HEADING_PADDING = 4  # above and below a heading's lines
ROW_HEIGHT = 20  # each pair's row in a table of two columns; at least, a row of a table of two rows
VALUE_COLUMN_WIDTH = 88  # each column of a table of two columns: 176 in all
HEADING_COLUMN_WIDTH = 92  # the headings' column of a table of two rows
VALUE_CELL_WIDTH = 26  # each number's cell in a table of two rows: 196 in all, with 4 pairs

# A table's column widths, row heights and cells, as draw_table takes them
type Layout = tuple[Sequence[float], Sequence[float], Sequence[Sequence[str | None]]]


def render_input_output_tables_worksheet(
    questions: Sequence[InputOutputQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    slot_of: Sequence[int] | None,
) -> None:
    """
    Render input-output table problems, and the answer key if requested, to ``path``.

    The questions are all tables to complete, or all multiple choice: tables to choose, and
    sentences and statements of a table's rule. A row of problems, or a multiple-choice problem,
    that would run past the bottom margin starts on the next page. The answer key gives each
    table's rule as an equation, and for a table to complete, the numbers left out under each
    heading; for a sentence, the completed sentence; for a lettered choice, the correct letter and
    the rule. ``path`` is a filename or a binary file-like object.

    With ``slot_of``, the sheet is for the self-check tiles case: the answer bank and pattern
    follow on a page of their own. Each table must leave out one number, and the numbers must be
    distinct. ``slot_of[i]`` is the slot of question i + 1's answer, as in
    ``core.self_check_tiles``, so there are at most 12 questions. The answer key adds each
    answer's slot letter.

    Raises ``ValueError`` if tables to complete and multiple-choice questions are mixed.
    """
    pdf = new_pdf(path, header.title)
    tables = [question for question in questions if _completes_table(question)]
    if len(tables) == len(questions):
        instruction = INSTRUCTION if slot_of is None else TILES_INSTRUCTION
        y = draw_instruction(pdf, instruction, start_page(pdf, header))
        for row, first in enumerate(range(0, len(tables), 2)):
            y = _draw_row(pdf, header, first + 1, tables[first : first + 2], row % 2 == 1, y)
    elif tables:
        raise ValueError("Tables to complete can't share a sheet with multiple-choice questions.")
    else:
        y = start_page(pdf, header)
        for index, question in enumerate(questions):
            y = _draw_choice_problem(pdf, header, index + 1, question, index % 2 == 1, y)

    if slot_of is None:
        solutions = [_solution(question) for question in questions]
    else:
        tile_questions = [input_output_tile_question(question.data) for question in tables]
        answers = [tile_question.answer for tile_question in tile_questions]
        draw_tiles_page(pdf, header, answers, slot_of)
        solutions = tile_solutions(tile_questions, slot_of)
    if answer_key:
        draw_answer_key(pdf, header, solutions)

    pdf.save()


def _asks_for_table(question: InputOutputQuestion) -> TypeIs[InputOutputTableQuestion]:
    """Return whether the question asks for a table, given its rule, rather than for a rule."""
    return isinstance(question.data, InputOutputTableQuestionData)


def _completes_table(question: InputOutputQuestion) -> TypeIs[InputOutputTableQuestion]:
    """Return whether the question is a table to complete."""
    return _asks_for_table(question) and isinstance(question.response, FreeResponse)


def _solution(question: InputOutputQuestion) -> str:
    """
    Return the answer key's entry, after the correct letter for a lettered choice: a sentence's
    is the sentence completed, a statement's the rule as an equation.
    """
    if _asks_for_table(question):
        table_response = question.response
        if isinstance(table_response, MultipleChoice):
            return f"{correct_letters(table_response)}) {solution(question.data)}"
        return solution(question.data)
    letters = correct_letters(question.response)
    if question.data.form is RuleForm.SENTENCE:
        return f"{letters}) {completed_sentence(question.data)}"
    return f"{letters}) {rule_equation(question.data)}"


def _draw_row(
    pdf: Canvas,
    header: Header,
    first_number: int,
    questions: Sequence[InputOutputTableQuestion],
    horizontal: bool,
    y: float,
) -> float:
    """
    Draw a row of up to two tables to complete, in two rows with ``horizontal``, else in two
    columns, each under its number and rule from baseline ``y``. Returns the next row's baseline.
    """
    rules = [wrap(rule(question.data), RULE_SIZE, RULE_WIDTH) for question in questions]
    layouts = [
        _layout(
            question.data,
            question.data.answer,
            horizontal,
            question.data.blank_inputs,
            question.data.blank_outputs,
        )
        for question in questions
    ]
    drops = [
        (len(lines) - 1) * RULE_LINE_HEIGHT + RULE_GAP + _table_height(layout)
        for lines, layout in zip(rules, layouts, strict=True)
    ]
    y = make_room(pdf, header, y, max(drops))
    for column, (question, lines, layout) in enumerate(zip(questions, rules, layouts, strict=True)):
        x = MARGIN + column * (PROBLEM_WIDTH + COLUMN_GAP)
        _draw_lines(pdf, first_number + column, x, lines, y)
        top = y - (len(lines) - 1) * RULE_LINE_HEIGHT - RULE_GAP
        centre = x + NUMBER_WIDTH + RULE_WIDTH / 2
        _draw_table(pdf, centre, top, question.data, layout, horizontal)
    return y - max(drops) - PROBLEM_GAP


def _draw_choice_problem(
    pdf: Canvas,
    header: Header,
    number: int,
    question: InputOutputQuestion,
    horizontal: bool,
    y: float,
) -> float:
    """
    Draw a multiple-choice problem from baseline ``y``, as its kind is drawn, with its tables in
    two rows each with ``horizontal``, else in two columns. Returns the next problem's baseline.
    """
    if _asks_for_table(question):
        table_response = question.response
        if not isinstance(table_response, MultipleChoice):
            raise ValueError("A table to choose must be multiple choice.")
        data = question.data
        return _draw_table_choice(pdf, header, number, data, table_response.options, horizontal, y)
    options = question.response.options
    if question.data.form is RuleForm.SENTENCE:
        return _draw_sentence(pdf, header, number, question.data, options, horizontal, y)
    return _draw_statements(pdf, header, number, question.data, options, horizontal, y)


def _draw_table_choice(
    pdf: Canvas,
    header: Header,
    number: int,
    data: InputOutputTableQuestionData,
    options: Sequence[NumberPairs],
    horizontal: bool,
    y: float,
) -> float:
    """
    Draw a table to choose: its number, rule and question, then its lettered ``options`` in rows
    of two. Returns the next problem's baseline.
    """
    lines = wrap(table_question(data), RULE_SIZE, TEXT_WIDTH)
    layouts = [_layout(data, option, horizontal) for option in options]
    row_heights = [
        max(_table_height(layout) for layout in layouts[first : first + 2])
        for first in range(0, len(layouts), 2)
    ]
    drop = (
        (len(lines) - 1) * RULE_LINE_HEIGHT
        + RULE_GAP
        + sum(row_heights)
        + (len(row_heights) - 1) * CHOICE_ROW_GAP
    )
    y = make_room(pdf, header, y, drop)
    _draw_lines(pdf, number, MARGIN, lines, y)
    top = y - (len(lines) - 1) * RULE_LINE_HEIGHT - RULE_GAP
    for index, layout in enumerate(layouts):
        row, column = divmod(index, 2)
        x = MARGIN + NUMBER_WIDTH + column * (CHOICE_WIDTH + CHOICE_GAP)
        row_top = top - sum(row_heights[:row]) - row * CHOICE_ROW_GAP
        # the letter level with the table's title
        pdf.setFont(BOLD_FONT, RULE_SIZE)
        pdf.drawString(x, row_top - TITLE_DROP, choice_label(index))
        centre = x + LETTER_WIDTH + (CHOICE_WIDTH - LETTER_WIDTH) / 2
        _draw_table(pdf, centre, row_top, data, layout, horizontal)
    return y - drop - PROBLEM_GAP


def _draw_statements(
    pdf: Canvas,
    header: Header,
    number: int,
    data: InputOutputRuleQuestionData,
    options: Sequence[Rule],
    horizontal: bool,
    y: float,
) -> float:
    """
    Draw a statement to choose: its number and question, the table, then the lettered statement
    of each rule in ``options``. Returns the next problem's baseline.
    """
    lines = wrap(STATEMENT_QUESTION, RULE_SIZE, TEXT_WIDTH)
    layout = _layout(data, data.pairs, horizontal)
    statements = [
        wrap(statement(data, option), RULE_SIZE, TEXT_WIDTH - LETTER_WIDTH) for option in options
    ]
    answer_drop = (sum(len(each) for each in statements) - 1) * RULE_LINE_HEIGHT + (
        len(statements) - 1
    ) * STATEMENT_GAP
    baseline = _draw_question_and_table(
        pdf, header, number, lines, data, layout, horizontal, answer_drop, y
    )
    x = MARGIN + NUMBER_WIDTH
    for index, statement_lines in enumerate(statements):
        pdf.setFont(BOLD_FONT, RULE_SIZE)
        pdf.drawString(x, baseline, choice_label(index))
        pdf.setFont(FONT, RULE_SIZE)
        for line in statement_lines:
            pdf.drawString(x + LETTER_WIDTH, baseline, line)
            baseline -= RULE_LINE_HEIGHT
        baseline -= STATEMENT_GAP
    return baseline + RULE_LINE_HEIGHT + STATEMENT_GAP - PROBLEM_GAP


def _draw_sentence(
    pdf: Canvas,
    header: Header,
    number: int,
    data: InputOutputRuleQuestionData,
    options: Sequence[Rule],
    horizontal: bool,
    y: float,
) -> float:
    """
    Draw a sentence to complete: its number and instruction, the table, the sentence with a
    blank, then a lettered choice for each rule in ``options``, in a row, each in an equal share
    of the width. Returns the next problem's baseline.
    """
    lines = wrap(sentence_instruction(options), RULE_SIZE, TEXT_WIDTH)
    layout = _layout(data, data.pairs, horizontal)
    sentence_lines = wrap(sentence_with_blank(data, options), RULE_SIZE, TEXT_WIDTH)
    answer_drop = len(sentence_lines) * RULE_LINE_HEIGHT + SENTENCE_CHOICES_GAP
    baseline = _draw_question_and_table(
        pdf, header, number, lines, data, layout, horizontal, answer_drop, y
    )
    x = MARGIN + NUMBER_WIDTH
    pdf.setFont(FONT, RULE_SIZE)
    for line in sentence_lines:
        pdf.drawString(x, baseline, line)
        baseline -= RULE_LINE_HEIGHT
    baseline -= SENTENCE_CHOICES_GAP
    share = TEXT_WIDTH / len(options)
    for index, option in enumerate(options):
        choice_x = x + index * share
        pdf.setFont(BOLD_FONT, RULE_SIZE)
        pdf.drawString(choice_x, baseline, choice_label(index))
        pdf.setFont(FONT, RULE_SIZE)
        pdf.drawString(choice_x + LETTER_WIDTH, baseline, sentence_choice(option, options))
    return baseline - PROBLEM_GAP


def _draw_question_and_table(
    pdf: Canvas,
    header: Header,
    number: int,
    lines: Sequence[str],
    data: InputOutputRuleQuestionData,
    layout: Layout,
    horizontal: bool,
    answer_drop: float,
    y: float,
) -> float:
    """
    Draw a problem's number and ``lines`` from baseline ``y``, and its table centred below them,
    first moving to a new page if the problem, ending ``answer_drop`` below the first line of
    its answer, won't fit. Returns the baseline of that first line.
    """
    above_answer = (len(lines) - 1) * RULE_LINE_HEIGHT + RULE_GAP + _table_height(layout)
    y = make_room(pdf, header, y, above_answer + ANSWER_GAP + answer_drop)
    _draw_lines(pdf, number, MARGIN, lines, y)
    top = y - (len(lines) - 1) * RULE_LINE_HEIGHT - RULE_GAP
    _draw_table(pdf, MARGIN + NUMBER_WIDTH + TEXT_WIDTH / 2, top, data, layout, horizontal)
    return y - above_answer - ANSWER_GAP


def _draw_lines(pdf: Canvas, number: int, x: float, lines: Sequence[str], y: float) -> None:
    """Draw a problem's number at ``x`` and its lines beside it, from baseline ``y``."""
    pdf.setFillColor("black")
    pdf.setFont(FONT, RULE_SIZE)
    pdf.drawString(x, y, f"{number}.")
    for line in lines:
        pdf.drawString(x + NUMBER_WIDTH, y, line)
        y -= RULE_LINE_HEIGHT


def _layout(
    data: InputOutputQuestionData,
    pairs: NumberPairs,
    horizontal: bool,
    blank_inputs: Collection[int] = (),
    blank_outputs: Collection[int] = (),
) -> Layout:
    """
    Return the column widths, row heights and cells of a table of ``pairs`` under ``data``'s
    headings: in two rows with ``horizontal``, the headings in the first column, else in two
    columns, the headings in the first row. The numbers at ``blank_inputs`` and
    ``blank_outputs`` are empty cells. A heading too long for one line takes more, and its row
    grows to fit.
    """
    inputs = [
        None if index in blank_inputs else str(input_) for index, (input_, _) in enumerate(pairs)
    ]
    outputs = [
        None if index in blank_outputs else str(output) for index, (_, output) in enumerate(pairs)
    ]
    heading_width = HEADING_COLUMN_WIDTH if horizontal else VALUE_COLUMN_WIDTH
    lines = [_heading_lines(heading, heading_width) for heading in headings(data)]
    heading_height = max(
        ROW_HEIGHT, max(map(len, lines)) * (HEADING_SIZE + LINE_GAP) + 2 * HEADING_PADDING
    )
    input_heading, output_heading = ("\n".join(each) for each in lines)
    if horizontal:
        widths = [HEADING_COLUMN_WIDTH] + [VALUE_CELL_WIDTH] * len(pairs)
        return widths, [heading_height] * 2, [[input_heading, *inputs], [output_heading, *outputs]]
    cells: list[list[str | None]] = [[input_heading, output_heading]]
    cells += [[input_, output] for input_, output in zip(inputs, outputs, strict=True)]
    return [VALUE_COLUMN_WIDTH] * 2, [heading_height] + [ROW_HEIGHT] * len(pairs), cells


def _heading_lines(heading: str, width: float) -> list[str]:
    """Split a heading into the lines that fit a cell ``width`` wide, inside its padding."""
    lines: list[str] = simpleSplit(heading, BOLD_FONT, HEADING_SIZE, width - 2 * CELL_PADDING)
    return lines


def _table_height(layout: Layout) -> float:
    """Return the height of a table with its title."""
    _, heights, _ = layout
    return TITLE_HEIGHT + sum(heights)


def _draw_table(
    pdf: Canvas,
    centre: float,
    top: float,
    data: InputOutputQuestionData,
    layout: Layout,
    horizontal: bool,
) -> None:
    """
    Draw ``data``'s table title, and below it the table laid out in ``layout``, centred on
    ``centre`` from ``top`` down. ``horizontal`` is as ``_layout`` was given it.
    """
    widths, heights, cells = layout
    pdf.saveState()
    pdf.setFillColor("black")
    title = table_title(data)
    fit_font(pdf, title, BOLD_FONT, TITLE_SIZE, sum(widths))
    pdf.drawCentredString(centre, top - TITLE_DROP, title)
    draw_table(
        pdf,
        centre - sum(widths) / 2,
        top - TITLE_HEIGHT,
        widths,
        heights,
        cells,
        heading_row=not horizontal,
        heading_column=horizontal,
        heading_size=HEADING_SIZE,
        body_size=BODY_SIZE,
    )
    pdf.restoreState()
