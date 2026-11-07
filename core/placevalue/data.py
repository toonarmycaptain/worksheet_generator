"""Data for place-value questions: a number shown in one form and asked for in another."""

from dataclasses import dataclass
from enum import StrEnum

from core.question import FreeResponse, MultipleChoice, Question, QuestionData


class PlaceValueForm(StrEnum):
    """
    A form of a number: written, or drawn as base-ten blocks. Values are stable identifiers for
    the API and storage.
    """

    STANDARD = "standard"  # 35,043
    EXPANDED = "expanded"  # 30,000 + 5,000 + 40 + 3
    UNIT = "unit"  # 3 ten thousands 5 thousands 4 tens 3 ones
    EXPANDED_NOTATION = "expanded_notation"  # (3 x 10,000) + (5 x 1,000) + (4 x 10) + (3 x 1)
    WORD = "word"  # thirty-five thousand, forty-three
    BLOCKS = "blocks"  # 352 as 3 flats, 5 rods and 2 units, drawn rather than written


@dataclass(frozen=True)
class PlaceValueQuestionData(QuestionData[int]):
    """
    A place-value question: write ``answer``, shown in the ``given`` form, in the ``asked`` form.

    The answer is the number itself. Every form represents the same value, so no other field is
    needed: given 35,043 and asked for expanded form, the answer is 35,043, written as
    30,000 + 5,000 + 40 + 3.

    ``given`` and ``asked`` must differ. This class does not enforce it; the generator never
    produces a question that asks for the form it shows.
    """

    answer: int
    given: PlaceValueForm
    asked: PlaceValueForm


# A place-value question as presented: written in, or chosen from numbers in the asked form
type PlaceValueQuestion = Question[PlaceValueQuestionData, FreeResponse | MultipleChoice[int]]
