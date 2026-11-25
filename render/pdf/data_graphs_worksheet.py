"""
PDF worksheets of data sets, each with questions about it, with an optional answer key page,
and for the self-check tiles case, an answer bank page.

The first page has the sheet's instruction under its header, and on a tiles sheet whose problems
have a first part, a line saying which parts go on the tiles. Each problem has its number and
introduction, then its parts, lettered when there are two or more. Its first part is one of:
- completing a display, with the given display beside the display to complete, or choosing it,
  with the given display above the four choices, two to a row;
- reading the counts from the given display, into boxes, or choosing the list of them;
- finding the error in a display, beside the data's table or list if it has one, by completing
  a sentence or choosing one;
- choosing which of four displays doesn't show the data, under its table if it has one.
Without a first part, the given display is shown alone. The one-step and two-step problems each
have an answer box on the right, or their choices beneath, or for the tiles case, their tile's
number.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from itertools import repeat
from string import ascii_uppercase
from typing import BinaryIO, assert_never

from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.discrete_data.data import (
    CategoricalData,
    DataDisplay,
    DiscreteDataProblem,
    DisplayChoice,
    DoesntMatchQuestionData,
    ErrorChoice,
    FindErrorQuestionData,
    NumericalData,
    ReadCountsQuestionData,
    ShownDisplay,
    SummarizeDataQuestionData,
    chosen_data,
)
from core.discrete_data.representation import (
    DISPLAY_NAMES,
    blank_counts,
    counts_text,
    error_displays,
    error_fix,
    error_sentence,
    instruction,
    intro,
    labels,
    mistake,
    stem,
    summarize_stem,
    tiles_note,
    work,
)
from core.question import MultipleChoice
from render.pdf.graphics.data_displays import NumberListStyle, draw_display
from render.pdf.page import (
    BOLD_FONT,
    FONT,
    MARGIN,
    PAGE_WIDTH,
    TEXT_INDENT,
    TEXT_SIZE,
    TEXT_WIDTH,
    Header,
    choice_label,
    correct_letters,
    draw_answer_key,
    draw_instruction,
    make_room,
    new_pdf,
    start_page,
    wrap,
)
from render.pdf.tiles import draw_tiles_page

INTRO_SIZE = 12
INTRO_LINE_HEIGHT = 15
PART_SIZE = 11
PART_LINE_HEIGHT = 14
PART_INDENT = 18  # from a part's letter to its text
PART_GAP = 8  # below a part's lines, which take at least two lines' room, for its answer box
PANEL_HEIGHT = 150
PANEL_GAP = 16  # between two displays side by side
PANEL_RAISE = 6  # the panels' top is this far above the next text baseline
PANEL_DROP = 22  # from the bottom of the panels down to the next part's baseline
ROW_GAP = 12  # between two rows of displays
LIST_PANEL_WIDTH = 180  # a list is narrow, leaving its number line room for the Xs
GIVEN_WIDTH = 260  # a display shown on its own, centred
CHOICE_COLUMNS = 2
CHOICE_GAP = 12  # between two choices in a row
CHOICE_LETTER_WIDTH = 22  # from a choice's letter to its display
CHOICE_HEIGHT = 136  # a choice's display
CHOICE_ROW_HEIGHT = 146  # from one row of choices' top to the next
CHOICES_DROP = 14  # from the display above down to the choices' top
CHOICE_LETTER_DROP = 14  # from a choice's top down to its letter's baseline
TEXT_CHOICE_GAP = 4  # below each written choice's lines
NUMBER_CHOICE_WIDTH = 90  # for each of a problem's number choices, across
NUMBER_CHOICE_DROP = 4  # extra, from a problem's last line down to its choices
COUNT_COLUMNS = 3  # boxes for counts, to a row
COUNT_ROW_HEIGHT = 26  # from one row of count boxes to the next
COUNT_BOX_WIDTH = 50
NUMBER_CELL_WIDTH = 26  # a box for one number of a list
NUMBER_CELL_HEIGHT = 20
BOX_WIDTH = 74
BOX_HEIGHT = 22
BOX_CORNER_RADIUS = 4
BOX_COLOUR = HexColor("#4a5568")  # dark grey
BOX_DROP = 7  # from a part's first baseline down to the bottom of its box
ANSWER_LABEL = "Answer:"
ANSWER_LABEL_GAP = 6  # from the label to the box
QUESTION_GAP = 12  # at least, from a part's text to its "Answer:" label
ANSWER_WIDTH = (
    QUESTION_GAP + stringWidth(ANSWER_LABEL, BOLD_FONT, PART_SIZE) + ANSWER_LABEL_GAP + BOX_WIDTH
)  # the room a part's text leaves for its answer box
PROBLEM_GAP = 22  # from the end of a problem down to the next problem's baseline


@dataclass(frozen=True)
class _Text:
    """
    A problem's wrapped text: its introduction, its first part's question, a sentence to
    complete or each written choice for it, and each word problem's question.
    """

    intro: list[str]
    task: list[str] | None
    task_choices: list[list[str]]
    sentence: str | None
    word_problems: list[list[str]]
    lettered: bool  # whether its parts are lettered, as they are when there are two or more


def render_data_graphs_worksheet(
    problems: Sequence[DiscreteDataProblem],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    list_styles: Sequence[NumberListStyle],
    slot_of: Sequence[int] | None = None,
) -> None:
    """
    Render data-set problems, and the answer key if requested, to ``path``.

    Problem i's list of numbers, if it has one, is shown in ``list_styles[i]``. A problem that
    would run past the bottom margin starts on the next page. The answer key gives each problem's
    blank counts, counts, fix or choice, with what's wrong with each wrong display or list, then
    the word problems' answers with their work. ``path`` is a filename or a binary file-like
    object.

    With ``slot_of``, the sheet is for the self-check tiles case: the word problems take the
    tiles in turn, from problem 1's, and the answer bank and pattern follow on a page of their
    own. ``slot_of[i]`` is the slot of tile i + 1's answer, and the answers must be distinct.
    """
    pdf = new_pdf(path, header.title)
    sheet_instruction = instruction(problems)
    note = tiles_note(problems) if slot_of is not None else None
    if note is not None:
        sheet_instruction += f"\n{note}"
    y = draw_instruction(pdf, sheet_instruction, start_page(pdf, header))
    tiles: Iterator[int | None] = iter(range(1, len(slot_of) + 1)) if slot_of else repeat(None)
    tile_numbers = [[next(tiles) for _ in problem.word_problems] for problem in problems]
    for number, (problem, list_style, numbers) in enumerate(
        zip(problems, list_styles, tile_numbers, strict=True), start=1
    ):
        text = _wrap_text(problem)
        y = make_room(pdf, header, y, _height(problem, text))
        y = _draw_problem(pdf, number, problem, text, list_style, numbers, y)

    if slot_of is not None:
        answers = [
            str(question.data.answer) for problem in problems for question in problem.word_problems
        ]
        draw_tiles_page(pdf, header, answers, slot_of)
    if answer_key:
        solutions = [
            _solution(problem, numbers, slot_of)
            for problem, numbers in zip(problems, tile_numbers, strict=True)
        ]
        draw_answer_key(pdf, header, solutions)
    pdf.save()


def _wrap_text(problem: DiscreteDataProblem) -> _Text:
    """Wrap the problem's text to the widths its parts have."""
    lettered = (problem.summarize is not None) + len(problem.word_problems) > 1
    indent = PART_INDENT if lettered else 0
    task, task_choices, sentence = None, [], None
    if (summarize := problem.summarize) is not None:
        task = wrap(summarize_stem(summarize), PART_SIZE, TEXT_WIDTH - indent)
        data, response = summarize.data, summarize.response
        if isinstance(response, MultipleChoice) and isinstance(
            data, ReadCountsQuestionData | FindErrorQuestionData
        ):
            task_choices = [
                wrap(
                    f"{choice_label(index)} {_choice_text(data, option)}",
                    PART_SIZE,
                    TEXT_WIDTH - indent,
                )
                for index, option in enumerate(response.options)
            ]
        elif isinstance(data, FindErrorQuestionData):
            sentence = error_sentence(data)
    return _Text(
        intro=wrap(intro(problem.dataset, problem.given), INTRO_SIZE, TEXT_WIDTH),
        task=task,
        task_choices=task_choices,
        sentence=sentence,
        word_problems=[
            wrap(stem(question.data), PART_SIZE, TEXT_WIDTH - indent - ANSWER_WIDTH)
            for question in problem.word_problems
        ],
        lettered=lettered,
    )


def _choice_text(data: ReadCountsQuestionData | FindErrorQuestionData, option: object) -> str:
    """Return a written choice's text: a list of counts, or a statement of an error."""
    if isinstance(data, ReadCountsQuestionData) and isinstance(option, DisplayChoice):
        return counts_text(data.dataset, option.counts)
    if isinstance(data, FindErrorQuestionData) and isinstance(option, ErrorChoice):
        return error_fix(data, option)
    raise ValueError("A written choice is a list of counts or a statement of an error.")


def _height(problem: DiscreteDataProblem, text: _Text) -> float:
    """Return the room the problem takes, from its first baseline to the next problem's."""
    height: float = len(text.intro) * INTRO_LINE_HEIGHT
    if text.task is not None:
        height += len(text.task) * PART_LINE_HEIGHT
    height += _displays_height(problem) - PANEL_RAISE + PANEL_DROP
    height += _answers_height(problem, text)
    for question, lines in zip(problem.word_problems, text.word_problems, strict=True):
        height += _word_problem_height(lines, isinstance(question.response, MultipleChoice))
    return height


def _displays_height(problem: DiscreteDataProblem) -> float:
    """Return the height of the problem's displays, from their top to their bottom."""
    summarize = problem.summarize
    if summarize is None:
        return PANEL_HEIGHT
    data, response = summarize.data, summarize.response
    match data:
        case SummarizeDataQuestionData():
            if isinstance(response, MultipleChoice):
                return PANEL_HEIGHT + CHOICES_DROP + _choices_height(len(response.options))
            return PANEL_HEIGHT
        case ReadCountsQuestionData():
            return PANEL_HEIGHT
        case FindErrorQuestionData():
            rows = 2 if len(_error_panels(data)) > 2 else 1
            return rows * PANEL_HEIGHT + (rows - 1) * ROW_GAP
        case DoesntMatchQuestionData():
            source = PANEL_HEIGHT + CHOICES_DROP if data.source is not None else 0
            options = response.options if isinstance(response, MultipleChoice) else ()
            return source + _choices_height(len(options))
        case _:
            assert_never(data)


def _choices_height(count: int) -> float:
    rows = -(-count // CHOICE_COLUMNS)
    return (rows - 1) * CHOICE_ROW_HEIGHT + CHOICE_HEIGHT


def _answers_height(problem: DiscreteDataProblem, text: _Text) -> float:
    """Return the room the first part's answers take below its displays."""
    summarize = problem.summarize
    if text.task_choices:
        lines = sum(len(lines) for lines in text.task_choices)
        return lines * PART_LINE_HEIGHT + len(text.task_choices) * TEXT_CHOICE_GAP + PART_GAP
    if text.sentence is not None:
        return PART_LINE_HEIGHT + PART_GAP
    if summarize is not None and isinstance(summarize.data, ReadCountsQuestionData):
        dataset = summarize.data.dataset
        if isinstance(dataset, NumericalData):
            rows = -(-len(dataset.values) // _numbers_per_row())
            return rows * NUMBER_CELL_HEIGHT + PART_GAP
        rows = -(-len(dataset.counts) // COUNT_COLUMNS)
        return rows * COUNT_ROW_HEIGHT
    return 0


def _numbers_per_row() -> int:
    return int(TEXT_WIDTH // NUMBER_CELL_WIDTH)


def _part_height(lines: Sequence[str]) -> float:
    """Return the room a part takes: at least two lines, so its answer box fits beside them."""
    return max(2, len(lines)) * PART_LINE_HEIGHT + PART_GAP


def _word_problem_height(lines: Sequence[str], choices: bool) -> float:
    """Return the room a word problem takes: its lines and choices, or its lines with room for
    its answer box."""
    if choices:
        return (len(lines) + 1) * PART_LINE_HEIGHT + NUMBER_CHOICE_DROP + PART_GAP
    return _part_height(lines)


def _letters(text: _Text) -> Iterator[str | None]:
    """Return the problem's part letters, in order: a, b, c, or none for a lone part."""
    return iter("abc") if text.lettered else repeat(None)


def _draw_problem(
    pdf: Canvas,
    number: int,
    problem: DiscreteDataProblem,
    text: _Text,
    list_style: NumberListStyle,
    tile_numbers: Sequence[int | None],
    y: float,
) -> float:
    """Draw one problem from its number down, and return the next problem's baseline."""
    x = MARGIN + TEXT_INDENT
    pdf.setFillColor("black")
    pdf.setFont(FONT, TEXT_SIZE)
    pdf.drawString(MARGIN, y, f"{number}.")
    pdf.setFont(FONT, INTRO_SIZE)
    for line in text.intro:
        pdf.drawString(x, y, line)
        y -= INTRO_LINE_HEIGHT

    letters = _letters(text)
    summarize = problem.summarize
    if summarize is None or text.task is None:
        top = y + PANEL_RAISE
        _draw_alone(pdf, problem.given, problem.dataset, top, list_style)
        y = top - PANEL_HEIGHT - PANEL_DROP
    else:
        y = _draw_part_text(pdf, next(letters), text.task, y)
        top = y + PANEL_RAISE
        bottom = _draw_displays(pdf, problem, list_style, top)
        y = _draw_answers(
            pdf, problem, text, bottom - PANEL_DROP, x + (PART_INDENT if text.lettered else 0)
        )

    for question, lines, tile in zip(
        problem.word_problems, text.word_problems, tile_numbers, strict=True
    ):
        below = _draw_part_text(pdf, next(letters), lines, y)
        response = question.response
        if isinstance(response, MultipleChoice):
            _draw_number_choices(pdf, response.options, below - NUMBER_CHOICE_DROP, text.lettered)
        elif tile is not None:
            _draw_tile_number(pdf, y, tile)
        else:
            _draw_answer_box(pdf, y)
        y -= _word_problem_height(lines, isinstance(response, MultipleChoice))
    return y - PROBLEM_GAP


def _draw_displays(
    pdf: Canvas, problem: DiscreteDataProblem, list_style: NumberListStyle, top: float
) -> float:
    """Draw the first part's displays from ``top`` down, and return their bottom."""
    summarize = problem.summarize
    if summarize is None:
        raise ValueError("Only a first part has displays of its own.")
    data, response = summarize.data, summarize.response
    match data:
        case SummarizeDataQuestionData():
            if isinstance(response, MultipleChoice):
                _draw_alone(pdf, data.given, data.dataset, top, list_style)
                choices_top = top - PANEL_HEIGHT - CHOICES_DROP
                options = [
                    (data.target, chosen_data(data.dataset, option))
                    for option in response.options
                    if isinstance(option, DisplayChoice)
                ]
                return _draw_choices(pdf, options, list_style, choices_top)
            _draw_completion(pdf, data, top, list_style)
            return top - PANEL_HEIGHT
        case ReadCountsQuestionData():
            _draw_alone(pdf, data.given, data.dataset, top, list_style)
            return top - PANEL_HEIGHT
        case FindErrorQuestionData():
            return _draw_error_panels(pdf, data, top, list_style)
        case DoesntMatchQuestionData():
            if data.source is not None:
                _draw_alone(pdf, data.source, data.dataset, top, list_style)
                top -= PANEL_HEIGHT + CHOICES_DROP
            options = [
                (option.display, chosen_data(data.dataset, option.choice))
                for option in (response.options if isinstance(response, MultipleChoice) else ())
                if isinstance(option, ShownDisplay)
            ]
            return _draw_choices(pdf, options, list_style, top)
        case _:
            assert_never(data)


def _draw_answers(
    pdf: Canvas, problem: DiscreteDataProblem, text: _Text, y: float, x: float
) -> float:
    """Draw the first part's written choices, sentence or boxes from baseline ``y``, and return
    the next part's baseline."""
    summarize = problem.summarize
    if text.task_choices or text.sentence is not None:
        pdf.setFillColor("black")
        pdf.setFont(FONT, PART_SIZE)
    if text.task_choices:
        for lines in text.task_choices:
            for line in lines:
                pdf.drawString(x, y, line)
                y -= PART_LINE_HEIGHT
            y -= TEXT_CHOICE_GAP
        return y - PART_GAP
    if text.sentence is not None:
        pdf.drawString(x, y, text.sentence)
        return y - PART_LINE_HEIGHT - PART_GAP
    if summarize is not None and isinstance(summarize.data, ReadCountsQuestionData):
        dataset = summarize.data.dataset
        if isinstance(dataset, NumericalData):
            return _draw_number_cells(pdf, len(dataset.values), y) - PART_GAP
        return _draw_count_boxes(pdf, labels(dataset), x, y)
    return y


def _draw_count_boxes(pdf: Canvas, names: Sequence[str], x: float, y: float) -> float:
    """Draw each name with a box for its count, ``COUNT_COLUMNS`` to a row, and return the
    baseline below them."""
    column_width = (MARGIN + TEXT_INDENT + TEXT_WIDTH - x) / COUNT_COLUMNS
    pdf.setStrokeColor(BOX_COLOUR)
    pdf.setLineWidth(1)
    for index, name in enumerate(names):
        row, column = divmod(index, COUNT_COLUMNS)
        left = x + column * column_width
        baseline = y - row * COUNT_ROW_HEIGHT
        label = f"{name}:"
        pdf.setFillColor("black")
        pdf.setFont(FONT, PART_SIZE)
        pdf.drawString(left, baseline, label)
        box_x = left + stringWidth(label, FONT, PART_SIZE) + 6
        pdf.roundRect(box_x, baseline - BOX_DROP, COUNT_BOX_WIDTH, BOX_HEIGHT, BOX_CORNER_RADIUS)
    rows = -(-len(names) // COUNT_COLUMNS)
    return y - rows * COUNT_ROW_HEIGHT


def _draw_number_cells(pdf: Canvas, count: int, y: float) -> float:
    """Draw ``count`` empty boxes for a list's numbers, from baseline ``y``, and return the
    bottom of the last row."""
    per_row = _numbers_per_row()
    pdf.setStrokeColor(BOX_COLOUR)
    pdf.setLineWidth(0.8)
    top = y + NUMBER_CELL_HEIGHT - BOX_DROP
    for index in range(count):
        row, column = divmod(index, per_row)
        pdf.rect(
            MARGIN + TEXT_INDENT + column * NUMBER_CELL_WIDTH,
            top - (row + 1) * NUMBER_CELL_HEIGHT,
            NUMBER_CELL_WIDTH,
            NUMBER_CELL_HEIGHT,
        )
    rows = -(-count // per_row)
    return y - rows * NUMBER_CELL_HEIGHT


def _panel_width(display: DataDisplay) -> float:
    """Return the width of a display shown on its own."""
    return LIST_PANEL_WIDTH if display is DataDisplay.LIST else GIVEN_WIDTH


def _draw_alone(
    pdf: Canvas,
    display: DataDisplay | None,
    dataset: CategoricalData | NumericalData,
    top: float,
    list_style: NumberListStyle,
) -> None:
    """Draw ``display`` on its own, centred, with its top at ``top``; nothing for ``None``."""
    if display is None:
        return
    width = _panel_width(display)
    x = MARGIN + TEXT_INDENT + (TEXT_WIDTH - width) / 2
    draw_display(pdf, display, dataset, x, top, width, PANEL_HEIGHT, (), list_style)


def _draw_completion(
    pdf: Canvas, data: SummarizeDataQuestionData, top: float, list_style: NumberListStyle
) -> None:
    """Draw the given display beside the display to complete, with their tops at ``top``."""
    x = MARGIN + TEXT_INDENT
    given_width = (
        LIST_PANEL_WIDTH if data.given is DataDisplay.LIST else (TEXT_WIDTH - PANEL_GAP) / 2
    )
    target_width = TEXT_WIDTH - PANEL_GAP - given_width
    draw_display(pdf, data.given, data.dataset, x, top, given_width, PANEL_HEIGHT, (), list_style)
    draw_display(
        pdf,
        data.target,
        data.dataset,
        x + given_width + PANEL_GAP,
        top,
        target_width,
        PANEL_HEIGHT,
        data.blanks,
        list_style,
    )


def _error_panels(data: FindErrorQuestionData) -> list[DataDisplay]:
    """Return the displays a question to find an error shows: the source, if any, then the
    displays to check."""
    source = [data.source] if data.source is not None else []
    return source + list(error_displays(data))


def _draw_error_panels(
    pdf: Canvas, data: FindErrorQuestionData, top: float, list_style: NumberListStyle
) -> float:
    """
    Draw the data's source, if any, and the displays to check, side by side, or with three, the
    source centred above the other two. The wrong display shows its error. Return their bottom.
    """
    wrong = chosen_data(
        data.dataset,
        DisplayChoice(
            tuple(
                data.shown if index == data.index else count
                for index, count in enumerate(data.dataset.counts)
            ),
            data.dataset.scale if isinstance(data.dataset, CategoricalData) else 1,
            (),
        ),
    )
    panels = _error_panels(data)
    if len(panels) > 2:
        _draw_alone(pdf, panels[0], data.dataset, top, list_style)
        top -= PANEL_HEIGHT + ROW_GAP
        panels = panels[1:]
        source_drawn = True
    else:
        source_drawn = False
    widths = [
        LIST_PANEL_WIDTH if display is DataDisplay.LIST else (TEXT_WIDTH - PANEL_GAP) / 2
        for display in panels
    ]
    if len(panels) == 2:
        widths[-1] = TEXT_WIDTH - PANEL_GAP - widths[0]
    x = MARGIN + TEXT_INDENT + (TEXT_WIDTH - sum(widths) - PANEL_GAP * (len(panels) - 1)) / 2
    for position, (display, width) in enumerate(zip(panels, widths, strict=True)):
        is_source = position == 0 and data.source is not None and not source_drawn
        dataset = wrong if display is data.wrong and not is_source else data.dataset
        draw_display(pdf, display, dataset, x, top, width, PANEL_HEIGHT, (), list_style)
        x += width + PANEL_GAP
    return top - PANEL_HEIGHT


def _draw_choices(
    pdf: Canvas,
    options: Sequence[tuple[DataDisplay, CategoricalData | NumericalData]],
    list_style: NumberListStyle,
    top: float,
) -> float:
    """
    Draw the displays to choose from, ``CHOICE_COLUMNS`` to a row, each with its letter, from
    ``top`` down, and return the bottom of the last row.
    """
    column_width = (TEXT_WIDTH - CHOICE_GAP * (CHOICE_COLUMNS - 1)) / CHOICE_COLUMNS
    for index, (display, dataset) in enumerate(options):
        row, column = divmod(index, CHOICE_COLUMNS)
        x = MARGIN + TEXT_INDENT + column * (column_width + CHOICE_GAP)
        row_top = top - row * CHOICE_ROW_HEIGHT
        pdf.setFillColor("black")
        pdf.setFont(BOLD_FONT, PART_SIZE)
        pdf.drawString(x, row_top - CHOICE_LETTER_DROP, choice_label(index))
        draw_display(
            pdf,
            display,
            dataset,
            x + CHOICE_LETTER_WIDTH,
            row_top,
            column_width - CHOICE_LETTER_WIDTH,
            CHOICE_HEIGHT,
            (),
            list_style,
        )
    return top - _choices_height(len(options))


def _draw_number_choices(pdf: Canvas, options: Sequence[object], y: float, lettered: bool) -> None:
    """Draw a problem's number choices across one line, from baseline ``y``."""
    x = MARGIN + TEXT_INDENT + (PART_INDENT if lettered else 0)
    pdf.setFillColor("black")
    pdf.setFont(FONT, PART_SIZE)
    for index, option in enumerate(options):
        pdf.drawString(x + index * NUMBER_CHOICE_WIDTH, y, f"{choice_label(index)} {option}")


def _draw_part_text(pdf: Canvas, letter: str | None, lines: Sequence[str], y: float) -> float:
    """
    Draw a part's letter, if any, and text from baseline ``y``, and return the baseline below
    them.
    """
    x = MARGIN + TEXT_INDENT
    pdf.setFillColor("black")
    if letter is not None:
        pdf.setFont(BOLD_FONT, PART_SIZE)
        pdf.drawString(x, y, f"{letter}.")
        x += PART_INDENT
    pdf.setFont(FONT, PART_SIZE)
    for line in lines:
        pdf.drawString(x, y, line)
        y -= PART_LINE_HEIGHT
    return y


def _draw_answer_box(pdf: Canvas, y: float) -> None:
    """Draw "Answer:" and its box at the right margin, beside a part's first baseline ``y``."""
    box_x = PAGE_WIDTH - MARGIN - BOX_WIDTH
    pdf.saveState()
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, PART_SIZE)
    pdf.drawRightString(box_x - ANSWER_LABEL_GAP, y, ANSWER_LABEL)
    pdf.setStrokeColor(BOX_COLOUR)
    pdf.setLineWidth(1)
    pdf.roundRect(box_x, y - BOX_DROP, BOX_WIDTH, BOX_HEIGHT, BOX_CORNER_RADIUS, fill=0)
    pdf.restoreState()


def _draw_tile_number(pdf: Canvas, y: float, tile: int) -> None:
    """Draw "Tile 3" at the right margin, beside a part's first baseline ``y``."""
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, PART_SIZE)
    pdf.drawRightString(PAGE_WIDTH - MARGIN, y, f"Tile {tile}")


def _solution(
    problem: DiscreteDataProblem,
    tile_numbers: Sequence[int | None],
    slot_of: Sequence[int] | None,
) -> str:
    """
    Return the problem's answer key entry: a line for each part, and for a display or list to
    choose, a line for each wrong one, "Not B: Soccer and Tennis are switched". A word problem's
    line ends with its answer's slot letter for the tiles case.
    """
    letters = _letters(_wrap_text(problem))
    rows = []
    if (summarize := problem.summarize) is not None:
        rows += _summarize_rows(next(letters), summarize.data, summarize.response)
    for question, tile in zip(problem.word_problems, tile_numbers, strict=True):
        solution = f"{question.data.answer}   ({work(question.data)})"
        if isinstance(question.response, MultipleChoice):
            solution = f"{correct_letters(question.response)}  {solution}"
        if tile is not None and slot_of is not None:
            solution += f"    ({ascii_uppercase[slot_of[tile - 1]]})"
        rows.append(_row(next(letters), solution))
    return "\n".join(rows)


def _summarize_rows(letter: str | None, data: object, response: object) -> list[str]:
    """Return the answer key lines for a problem's first part."""
    choose = isinstance(response, MultipleChoice)
    match data:
        case SummarizeDataQuestionData() if isinstance(response, MultipleChoice):
            return [
                _row(letter, f"{correct_letters(response)}   ({blank_counts(data)})"),
                *_not_rows(data, response),
            ]
        case SummarizeDataQuestionData():
            target = DISPLAY_NAMES[data.target].capitalize()
            return [_row(letter, f"{target} \N{EM DASH} {blank_counts(data)}")]
        case ReadCountsQuestionData() if isinstance(response, MultipleChoice):
            counts = counts_text(data.dataset, _counts(data))
            return [
                _row(letter, f"{correct_letters(response)}   ({counts})"),
                *_not_rows(data, response),
            ]
        case ReadCountsQuestionData():
            return [_row(letter, counts_text(data.dataset, _counts(data)))]
        case FindErrorQuestionData():
            fix = error_fix(data, ErrorChoice(data.wrong, data.index, data.answer))
            if choose and isinstance(response, MultipleChoice):
                return [_row(letter, f"{correct_letters(response)}   ({fix})")]
            return [_row(letter, fix)]
        case DoesntMatchQuestionData() if isinstance(response, MultipleChoice):
            name = DISPLAY_NAMES[data.answer.display].capitalize()
            return [
                _row(
                    letter, f"{correct_letters(response)}   ({name}: {mistake(data, data.answer)})"
                )
            ]
    raise ValueError("A first part is one of the summarizing questions.")


def _counts(data: ReadCountsQuestionData) -> tuple[int, ...]:
    """Return the counts a list of the data set's counts shows, by category or tick."""
    return data.dataset.counts


def _not_rows(
    data: SummarizeDataQuestionData | ReadCountsQuestionData, response: MultipleChoice[object]
) -> list[str]:
    """Return a line for each wrong choice: "Not B: Soccer and Tennis are switched"."""
    return [
        f"Not {ascii_uppercase[index]}: {mistake(data, option)}"
        for index, option in enumerate(response.options)
        if index not in response.correct_indexes and isinstance(option, DisplayChoice)
    ]


def _row(letter: str | None, text: str) -> str:
    """Return an answer key line, led by its part's letter if it has one."""
    return text if letter is None else f"{letter}.  {text}"
