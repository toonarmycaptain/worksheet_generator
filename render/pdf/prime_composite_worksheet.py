"""
PDF worksheets of prime and composite questions, with an optional answer key page.

Each problem is its number and question, then what the student answers on:
- lettered choices, in a row when every one fits its share of the width, else one under
  another;
- a row of numbers, to circle two of, or to mark prime, composite or neither: in a box under
  each number, which a tiles sheet keeps for working out a row's letters, or by circling one of
  the three words under it;
- answer lines: one, two for a number's factors and what it is, or three to explain who is
  correct.

A sheet for the self-check tiles case has no choices or answer lines, and ends with a page for
the answer bank and pattern. A problem that would run past the bottom margin starts on the next
page.
"""

from collections.abc import Sequence
from typing import Any, BinaryIO

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.prime_composite.data import (
    CountQuestionData,
    EachNumberQuestionData,
    FactorPairCountQuestionData,
    FactorPairQuestionData,
    ListFactorsQuestionData,
    PrimeCompositeQuestion,
    PrimeCountQuestionData,
    WhoIsCorrectQuestionData,
)
from core.prime_composite.representation import (
    TileQuestionData,
    factor_list_text,
    numbers_shown,
    pair_text,
    prime_composite_tile_question,
    question,
    solution,
    verdict_text,
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
    make_room,
    new_pdf,
    start_page,
    wrap,
)
from render.pdf.tiles import draw_tiles_page, tile_solutions

QUESTION_SIZE = 12  # every problem's text, its choices and its numbers
QUESTION_LINE_HEIGHT = 15
NUMBER_WIDTH = 24  # from a problem's number to its text
TEXT_WIDTH = CONTENT_WIDTH - NUMBER_WIDTH
BELOW_GAP = 10  # from the question's last line down to the top of what is under it
PROBLEM_GAP = 26  # from the bottom of a problem down to the next problem's baseline

LETTER_WIDTH = 24  # room for "A)" left of each choice
CHOICE_MARGIN = 16  # the least gap between a choice in a row and the next choice's letter
CHOICE_GAP = 6  # between two choices one under another

ROW_NUMBER_SIZE = 14  # the numbers in a row to circle or mark
ROW_NUMBER_HEIGHT = 18  # from the top of a row of numbers down to below their baseline
BOX_SIDE = 26  # the box under each number to write P, C or N in
BOX_GAP = 6  # from a number down to its box or words
WORD_SIZE = 10  # the words under each number to circle one of
WORD_LINE_HEIGHT = 13

ANSWER_LINE_DROP = 24  # from the top of an answer line's space down to the line
ANSWER_LINE_GAP = 26  # between two answer lines
LABEL_GAP = 6  # between an answer line's label and the line
EXPLAIN_LINES = 3  # to say who is correct and why
FACTOR_LABELS = ("Factors:", "Prime or composite:")


def render_prime_composite_worksheet(
    questions: Sequence[PrimeCompositeQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    slot_of: Sequence[int] | None,
) -> None:
    """
    Render prime and composite problems, and the answer key if requested, to ``path``.

    The answer key gives each problem's answer, after the correct letters for lettered choices,
    with the facts or numbers that show it where they help. ``path`` is a filename or a binary
    file-like object.

    With ``slot_of``, the sheet is for the self-check tiles case: the questions must all be
    written counting forms (see ``core.prime_composite.generator``), with different answers,
    and the answer bank and pattern follow on a page of their own. ``slot_of[i]`` is the slot of
    question i + 1's answer, as in ``core.self_check_tiles``, so there are at most 12 questions.
    The answer key adds each answer's slot letter.
    """
    pdf = new_pdf(path, header.title)
    y = start_page(pdf, header)
    for number, each in enumerate(questions, start=1):
        y = _draw_problem(pdf, header, number, each, slot_of is not None, y)

    if slot_of is None:
        solutions = [_solution(each) for each in questions]
    else:
        tile_questions = [prime_composite_tile_question(_tile_data(each)) for each in questions]
        draw_tiles_page(pdf, header, [each.answer for each in tile_questions], slot_of)
        solutions = tile_solutions(tile_questions, slot_of)
    if answer_key:
        draw_answer_key(pdf, header, solutions)

    pdf.save()


def _tile_data(each: PrimeCompositeQuestion) -> TileQuestionData:
    """
    Return a tiles sheet's question's data. Raises ``ValueError`` for a question with no tile
    form.
    """
    data = each.data
    counting = (
        FactorPairCountQuestionData,
        CountQuestionData,
        PrimeCountQuestionData,
        EachNumberQuestionData,
    )
    if isinstance(data, counting) and isinstance(each.response, FreeResponse):
        return data
    raise ValueError("A self-check tiles sheet asks only written counting questions.")


def _solution(each: PrimeCompositeQuestion) -> str:
    """Return the answer key's entry, after the correct letters for lettered choices."""
    entry = solution(each.data)
    if isinstance(each.response, MultipleChoice):
        return f"{correct_letters(each.response)}) {entry}"
    return entry


def _draw_problem(
    pdf: Canvas,
    header: Header,
    number: int,
    each: PrimeCompositeQuestion,
    tiles: bool,
    y: float,
) -> float:
    """
    Draw a problem from baseline ``y``, moving to a new page first if it won't fit, and return
    the next problem's baseline. On a tiles sheet, ``tiles``, it has no choices or answer lines.
    """
    data = each.data
    response = each.response
    choices = not isinstance(response, FreeResponse)
    lines = wrap(question(data, choices), QUESTION_SIZE, TEXT_WIDTH)
    texts = _choice_texts(each)
    row = numbers_shown(data) if not isinstance(response, MultipleChoice) else ()
    below = _below_height(each, texts, row, tiles)
    y = make_room(pdf, header, y, (len(lines) - 1) * QUESTION_LINE_HEIGHT + BELOW_GAP + below)
    pdf.setFillColor("black")
    pdf.setFont(FONT, QUESTION_SIZE)
    pdf.drawString(MARGIN, y, f"{number}.")
    for line in lines:
        pdf.drawString(MARGIN + NUMBER_WIDTH, y, line)
        y -= QUESTION_LINE_HEIGHT
    # below the last line's baseline, leaving room for its descenders
    top = y + QUESTION_LINE_HEIGHT - BELOW_GAP
    left = MARGIN + NUMBER_WIDTH
    if texts:
        _draw_choices(pdf, texts, left, top)
    elif row:
        words = isinstance(response, tuple)
        boxes = isinstance(data, EachNumberQuestionData) and not words
        _draw_row(pdf, row, left, top, boxes, words)
    elif not tiles:
        _draw_answer_lines(pdf, _labels(each), left, top)
    return top - below - PROBLEM_GAP


def _choice_texts(each: PrimeCompositeQuestion) -> list[str]:
    """Return the problem's lettered choices as written, or none if it has none."""
    response = each.response
    if not isinstance(response, MultipleChoice):
        return []
    data = each.data
    return [_option_text(data, option) for option in response.options]


def _option_text(data: Any, option: Any) -> str:
    """Return a choice as written: a factor pair in the question's look, a verdict, a list."""
    if isinstance(data, FactorPairQuestionData):
        return pair_text(data, option)
    if isinstance(data, WhoIsCorrectQuestionData):
        return verdict_text(data, option)
    if isinstance(data, ListFactorsQuestionData):
        return factor_list_text(option)
    return str(option)


def _labels(each: PrimeCompositeQuestion) -> tuple[str, ...]:
    """
    Return the labels of the problem's answer lines: two for a number's factors and what it is,
    three unlabelled lines to explain who is correct, else one unlabelled line.
    """
    if isinstance(each.data, ListFactorsQuestionData):
        return FACTOR_LABELS
    if isinstance(each.data, WhoIsCorrectQuestionData):
        return ("",) * EXPLAIN_LINES
    return ("",)


def _in_a_row(texts: Sequence[str]) -> bool:
    """Return whether every choice fits its share of the width, beside its letter."""
    share = TEXT_WIDTH / len(texts)
    room = share - LETTER_WIDTH - CHOICE_MARGIN
    return all(stringWidth(text, FONT, QUESTION_SIZE) <= room for text in texts)


def _choice_lines(texts: Sequence[str]) -> list[list[str]]:
    """Return each choice's lines, wrapped beside its letter, for choices one under another."""
    return [wrap(text, QUESTION_SIZE, TEXT_WIDTH - LETTER_WIDTH) for text in texts]


def _below_height(
    each: PrimeCompositeQuestion, texts: Sequence[str], row: Sequence[int], tiles: bool
) -> float:
    """
    Return the height of what is under the question: its choices, its row of numbers or its
    answer lines, from the top of the space below its last line.
    """
    if texts:
        if _in_a_row(texts):
            return QUESTION_LINE_HEIGHT
        lines = _choice_lines(texts)
        count = sum(len(each_lines) for each_lines in lines)
        return count * QUESTION_LINE_HEIGHT + (len(lines) - 1) * CHOICE_GAP
    if row:
        if isinstance(each.response, tuple):
            return ROW_NUMBER_HEIGHT + BOX_GAP + 3 * WORD_LINE_HEIGHT
        if isinstance(each.data, EachNumberQuestionData):
            return ROW_NUMBER_HEIGHT + BOX_GAP + BOX_SIDE
        return ROW_NUMBER_HEIGHT
    if tiles:
        return 0
    return ANSWER_LINE_DROP + (len(_labels(each)) - 1) * ANSWER_LINE_GAP


def _draw_choices(pdf: Canvas, texts: Sequence[str], left: float, top: float) -> None:
    """
    Draw lettered choices from ``top`` down: in a row, each in an equal share of the width,
    when every one fits, else one under another, each wrapped beside its letter.
    """
    baseline = top - QUESTION_SIZE
    if _in_a_row(texts):
        share = TEXT_WIDTH / len(texts)
        for index, text in enumerate(texts):
            x = left + index * share
            pdf.setFont(BOLD_FONT, QUESTION_SIZE)
            pdf.drawString(x, baseline, choice_label(index))
            pdf.setFont(FONT, QUESTION_SIZE)
            pdf.drawString(x + LETTER_WIDTH, baseline, text)
        return
    for index, lines in enumerate(_choice_lines(texts)):
        pdf.setFont(BOLD_FONT, QUESTION_SIZE)
        pdf.drawString(left, baseline, choice_label(index))
        pdf.setFont(FONT, QUESTION_SIZE)
        for line in lines:
            pdf.drawString(left + LETTER_WIDTH, baseline, line)
            baseline -= QUESTION_LINE_HEIGHT
        baseline -= CHOICE_GAP


def _draw_row(
    pdf: Canvas,
    numbers: Sequence[int],
    left: float,
    top: float,
    boxes: bool,
    words: bool,
) -> None:
    """
    Draw a row of numbers from ``top`` down, each centred in an equal share of the width, with
    a box under each with ``boxes``, or with ``words``, the three words to circle one of.
    """
    share = TEXT_WIDTH / len(numbers)
    baseline = top - ROW_NUMBER_SIZE
    for index, number in enumerate(numbers):
        centre = left + (index + 0.5) * share
        pdf.setFont(BOLD_FONT, ROW_NUMBER_SIZE)
        pdf.drawCentredString(centre, baseline, str(number))
        under = top - ROW_NUMBER_HEIGHT - BOX_GAP
        if boxes:
            pdf.rect(centre - BOX_SIDE / 2, under - BOX_SIDE, BOX_SIDE, BOX_SIDE)
        if words:
            pdf.setFont(FONT, WORD_SIZE)
            for line, word in enumerate(("prime", "composite", "neither")):
                pdf.drawCentredString(centre, under - WORD_SIZE - line * WORD_LINE_HEIGHT, word)


def _draw_answer_lines(pdf: Canvas, labels: Sequence[str], left: float, top: float) -> None:
    """Draw an answer line for each label, from ``top`` down, each after its label, if any."""
    y = top - ANSWER_LINE_DROP
    pdf.setFont(FONT, QUESTION_SIZE)
    for label in labels:
        start = left
        if label:
            pdf.drawString(left, y + 2, label)
            start += stringWidth(label, FONT, QUESTION_SIZE) + LABEL_GAP
        pdf.line(start, y, left + TEXT_WIDTH, y)
        y -= ANSWER_LINE_GAP
